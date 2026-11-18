#!/usr/bin/python3
"""Real six-world service/config/file-hash/QMP qualification in the owned guest."""
import ast,json,shlex,time
from pathlib import Path
from urllib.parse import urlparse,unquote
from vm_lab import Lab
lab=Lab();root=lab.project;folder=root/'evidence/v3-integration/worlds';folder.mkdir(exist_ok=False)
manifest={p['worldline']:p for p in json.loads((root/'prototype/artwork-v3/PROVENANCE.json').read_text())}
worlds=[('alpha','0.571024'),('steins-gate','1.048596'),('hinamizawa','2.198306'),('hitogashima','3.072100'),('lugunica','4.250801'),('mitakihara','5.093001')]
code='''import dbus,json,hashlib;from pathlib import Path
b=dbus.SessionBus();i=dbus.Interface(b.get_object('org.steinsos.Worldline1','/org/steinsos/Worldline'),'org.steinsos.Worldline1')
s=json.loads(i.SetDivergence(VALUE,timeout=65))
p=Path('/usr/share/backgrounds/steins-prototype')/(s['id']+'.png')
shell=dbus.Interface(b.get_object('org.kde.plasmashell','/PlasmaShell'),'org.kde.PlasmaShell')
script="var out=[];var ds=desktops();for(var i=0;i<ds.length;i++){ds[i].currentConfigGroup=['Wallpaper','org.kde.image','General'];out.push(String(ds[i].readConfig('Image','')));}print(JSON.stringify(out));"
print(json.dumps({'state':s,'wallpaper_uris':json.loads(str(shell.evaluateScript(script,timeout=20))),'png_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
'''
def request(value):
 rc,out=lab.serial('export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_RUNTIME_DIR=/run/user/1000; python3 -c '+shlex.quote('exec(bytes.fromhex('+repr(code.replace('VALUE',repr(value)).encode().hex())+').decode())'),55)
 if rc:raise RuntimeError(out)
 return json.loads(out[out.index('{'):])
results=[]
lab.serial('export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_RUNTIME_DIR=/run/user/1000; qdbus6 org.kde.KWin /KWin org.kde.KWin.showDesktop true',10);time.sleep(.5)
try:
 for name,value in worlds:
  result=request(value)
  assert result['state']['id']==name and result['state']['applied'] is True,result
  assert result['png_sha256']==manifest[name]['sha256'],result
  assert result['wallpaper_uris'] and all(unquote(urlparse(uri).path)==('/usr/share/backgrounds/steins-prototype/'+name+'.png') for uri in result['wallpaper_uris']),result
  time.sleep(2.5)
  path=folder/(name+'.png');lab.qmp('screendump',{'filename':str(path),'format':'png'})
  result.update(worldline=name,screenshot=str(path.relative_to(root)),passed=True);results.append(result)
finally:
 try:request('1.048596')
 finally:lab.serial('export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_RUNTIME_DIR=/run/user/1000; qdbus6 org.kde.KWin /KWin org.kde.KWin.showDesktop false',10)
(root/'evidence/v3-integration/six-world-runtime.json').write_text(json.dumps({'passed':len(results),'total':6,'checks':results,'scope':'actual guest state, Plasma image URI, file SHA and QMP screenshots; no GPU performance claim'},indent=2)+'\n')
print('Six native worldline images, supported appearance and hashes verified')
