#!/usr/bin/python3
"""Real V4 six-world state, stable palette, artwork and QMP screenshots."""
import json,shlex,time,argparse
from pathlib import Path
from urllib.parse import unquote,urlparse
from vm_lab import Lab

ENV='export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_RUNTIME_DIR=/run/user/1000 STEINS_DESKTOP_BACKEND=plasma; '
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('label',nargs='?',default='final');args=parser.parse_args()
from vm_lab import engine
tag=engine.label(args.label)
lab=Lab(); root=lab.project; folder=root/('evidence/v4-design/worlds-'+tag);folder.mkdir(exist_ok=False)
manifest={p['worldline']:p for p in json.loads((root/'prototype/artwork-v3/PROVENANCE.json').read_text())}
worlds=[('alpha','0.571024'),('steins-gate','1.048596'),('hinamizawa','2.198306'),('hitogashima','3.072100'),('lugunica','4.250801'),('mitakihara','5.093001')]
code='''import dbus,json,hashlib;from pathlib import Path
b=dbus.SessionBus();i=dbus.Interface(b.get_object('org.steinsos.Worldline1','/org/steinsos/Worldline'),'org.steinsos.Worldline1')
s=json.loads(i.SetDivergence(VALUE,timeout=65));p=Path('/usr/share/backgrounds/steins-prototype')/(s['id']+'.png')
shell=dbus.Interface(b.get_object('org.kde.plasmashell','/PlasmaShell'),'org.kde.PlasmaShell')
script="var out=[];var ds=desktops();for(var i=0;i<ds.length;i++){ds[i].currentConfigGroup=['Wallpaper','org.kde.image','General'];out.push(String(ds[i].readConfig('Image','')));}print(JSON.stringify(out));"
pid=Path('/tmp/v4-design/probe.pid').read_text().strip();proc=Path('/proc')/pid/'stat'
print(json.dumps({'state':s,'wallpaper_uris':json.loads(str(shell.evaluateScript(script,timeout=20))),'png_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bash_pid':pid,'bash_start':proc.read_text().split()[21]}))
'''
def request(value):
 rc,out=lab.serial(ENV+'python3 -c '+shlex.quote(code.replace('VALUE',repr(value))),55)
 if rc: raise RuntimeError(out)
 return json.loads(out[out.index('{'):])
results=[]
rc,out=lab.serial(ENV+'qdbus6 org.kde.KWin /KWin org.kde.KWin.showDesktop true',10)
if rc: raise RuntimeError(out)
try:
 for name,value in worlds:
  result=request(value);s=result['state']
  assert s['id']==name and s['applied'] is True,result
  assert result['png_sha256']==manifest[name]['sha256'],result
  assert all(unquote(urlparse(uri).path)==('/usr/share/backgrounds/steins-prototype/'+name+'.png') for uri in result['wallpaper_uris']) and result['wallpaper_uris'],result
  if results:
   assert (result['bash_pid'],result['bash_start'])==(results[0]['bash_pid'],results[0]['bash_start']),result
   assert all(s['palette'][k]==results[0]['state']['palette'][k] for k in ('bg','bg_alt','fg','selection','muted')),result
  time.sleep(1.5);path=folder/(name+'.png');lab.qmp('screendump',{'filename':str(path),'format':'png'})
  result.update(worldline=name,screenshot=str(path.relative_to(root)),passed=True);results.append(result)
finally:
 request('2.198306')
 lab.serial(ENV+'qdbus6 org.kde.KWin /KWin org.kde.KWin.showDesktop false',10)
(root/('evidence/v4-design/six-world-runtime-'+tag+'.json')).write_text(json.dumps({'passed':len(results),'total':6,'checks':results,'scope':'native guest state, stable neutral chrome, unchanged artwork SHA/URI and actual Bash process continuity'},indent=2)+'\n')
print('Six worlds verified with stable chrome and unchanged running Bash PID')
