#!/usr/bin/python3
"""Explicit guest-only V3 panel activation; existing widgets/launchers retained."""
import json,os,subprocess as sp,time
from pathlib import Path
import dbus
assert Path('/etc/hostname').read_text().strip()=='steins-prototype' and os.getuid()==1000
os.environ.update(DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus',XDG_RUNTIME_DIR='/run/user/1000',WAYLAND_DISPLAY='wayland-0',STEINS_DESKTOP_BACKEND='plasma')
bus=dbus.SessionBus()
previous=bus.get_name_owner('org.steinsos.Worldline1') if bus.name_has_owner('org.steinsos.Worldline1') else None
sp.run(['pkill','-TERM','-f','^/usr/bin/python3 /usr/bin/steins-worldline-service$'])
for attempt in range(60):
 if not bus.name_has_owner('org.steinsos.Worldline1') or bus.get_name_owner('org.steinsos.Worldline1')!=previous:break
 time.sleep(.1)
else:raise RuntimeError('Previous service owner did not stop')
sp.run(['pkill','-TERM','-f','^/usr/bin/python3 /usr/bin/steins-navigator$'])
bus=dbus.SessionBus();state=dbus.Interface(bus.get_object('org.steinsos.Worldline1','/org/steinsos/Worldline'),'org.steinsos.Worldline1')
state.SetPreference('meter','false',timeout=65)
print(state.SetDivergence('1.048596',timeout=65))
shell=dbus.Interface(bus.get_object('org.kde.plasmashell','/PlasmaShell'),'org.kde.PlasmaShell')
answer=str(shell.evaluateScript(Path('/usr/share/steins-panel/attach.js').read_text(),timeout=20))
if 'Error' in answer or 'Exception' in answer:raise RuntimeError(answer)
script="""var ps=panels();for(var i=0;i<ps.length;i++){if(ps[i].location==='bottom'){ps[i].height=56;var ws=ps[i].widgets();for(var j=0;j<ws.length;j++){if(ws[j].type==='org.kde.plasma.icontasks'){ws[j].currentConfigGroup=['General'];var list=ws[j].readConfig('launchers',[]);if(list.indexOf('applications:steins-terminal-v3.desktop')<0){list.push('applications:steins-terminal-v3.desktop');ws[j].writeConfig('launchers',list);}}}}}"""
answer=str(shell.evaluateScript(script,timeout=20))
if 'Error' in answer or 'Exception' in answer:raise RuntimeError(answer)
print('V3 instrument added; existing widgets and launchers retained')
