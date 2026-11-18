#!/usr/bin/python3
"""Run inside the V3 disposable guest: shared CLI paths and preserved art."""
import ast,hashlib,json,os,subprocess as sp,sys
from pathlib import Path
sys.path.insert(0,'/usr/lib/steins')
import steinslib as sl
os.environ.update(DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus',XDG_RUNTIME_DIR='/run/user/1000',WAYLAND_DISPLAY='wayland-0',STEINS_DESKTOP_BACKEND='plasma',STEINS_FAST='1')
results=[]
def check(label,condition):
 results.append({'check':label,'passed':bool(condition)})
 if not condition:raise AssertionError(label)
def state():
 return json.loads(ast.literal_eval(sp.check_output(['gdbus','call','--session','--dest','org.steinsos.Worldline1','--object-path','/org/steinsos/Worldline','--method','org.steinsos.Worldline1.GetState'],text=True))[0])
initial=state()['divergence']
try:
 first=sp.run(['steins-worldline','set','2.198306'],text=True,capture_output=True,check=True)
 check('CLI reports service application','session service' in first.stdout)
 current=state();check('CLI and service agree',current['divergence']=='2.198306' and current['applied'])
 check('16 ANSI colours exposed',len(current['terminal_palette'])==16)
 second=sp.run(['ibm5100'],input='SET 3.072100\nEXIT\n',text=True,capture_output=True,check=True)
 current=state();check('IBN and service agree',current['divergence']=='3.072100' and current['applied'])
 message='V3 shared-state fixture'
 expected=sl.send_dmail(message,current['divergence'])
 third=sp.run(['dmail',message],text=True,capture_output=True,check=True)
 current=state();check('local D-Mail serialized arithmetic',current['divergence']==expected and current['applied'])
 check('local D-Mail reports service application','session service' in third.stdout)
 for name,sha in [('steins-gate','0fef65f9a8fd763e1745739ed1b0ac84368ce47156910a779125ce4f831a1440'),('hinamizawa','5ba3560971f3c0a1fd2326dae6609ed96506fdb13c1ea575ec234ff0fea8a403'),('hitogashima','966e415f1b69c43023046fdc341ad414bb2bae0d3c59b1ccad4e0454f6593414')]:
  path=Path('/usr/share/backgrounds/steins-prototype')/(name+'.png')
  check('approved artwork hash '+name,hashlib.sha256(path.read_bytes()).hexdigest()==sha)
finally:
 sp.run(['steins-worldline','set',initial],capture_output=True,check=True)
check('initial worldline restored',state()['divergence']==initial and state()['applied'])
print(json.dumps({'checks':results,'passed':len(results),'total':len(results),'initial':initial},indent=2))
