#!/usr/bin/python3
"""Bounded disposable-guest soak; source state restored when the test finishes."""
import ast,json,os,subprocess as sp,time
from pathlib import Path
os.environ.update(DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus',XDG_RUNTIME_DIR='/run/user/1000',STEINS_DESKTOP_BACKEND='plasma')
path=Path('/tmp/v3-worldline-soak.json')
primary=int(sp.check_output(['pgrep','-x','startplasma-wayl'],text=True).strip()) if sp.run(['pgrep','-x','startplasma-wayl'],capture_output=True).returncode==0 else int(sp.check_output(['pgrep','-f','^/usr/bin/startplasma-wayland$'],text=True).strip())
primary_stat=Path('/proc',str(primary),'stat').read_text().split()[21]
worlds=['0.571024','1.048596','2.198306','3.072100','4.250801','5.093001']
def request(method,*args):return json.loads(ast.literal_eval(sp.check_output(['gdbus','call','--session','--dest','org.steinsos.Worldline1','--object-path','/org/steinsos/Worldline','--method','org.steinsos.Worldline1.'+method,*args],text=True))[0])
initial=request('GetState')['divergence'];records=[];start=time.monotonic()
def save(phase):
 tmp=path.with_suffix('.new');tmp.write_text(json.dumps({'phase':phase,'primary_pid':primary,'initial':initial,'elapsed_seconds':round(time.monotonic()-start,2),'checks':records},indent=2)+'\n');tmp.replace(path)
try:
 for index in range(36):
  value=worlds[index%len(worlds)];state=request('SetDivergence',value)
  alive=Path('/proc',str(primary),'stat').exists() and Path('/proc',str(primary),'stat').read_text().split()[21]==primary_stat
  records.append({'iteration':index+1,'divergence':state['divergence'],'applied':state.get('applied') is True,'primary_alive':alive,'errors':state.get('errors',[])})
  save('running')
  if not alive or not state.get('applied'):raise RuntimeError('Session or appearance failed')
  time.sleep(45)
finally:
 request('SetDivergence',initial)
 save('complete' if len(records)==36 and all(r['applied'] and r['primary_alive'] for r in records) else 'incomplete')
