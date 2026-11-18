#!/usr/bin/python3
"""Read-only final guest inventory and assertions, through the guarded serial API."""
import argparse,json,shlex
from vm_lab import Lab
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('label',nargs='?',default='final');args=parser.parse_args()
from vm_lab import engine
tag=engine.label(args.label);lab=Lab()
code='''import configparser,dbus,json,subprocess,os,time
from pathlib import Path
os.environ.update(DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus',XDG_RUNTIME_DIR='/run/user/1000')
b=dbus.SessionBus();deadline=time.monotonic()+35
while not b.name_has_owner('org.kde.plasmashell'):
 if time.monotonic()>deadline:raise RuntimeError('Plasma desktop did not become ready')
 time.sleep(.5)
time.sleep(2)
api=dbus.Interface(b.get_object('org.steinsos.Worldline1','/org/steinsos/Worldline'),'org.steinsos.Worldline1')
deadline=time.monotonic()+10
while True:
 state=json.loads(api.GetState())
 if state.get('applied') is True or state.get('errors'):break
 if time.monotonic()>deadline:raise RuntimeError('Worldline startup did not finish')
 time.sleep(.5)
shell=dbus.Interface(b.get_object('org.kde.plasmashell','/PlasmaShell'),'org.kde.PlasmaShell')
script="var out=[];panels().forEach(function(p){p.currentConfigGroup=['General'];var order=String(p.readConfig('AppletOrder',''));var ws=p.widgets().map(function(w){var result={id:w.id,type:w.type,geometry:w.geometry};if(w.type==='org.kde.plasma.icontasks'){w.currentConfigGroup=['General'];result.launchers=w.readConfig('launchers',[]);}return result;});out.push({id:p.id,height:p.height,location:p.location,order:order,widgets:ws});});print(JSON.stringify(out));"
cfg=configparser.ConfigParser(interpolation=None);cfg.read(Path.home()/'.config/kdeglobals')
run=lambda a:subprocess.check_output(a,text=True).strip()
data={'state':json.loads(api.GetState()),'panels':json.loads(str(shell.evaluateScript(script,timeout=20))),
 'packages':dict(line.split('\\t',1) for line in run(['dpkg-query','-W','steins-identity-v4','steins-panel-v4','steins-plasma-prototype','steins-surfaces-v4','steins-terminal-v3']).splitlines()),
 'qt_scheme':cfg['General']['ColorScheme'],'wm_active_background':cfg['WM']['activeBackground'],'icon_theme':cfg['Icons']['Theme'],
 'package_audit':run(['dpkg','--audit']),'failed_user_units':run(['systemctl','--user','--failed','--plain','--no-legend']),
 'failed_system_units':run(['systemctl','--failed','--plain','--no-legend']),
 'legacy_locker_exclusion':'NotShowIn=GNOME;Unity;KDE;' in (Path.home()/'.config/autostart/light-locker.desktop').read_text(),
 'native_locker_active':bool(dbus.Interface(b.get_object('org.freedesktop.ScreenSaver','/ScreenSaver'),'org.freedesktop.ScreenSaver').GetActive()),
 'wayland_socket':Path('/run/user/1000/wayland-0').is_socket()}
print(json.dumps(data))
'''
rc,out=lab.serial('python3 -c '+shlex.quote(code),55)
if rc:raise RuntimeError(out)
data=json.loads(out[out.index('{'):]);manifest=json.loads((lab.project/'dist/v4/BUILD-SET.json').read_text())
assert data['packages']=={p['package']:p['version'] for p in manifest['install_packages']},data
assert not any(data[k] for k in ('package_audit','failed_user_units','failed_system_units')),data
assert data['state']['applied'] is True and data['wayland_socket'] and data['legacy_locker_exclusion'],data
assert data['qt_scheme'].startswith('SteinsV4-') and data['wm_active_background']=='17,24,30' and data['icon_theme']=='SteinsLab',data
assert data['state']['preferences']=={'meter':False,'motion':'reduced'},data
panels=data['panels'];assert len(panels)==1 and panels[0]['height']==46 and panels[0]['location']=='bottom',data
widgets=panels[0]['widgets'];assert sum(w['type']=='org.steinsos.worldline.v4' for w in widgets)==1 and not any(w['type']=='org.steinsos.worldline' for w in widgets),data
tasks=next(w for w in widgets if w['type']=='org.kde.plasma.icontasks')
assert tasks['launchers']==['applications:steins-navigator-v4.desktop','applications:org.kde.dolphin.desktop','applications:steins-terminal-v3.desktop','applications:steins-dmail.desktop'],data
data.update(kvm=lab.qmp('query-kvm'),name=lab.qmp('query-name'),passed=True)
assert data['kvm']['enabled'] and data['name']['name']=='SteinsOS-V4-Design',data
path=lab.project/('evidence/v4-design/qualification-'+tag+'.json');path.write_text(json.dumps(data,indent=2)+'\n')
print('V4 package/configuration/KVM/Wayland/panel/locker inventory passed: '+str(path))
