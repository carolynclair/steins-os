#!/usr/bin/python3
"""Functional checks in the isolated validation fork; no external accounts/mail."""
import json
import os
from pathlib import Path
import subprocess
import time
import dbus

assert Path('/etc/hostname').read_text().strip()=='steins-prototype'
assert Path('/tmp/v2-validation').is_dir()
os.environ.update(DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus',XDG_RUNTIME_DIR='/run/user/1000',
                  WAYLAND_DISPLAY='wayland-0',STEINS_DESKTOP_BACKEND='plasma')
bus=dbus.SessionBus()
api=dbus.Interface(bus.get_object('org.steinsos.Worldline1','/org/steinsos/Worldline'),'org.steinsos.Worldline1')
shell=dbus.Interface(bus.get_object('org.kde.plasmashell','/PlasmaShell'),'org.kde.PlasmaShell')
checks=[]
def check(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
    if not condition:raise AssertionError(name)
def state():return json.loads(api.GetState())
def observed(pid):
    for _ in range(35):
        v=state()
        if v['id']==pid and v.get('applied'):return v
        time.sleep(.2)
    raise AssertionError('Service did not apply '+pid)

before=state()
session=subprocess.check_output(['loginctl','show-user','1000','-p','Display','--value'],text=True).strip()
stype=subprocess.check_output(['loginctl','show-session',session,'-p','Type','--value'],text=True).strip()
check('graphical session Wayland',stype=='wayland')
check('six registry entries',len(json.loads(api.ListWorldlines()))==6)
number=state()['divergence']
try:api.SetDivergence('NaN')
except dbus.DBusException:pass
else:raise AssertionError('Invalid divergence accepted')
check('invalid request preserves divergence',state()['divergence']==number)
for value,pid in [('1.048596','steins-gate'),('2.198306','hinamizawa'),('3.072100','hitogashima')]:
    answer=json.loads(api.SetDivergence(value,timeout=40))
    check(pid+' apply result',answer['applied'] and not answer['errors'])
    actual=str(shell.evaluateScript("var d=desktops()[0];d.currentConfigGroup=['Wallpaper','org.kde.image','General'];print(d.readConfig('Image'));"))
    check(pid+' wallpaper actually changed',pid+'.png' in actual)
    check(pid+' active Qt scheme','ColorScheme=Steins-'+pid in Path.home().joinpath('.config/kdeglobals').read_text())
    check(pid+' persisted number',Path.home().joinpath('.local/state/steins/divergence').read_text().strip()==value)
check('no default Conky process',subprocess.run(['pgrep','-x','conky'],capture_output=True).returncode!=0)
subprocess.run(['steins-worldline','set','2.198306','--no-apply'],capture_output=True,check=True)
check('legacy CLI observed by service',observed('hinamizawa')['divergence']=='2.198306')
env={**os.environ,'STEINS_FAST':'1','STEINS_NO_APPLY':'1'}
ibn=subprocess.run(['ibm5100'],input='SET 1.048596\nDIVERGENCE\nQUIT\n',text=True,capture_output=True,env=env,timeout=25)
check('IBN command process exits successfully',ibn.returncode==0)
check('IBN SET updates shared service',observed('steins-gate')['divergence']=='1.048596')
check('IBN reports requested number','1.048596' in ibn.stdout)
notify=dbus.Interface(bus.get_object('org.freedesktop.Notifications','/org/freedesktop/Notifications'),'org.freedesktop.Notifications')
notification_id=notify.Notify('Steins validation',0,'dialog-information','Isolated VM validation',
    'Notification delivery from the preserved prototype.',[],{},8000)
check('notification server accepted message',int(notification_id)>0)
api.SetDivergence('1.048596',timeout=40)
report={'checks':checks,'baseline_state':before,'final_state':state(),'session_type':stype,
        'notification_id':int(notification_id),'scope':'actual existing Plasma prototype in isolated fork; V2 shell/terminal/boot are previews',
        'not_tested':['SSH connection (client absent)','Zsh (absent)','Neovim (absent)','native cinematic transition','physical audio audibility','new flagship terminal frontend']}
Path('/tmp/v2-validation/runtime-results.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
