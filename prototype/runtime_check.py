#!/usr/bin/python3
"""Functional smoke checks inside the disposable design VM, after Plasma login."""
import json
import os
from pathlib import Path
import subprocess
import time
import dbus

assert Path('/etc/hostname').read_text().strip() == 'steins-prototype'
os.environ['DBUS_SESSION_BUS_ADDRESS'] = 'unix:path=/run/user/1000/bus'
bus = dbus.SessionBus()
interface = dbus.Interface(bus.get_object('org.steinsos.Worldline1', '/org/steinsos/Worldline'), 'org.steinsos.Worldline1')
state = lambda: json.loads(interface.GetState())
checks = []
def check(name, ok):
    checks.append({'name': name, 'passed': bool(ok)})
    if not ok: raise AssertionError(name)
display_session = subprocess.check_output(['loginctl', 'show-user', '1000', '-p', 'Display', '--value'], text=True).strip()
session_type = subprocess.check_output(['loginctl', 'show-session', display_session, '-p', 'Type'], text=True).strip()
check('actual graphical session is Wayland', session_type == 'Type=wayland')
packs = json.loads(interface.ListWorldlines())
check('six worldlines available', len(packs) == 6)
before = state()['divergence']
try:
    interface.SetDivergence('NaN')
except dbus.DBusException:
    pass
else:
    raise AssertionError('Invalid number was accepted')
check('invalid request preserves state', state()['divergence'] == before)
shell = dbus.Interface(bus.get_object('org.kde.plasmashell', '/PlasmaShell'), 'org.kde.PlasmaShell')
for value, pid in [('1.048596', 'steins-gate'), ('2.198306', 'hinamizawa'), ('3.072100', 'hitogashima')]:
    result = json.loads(interface.SetDivergence(value, timeout=40))
    check(pid + ' applied', result['applied'] and not result['errors'])
    wallpaper = str(shell.evaluateScript("var d=desktops()[0]; d.currentConfigGroup=['Wallpaper','org.kde.image','General']; print(d.readConfig('Image'));"))
    check(pid + ' actual Plasma wallpaper', pid + '.png' in wallpaper)
    check(pid + ' saved number', Path.home().joinpath('.local/state/steins/divergence').read_text().strip() == value)
    check(pid + ' active Qt scheme', ('ColorScheme=Steins-' + pid) in Path.home().joinpath('.config/kdeglobals').read_text())
check('monitor hidden', subprocess.run(['pgrep', '-x', 'conky'], capture_output=True).returncode != 0)
interface.SetPreference('meter', 'true', timeout=40)
time.sleep(2)
check('optional meter started', subprocess.run(['pgrep', '-f', '^/usr/bin/python3 /usr/bin/steins-meter$'], capture_output=True).returncode == 0)
interface.SetPreference('meter', 'false', timeout=40)
time.sleep(.5)
check('optional meter stopped', subprocess.run(['pgrep', '-f', '^/usr/bin/python3 /usr/bin/steins-meter$'], capture_output=True).returncode != 0)
subprocess.run(['steins-worldline', 'set', '2.198306', '--no-apply'], check=True, capture_output=True)
for _ in range(20):
    time.sleep(.3)
    current = state()
    if current.get('applied') and current['id'] == 'hinamizawa': break
check('legacy CLI observed by service', current['id'] == 'hinamizawa' and current.get('applied'))
interface.SetDivergence('1.048596', timeout=40)
report = {'checks': checks, 'state': state(),
          'session': session_type,
          'versions': subprocess.check_output(['dpkg-query', '-W', 'plasma-desktop', 'kwin-wayland', 'thunderbird', 'steins-desktop', 'steins-plasma-prototype'], text=True).strip()}
Path('/tmp/prototype-runtime.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
