import argparse
import json,time,math,bisect,zipfile,os
from pathlib import Path
import scservo_sdk as sdk
patterns = ['up_and_down', 'sin_sin', 'sin_time_square', 'lift_and_drop', 'brutal']
parser = argparse.ArgumentParser(description='Replay unloaded Rhoban BAM trajectories on C044 ID 3.')
parser.add_argument('output', type=Path)
parser.add_argument('port')
parser.add_argument('archive')
parser.add_argument('gains', type=int, choices=[4, 8, 16, 32], nargs='+')
parser.add_argument('--pattern', choices=patterns, action='append')
parser.add_argument('--operator-confirmed-clear', action='store_true',
                    help='Onsite operator has verified the fixed servo, bare horn and clear motion area.')
parser.add_argument('--brutal-amplitude', type=int, choices=[5, 15, 30, 60],
                    help='Diagnostic variant of the BAM step pattern, in degrees.')
args = parser.parse_args()
if args.brutal_amplitude is not None and args.pattern != ['brutal']:
 parser.error('--brutal-amplitude requires --pattern brutal')
r = args.output
r.mkdir(exist_ok=False)
p = sdk.PortHandler(args.port)
h = sdk.PacketHandler(0)
assert p.setBaudRate(1000000)
def ck(out):
 *v,c,e=out
 if c or e:raise RuntimeError(str((c,e)))
 return v[0] if v else None
def rd(reg,n=1):return ck(getattr(h,f'read{n}ByteTxRx')(p,3,reg))
def wr(reg,v,n=1):ck(getattr(h,f'write{n}ByteTxRx')(p,3,reg,v))
def obs():
 a=ck(h.readTxRx(p,3,56,15)); return dict(ticks=a[0]+256*a[1],volts=a[6]/10,temp_C=a[7],current_raw=(a[13]+256*a[14])&32767)
low_voltage_since = None
def guard(e):
 global low_voltage_since
 now = time.monotonic()
 if e['volts'] >= 5:
  low_voltage_since = None
 elif low_voltage_since is None:
  low_voltage_since = now
 low_voltage = e['volts'] < 4.9 or (low_voltage_since is not None and now - low_voltage_since >= .06)
 if not (lo+20 < e['ticks'] < hi-20 and not low_voltage and e['volts'] <= 8.4 and e['temp_C'] < 45 and e['current_raw'] < 150):
  raise RuntimeError('telemetry guard '+str(e))
 if not args.operator_confirmed_clear:
  if time.time()-os.stat('/tmp/so101-realsense-live/color.bmp').st_mtime >= 2:
   raise RuntimeError('D435 stream is stale')

refs={}
with zipfile.ZipFile(args.archive) as z:
 for member in z.namelist():
  if member.endswith('.json'):
   d=json.loads(z.read(member))
   if d['mass']==0:refs[d['kp'],d['trajectory']]=(member,d)
meta={'completed':[], 'stop':None,'inputs':'Rhoban Feetech raw archive, no tip load','servo':'C044 ID 3, horn only','voltage_bounds':[5,8.4], 'voltage_note':'One quantization step at 4.9 V tolerated for less than 60 ms. Lower readings are immediate stops.','current_trip_raw':150}
saved=None;active=False;settings_changed=False;name='preflight';samples=[]
def save():
 (r/(name+'.json')).write_text(json.dumps(samples))
def sample(start,t,q,on):
 t0=time.monotonic();e=obs();e.update(timestamp=(t0+time.monotonic())/2-start,command_timestamp=t,goal_ticks=q,enabled=on)
 samples.append(e);guard(e)
def goal(q):
 if not lo+45<=q<=hi-45:raise ValueError(q)
 wr(42,q,2)
def arm(q):
 global active
 goal(q);active=True;wr(40,1)
 if rd(40)!=1:raise RuntimeError("Torque enable failed readback")
def torque_off():
 for _ in range(3):
  try:
   wr(40,0)
   if rd(40)==0:
    return
  except RuntimeError:
   pass
  time.sleep(.05)
 raise RuntimeError("Torque off could not be confirmed. Disconnect servo power.")
def home():
 q=rd(56,2);arm(q);start=time.monotonic()
 for i in range(1,max(2,1+math.ceil(abs(center-q)/6))):
  cmd=q+int(math.copysign(min(6*i,abs(center-q)),center-q));t=time.monotonic()-start;goal(cmd);time.sleep(.025);sample(start,t,cmd,True)
 torque_off()
def setting(register, value):
 if rd(register)==value:
  return
 write_error=None
 try:
  wr(register,value)
 except RuntimeError as exc:
  write_error=str(exc)
 p.closePort()
 time.sleep(.15)
 if not p.setBaudRate(1000000):
  raise RuntimeError('Could not reopen servo port after settings write')
 actual=rd(register)
 meta.setdefault('setting_readbacks',[]).append(dict(register=register,requested=value,actual=actual,write_error=write_error))
 if actual!=value:
  raise RuntimeError(f'Register {register}: requested {value}, read {actual}')

try:
 assert ck(h.ping(p,3))==777 and rd(40)==0 and rd(33)==0
 lo,hi=rd(9,2),rd(11,2); assert (lo,hi)==(820,3031)
 assert rd(62)>=50
 center=(lo+hi)//2
 guard(obs());saved={k:rd(k) for k in [21,22,23,55]}
 meta.update(original=saved,zero_ticks=center,operator_confirmed_clear=args.operator_confirmed_clear)
 for kp in args.gains:
  name=f'p{kp}-preflight';samples=[]
  assert rd(40)==0 and rd(22)==32
  if rd(21)!=kp:
   settings_changed=True
   setting(55,0);setting(21,kp);setting(55,saved[55])
  assert rd(21)==kp
  for pattern in args.pattern or patterns:
   name=f'p{kp}-{pattern}-setup';samples=[];home();save()
   member,d=refs[kp,pattern];a=d['entries'];ts=[x['timestamp'] for x in a];scale=.9 if pattern=='sin_sin' else 1
   suffix = '-90pct' if pattern == 'sin_sin' else ''
   if args.brutal_amplitude is not None:
    scale = args.brutal_amplitude / 90
    suffix = f'-diagnostic-{args.brutal_amplitude}deg'
   name=f'p{kp}-{pattern}{suffix}';samples=[]
   meta[name]={'member':member,'scale':scale,'p':kp,'d':32}
   targets=[center+round(x['goal_position']*scale*4096/(2*math.pi)) for x in a if x['torque_enable']]
   assert min(targets)>=lo+45 and max(targets)<=hi-45
   guard(obs());arm(center);on=True;start=time.monotonic()
   meta[name]['start_monotonic_s'] = start
   while (t:=time.monotonic()-start)<ts[-1]:
    x=a[max(0,bisect.bisect_right(ts,t)-1)];q=center+round(x['goal_position']*scale*4096/(2*math.pi))
    if x['torque_enable']:goal(q)
    if on and not x['torque_enable']:
     torque_off();on=False
     meta[name]['torque_off_confirmed_s']=time.monotonic()-start
    elif not on and x['torque_enable']:
     raise RuntimeError("Unexpected torque re-enable in reference")
    sample(start,t,q,on);time.sleep(max(0,.02-(time.monotonic()-start-t)))
   torque_off();save();meta['completed'].append(name);print(name,len(samples),flush=True)
except Exception as e:meta['stop']=name+' '+repr(e)
finally:
 try:
  if active:torque_off()
  if settings_changed:
   if rd(21)!=saved[21]:
    setting(55,0);setting(21,saved[21])
   setting(55,saved[55])
  meta['final']={k:rd(k) for k in [21,22,23,40,55,56] if k!=56};meta['final_ticks']=rd(56,2)
  if saved and (meta['final'][40]!=0 or any(meta['final'][k]!=saved[k] for k in saved)):
   raise RuntimeError('Final motor state differs from expected state')
 finally:
  p.closePort();save();(r/'status.json').write_text(json.dumps(meta,indent=2));print(meta,flush=True)
