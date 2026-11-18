#!/usr/bin/env python3
"""Load the actual applet and API functions against a private fake session bus.

Everything, including any KDE activation, uses temporary HOME/XDG paths. No host
worldline service/layout is contacted and no VM is started. Added QML timers exist
only in the throwaway package copy; they drive the production methods directly.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile

HERE=Path(__file__).resolve().parent
FIXTURE=r'''
import dbus,dbus.service,json,os
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from pathlib import Path
DBusGMainLoop(set_as_default=True)
bus=dbus.SessionBus()
state={'interface':1,'divergence':'1.048596','id':'steins-gate','name':'Steins Gate','palette':{'accent':'#e99a45'},'preferences':{'meter':False,'motion':'reduced'},'applied':True,'errors':[]}
log=Path(os.environ['PANEL_FIXTURE_LOG'])
started=False
def record(method,args):
 with log.open('a') as f:f.write(json.dumps({'method':method,'args':list(args)})+'\n')
class Fixture(dbus.service.Object):
 @dbus.service.method('org.steinsos.Worldline1',in_signature='',out_signature='s')
 def GetState(self):
  global started
  if not started:
   started=True;GLib.timeout_add(10000,disappear);GLib.timeout_add(12500,reappear)
  record('GetState',[]);return json.dumps(state)
 @dbus.service.method('org.steinsos.Worldline1',in_signature='',out_signature='s')
 def ListWorldlines(self):
  record('ListWorldlines',[]);return json.dumps([{'id':'steins-gate','name':'Steins Gate','divergence':'1.048596'},{'id':'hinamizawa','name':'Hinamizawa','divergence':'2.198306'}])
 @dbus.service.method('org.steinsos.Worldline1',in_signature='ss',out_signature='s')
 def SetPreference(self,key,value):
  record('SetPreference',[str(key),str(value)]);state['preferences'][str(key)]=json.loads(str(value));return json.dumps(state)
 @dbus.service.method('org.steinsos.Worldline1',in_signature='s',out_signature='s')
 def SetDivergence(self,value):
  record('SetDivergence',[str(value)]);state['divergence']=str(value);state['id']='hinamizawa';state['name']='Hinamizawa';state['applied']=False;state['errors']=[{'step':'wallpaper','message':'controlled partial apply'}];return json.dumps(state)
 @dbus.service.method('org.steinsos.Worldline1',in_signature='',out_signature='s')
 def ApplyCurrent(self):
  record('ApplyCurrent',[]);state['applied']=True;state['errors']=[];return json.dumps(state)
 @dbus.service.method('org.steinsos.Worldline1',in_signature='',out_signature='s')
 def OpenNavigator(self):
  record('OpenNavigator',[]);return json.dumps(state)
name=dbus.service.BusName('org.steinsos.Worldline1',bus)
service=Fixture(bus,'/org/steinsos/Worldline')
def disappear():
 global name
 bus.release_name('org.steinsos.Worldline1');name=None;record('disappear',[]);return False
def reappear():
 global name
 name=dbus.service.BusName('org.steinsos.Worldline1',bus);record('reappear',[]);return False
GLib.MainLoop().run()
'''
TEST_TIMERS='''
    Timer { interval: 1800; running: true; onTriggered: root.setMeter(true) }
    Timer { interval: 2800; running: true; onTriggered: root.setMotion("off") }
    Timer { interval: 3800; running: true; onTriggered: root.selectWorld("2.198306") }
    Timer { interval: 4700; running: true; onTriggered: console.log("PANEL_PROBE " + JSON.stringify({phase:"partial",number:root.number,partial:root.partial,name:root.worldName,error:root.errorText})) }
    Timer { interval: 5800; running: true; onTriggered: root.call("ApplyCurrent", []) }
    Timer { interval: 7000; running: true; onTriggered: console.log("PANEL_PROBE " + JSON.stringify({phase:"applied",applied:root.applied})) }
    Timer { interval: 8000; running: true; onTriggered: root.call("OpenNavigator", []) }
    Timer { interval: 10800; running: true; onTriggered: console.log("PANEL_PROBE " + JSON.stringify({phase:"disconnected",connected:root.connected,number:root.number})) }
    Timer { interval: 14200; running: true; onTriggered: console.log("PANEL_PROBE " + JSON.stringify({phase:"reconnected",connected:root.connected,number:root.number})) }
'''
def main():
 (HERE/'evidence').mkdir(exist_ok=True)
 loader=HERE/'evidence/private-bus-loader.log'
 with tempfile.TemporaryDirectory(prefix='steins-panel-qa-') as tmp_name:
  tmp=Path(tmp_name);(tmp/'run').mkdir(mode=0o700)
  package=tmp/'package';shutil.copytree(HERE/'package',package)
  main=package/'contents/ui/main.qml';s=main.read_text();s=s.replace('    compactRepresentation:',TEST_TIMERS+'\n    compactRepresentation:',1);main.write_text(s)
  fixture=tmp/'fixture.py';fixture.write_text(FIXTURE)
  events=tmp/'events.jsonl'
  launch=tmp/'launch.sh';launch.write_text('#!/bin/sh\n/usr/bin/python3 "$1" &\nfixture_pid=$!\ntrap \'kill "$fixture_pid" 2>/dev/null || true\' EXIT\nsleep 0.3\ntimeout -k 2s 20s plasmawindowed "$2"\n')
  env=dict(os.environ,HOME=str(tmp),XDG_CONFIG_HOME=str(tmp/'config'),XDG_DATA_HOME=str(tmp/'data'),XDG_CACHE_HOME=str(tmp/'cache'),XDG_RUNTIME_DIR=str(tmp/'run'),QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',PANEL_FIXTURE_LOG=str(events))
  with loader.open('w') as f:
   result=subprocess.run(['dbus-run-session','--','sh',str(launch),str(fixture),str(package)],env=env,stdout=f,stderr=f,timeout=28)
  assert result.returncode==124,result.returncode
  records=[json.loads(line) for line in events.read_text().splitlines()]
  (HERE/'evidence/private-bus-events.json').write_text(json.dumps(records,indent=2)+'\n')
  text=loader.read_text()
  probes=[json.loads(line.split('PANEL_PROBE ',1)[1]) for line in text.splitlines() if 'PANEL_PROBE ' in line]
  by_phase={p['phase']:p for p in probes}
  assert {'method':'SetPreference','args':['meter','true']} in records,records
  assert {'method':'SetPreference','args':['motion','"off"']} in records,records
  assert {'method':'SetDivergence','args':['2.198306']} in records,records
  assert any(r['method']=='ApplyCurrent' for r in records)
  assert any(r['method']=='OpenNavigator' for r in records)
  assert by_phase['partial']['partial'] is True and by_phase['partial']['number']=='2.198306',by_phase
  assert 'controlled partial apply' in by_phase['partial']['error']
  assert by_phase['applied']['applied'] is True
  assert by_phase['disconnected']['connected'] is False and by_phase['disconnected']['number']=='—.——————'
  assert by_phase['reconnected']['connected'] is True and by_phase['reconnected']['number']=='2.198306'
  assert 'TypeError:' not in text and 'ReferenceError:' not in text and 'is not a type' not in text,text
  report={'source_sha256':hashlib.sha256((HERE/'package/contents/ui/main.qml').read_bytes()).hexdigest(),'scope':'isolated offscreen Plasma loader + real QML methods + private fake D-Bus; not VM/host deployment','passed':True,'probes':probes,'backend_calls':records,'loader_exit':result.returncode,'temporary_home_and_private_bus':True}
  (HERE/'evidence/private-bus-result.json').write_text(json.dumps(report,indent=2)+'\n')
  print(json.dumps(report,indent=2))
if __name__=='__main__':main()
