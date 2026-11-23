import json,time,math,bisect,zipfile,sys,os
from pathlib import Path
import scservo_sdk as sdk
r=Path(sys.argv[1]);p=sdk.PortHandler(sys.argv[2]);h=sdk.PacketHandler(0);assert p.setBaudRate(1000000)
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
 if not (lo+20 < e['ticks'] < hi-20 and not low_voltage and e['volts'] <= 8.4 and e['temp_C'] < 45 and e['current_raw'] < 150 and time.time()-os.stat('/tmp/so101-realsense-live/color.bmp').st_mtime < 2):
  raise RuntimeError('telemetry guard '+str(e))

refs={}
with zipfile.ZipFile(sys.argv[3]) as z:
 for member in z.namelist():
  if member.endswith('.json'):
   d=json.loads(z.read(member))
   if d['mass']==0:refs[d['kp'],d['trajectory']]=(member,d)
meta={'completed':[], 'stop':None,'inputs':'Rhoban Feetech raw archive, no tip load','servo':'C044 ID 3, horn only','voltage_bounds':[5,8.4], 'voltage_note':'One quantization step at 4.9 V tolerated for less than 60 ms. Lower readings are immediate stops.','current_trip_raw':150}
saved=None;active=False;name='preflight';samples=[]
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
def torque_off():
 for _ in range(3):
  try:
   wr(40,0)
   time.sleep(.15)
   if rd(40)==0:
    return
  except RuntimeError:
   time.sleep(.15)
 raise RuntimeError("Torque off could not be confirmed. Disconnect servo power.")
def home():
 q=rd(56,2);arm(q);start=time.monotonic()
 for i in range(1,max(2,1+math.ceil(abs(center-q)/6))):
  cmd=q+int(math.copysign(min(6*i,abs(center-q)),center-q));t=time.monotonic()-start;goal(cmd);time.sleep(.025);sample(start,t,cmd,True)
 torque_off()
def setting(k,v):
 if rd(k)!=v:
  try:wr(k,v)
  except RuntimeError:pass
  time.sleep(.15);assert rd(k)==v
try:
 assert ck(h.ping(p,3))==777 and rd(40)==0 and rd(33)==0
 lo,hi=rd(9,2),rd(11,2); assert (lo,hi)==(820,3031)
 assert rd(62)>=50
 center=(lo+hi)//2
 guard(obs());saved={k:rd(k) for k in [21,22,23,55]}
 meta.update(original=saved,zero_ticks=center)
 for kp in [int(k) for k in sys.argv[4:]]:
  assert rd(40)==0 and rd(22)==32
  if rd(21)!=kp:
   setting(55,0);setting(21,kp);setting(55,saved[55])
  assert rd(21)==kp
  for pattern in ['up_and_down','sin_sin','sin_time_square','lift_and_drop','brutal']:
   name=f'p{kp}-{pattern}-setup';samples=[];home();save()
   member,d=refs[kp,pattern];a=d['entries'];ts=[x['timestamp'] for x in a];scale=.9 if pattern=='sin_sin' else 1
   name=f'p{kp}-{pattern}'+('-90pct' if scale!=1 else '');samples=[]
   meta[name]={'member':member,'scale':scale,'p':kp,'d':32}
   targets=[center+round(x['goal_position']*scale*4096/(2*math.pi)) for x in a if x['torque_enable']]
   assert min(targets)>=lo+45 and max(targets)<=hi-45
   guard(obs());arm(center);on=True;start=time.monotonic()
   while (t:=time.monotonic()-start)<ts[-1]:
    x=a[max(0,bisect.bisect_right(ts,t)-1)];q=center+round(x['goal_position']*scale*4096/(2*math.pi))
    if x['torque_enable']:goal(q)
    if on and not x['torque_enable']:
     torque_off();on=False
    elif not on and x['torque_enable']:
     raise RuntimeError("Unexpected torque re-enable in reference")
    sample(start,t,q,on);time.sleep(max(0,.02-(time.monotonic()-start-t)))
   torque_off();save();meta['completed'].append(name);print(name,len(samples),flush=True)
except Exception as e:meta['stop']=name+' '+repr(e)
finally:
 try:
  if active:torque_off()
  if saved:
   if rd(21)!=saved[21]:
    setting(55,0);setting(21,saved[21])
   setting(55,saved[55])
  meta['final']={k:rd(k) for k in [21,22,23,40,55,56] if k!=56};meta['final_ticks']=rd(56,2)
 finally:
  p.closePort();save();(r/'status.json').write_text(json.dumps(meta,indent=2));print(meta,flush=True)
