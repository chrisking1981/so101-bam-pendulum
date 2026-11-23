# Step response timeline: when does the servo apply current (load/current) vs when does it move?
import time, json, numpy as np, rustypot
from bam.feetech.sts import sm
c = rustypot.Sts3215PyController('/dev/cu.usbmodem5B421351891', 1000000, 0.05)
ID = 2
# pure bus round trip
t=[];
for _ in range(500):
    a=time.perf_counter(); c.read_raw_data(ID,56,2); t.append(time.perf_counter()-a)
print('read round trip ms: median %.3f p99 %.3f max %.3f'%tuple(1000*np.percentile(t,[50,99,100])))
t=[]
p0 = c.read_raw_data(ID,56,2); p0=p0[0]|p0[1]<<8
c.write_p_coefficient(ID,32); c.write_d_coefficient(ID,0)
for _ in range(200):
    a=time.perf_counter(); c.write_raw_goal_position(ID,p0); t.append(time.perf_counter()-a)
print('write(ack) round trip ms: median %.3f p99 %.3f max %.3f'%tuple(1000*np.percentile(t,[50,99,100])))
c.write_raw_goal_position(ID,p0); c.write_torque_enable(ID,True); time.sleep(0.5)
rows=[]; misses=[]
for target in (p0+1024, p0):
    c.write_raw_goal_position(ID,target); ts=time.perf_counter()
    while time.perf_counter()-ts<0.6:
        try:
            r=c.read_raw_data(ID,56,15)
        except RuntimeError:
            misses.append(time.perf_counter()-ts); continue
        tt=time.perf_counter()-ts
        rows.append((target,tt,sm(r[0]|r[1]<<8,15)-p0,sm(r[2]|r[3]<<8,15),sm(r[4]|r[5]<<8,10),r[10],(r[13]|r[14]<<8)&0x7fff))
    time.sleep(0.4)
for _ in range(5):
    try: c.write_torque_enable(ID,False); c.write_d_coefficient(ID,32); break
    except RuntimeError: time.sleep(0.05)
print('missed reads at ms:',[round(1000*m,1) for m in misses])
for target in (p0+1024,):
    R=[x for x in rows if x[0]==target]
    def first(i,th): 
        for x in R:
            if abs(x[i])>=th: return '%5.1f ms'%(1000*x[1])
        return '  -  '
    print('step +90deg: load>0:',first(4,1),' current>0:',first(6,1),' moving flag:',first(5,1),' speed>0:',first(3,1),' pos>=1 tick:',first(2,1),' pos>=5deg:',first(2,57))
    for x in R[:: max(1,len(R)//40)][:30]: print('  %6.1f ms pos %5d speed %5d load %5d moving %d current %4d'%(1000*x[1],x[2],x[3],x[4],x[5],x[6]))
