#!/usr/bin/env python3
"""Execute real Plymouth script/native libraries headlessly; never starts plymouthd.

Uses installed 24.004.60 script.so with an EMPTY display list. Native parser,
images, Sprite state, refresh and prompt callbacks run. This is not a DRM/boot
or authentication test. Every mode/scenario is isolated in a short subprocess.
"""
import ctypes as C
import json
import math
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parent
class State(C.Structure):
 _fields_=[('user_data',C.c_void_p),('global_obj',C.c_void_p),('local',C.c_void_p),('this',C.c_void_p)]
class Return(C.Structure):
 _fields_=[('type',C.c_int),('object',C.c_void_p)]
def one(variant,mode,scenario):
 lib=C.CDLL('/usr/lib/x86_64-linux-gnu/plymouth/script.so')
 ply=C.CDLL('libply.so.5')
 def f(name,rest,args):
  fn=getattr(lib,name);fn.restype=rest;fn.argtypes=args;return fn
 state=f('script_state_new',C.POINTER(State),[C.c_void_p])(None)
 ply.ply_list_new.restype=C.c_void_p
 displays=ply.ply_list_new()
 image=f('script_lib_image_setup',C.c_void_p,[C.POINTER(State),C.c_char_p])(state,str(ROOT/'generated'/variant).encode())
 sprite=f('script_lib_sprite_setup',C.c_void_p,[C.POINTER(State),C.c_void_p])(state,displays)
 data=f('script_lib_plymouth_setup',C.c_void_p,[C.POINTER(State),C.c_int,C.c_int,C.c_void_p])(state,mode,30,None)
 f('script_lib_math_setup',C.c_void_p,[C.POINTER(State)])(state)
 f('script_lib_string_setup',C.c_void_p,[C.POINTER(State)])(state)
 parse=f('script_parse_string',C.c_void_p,[C.c_char_p,C.c_char_p])
 parsefile=f('script_parse_file',C.c_void_p,[C.c_char_p])
 execute=f('script_execute',Return,[C.POINTER(State),C.c_void_p])
 number=f('script_obj_hash_get_number',C.c_double,[C.c_void_p,C.c_char_p])
 string=f('script_obj_hash_get_string',C.c_void_p,[C.c_void_p,C.c_char_p])
 libc=C.CDLL(None);libc.free.argtypes=[C.c_void_p]
 def num(name):return number(state.contents.global_obj,name.encode())
 def text(name):
  ptr=string(state.contents.global_obj,name.encode())
  if not ptr:return None
  value=C.string_at(ptr).decode();libc.free(ptr);return value
 def run(code):
  op=parse(code.encode(),b'headless-fixture');assert op,'parse failure'
  result=execute(state,op);assert result.type!=2, ('execute failed',code)
 # No display backend is ever opened. Supply deterministic geometry only.
 run('Window.GetWidth = fun () { return 1366; }; Window.GetHeight = fun () { return 768; };')
 op=parsefile(str(ROOT/'generated'/variant/'steins.script').encode());assert op,'theme parse failure'
 result=execute(state,op);assert result.type!=2,'theme execution failure'
 refresh=f('script_lib_plymouth_on_refresh',None,[C.POINTER(State),C.c_void_p])
 password=f('script_lib_plymouth_on_display_password',None,[C.POINTER(State),C.c_void_p,C.c_char_p,C.c_int])
 question=f('script_lib_plymouth_on_display_question',None,[C.POINTER(State),C.c_void_p,C.c_char_p,C.c_char_p])
 message=f('script_lib_plymouth_on_display_message',None,[C.POINTER(State),C.c_void_p,C.c_char_p])
 normal=f('script_lib_plymouth_on_display_normal',None,[C.POINTER(State),C.c_void_p])
 expected=['INITIALISING LABORATORY','SHUTTING DOWN LABORATORY','RESTARTING LABORATORY','APPLYING SYSTEM UPDATES','APPLYING SYSTEM UPDATES','APPLYING FIRMWARE UPDATE','RESETTING SYSTEM','INITIALISING LABORATORY'][mode]
 assert text('last_message')==expected,(text('last_message'),expected)
 if scenario=='prompt':
  refresh(state,data);password(state,data,b'Unlock fixture volume:',3)
  assert num('settled')==1 and num('prompt_active')==1
  assert text('last_message')=='Unlock fixture volume: ***'
  message(state,data,b'External background status')
  assert text('last_message')=='Unlock fixture volume: ***','background text obscured auth'
  for _ in range(60):refresh(state,data)
  assert text('last_message')=='Unlock fixture volume: ***','refresh obscured auth'
  normal(state,data)
  assert num('prompt_active')==0 and text('last_message')=='External background status'
  question(state,data,b'Fixture question:',b'fixture-answer')
  assert text('last_message')=='Fixture question: fixture-answer'
  normal(state,data);assert text('last_message')=='External background status'
 else:
  for _ in range(40):refresh(state,data)
  assert num('settled')==1,'animation never settles'
  expected_frame=0 if variant.endswith('static') else (3 if variant.endswith('reduced') else 33)
  assert num('frame')==expected_frame,(variant,num('frame'),expected_frame)
  run('probe_trace = trace_sprite.GetOpacity(); probe_calibration = calibration_sprite.GetOpacity(); probe_logo = logo_sprite.GetOpacity();')
  assert num('probe_trace')==0 and num('probe_calibration')==0 and num('probe_logo')==1
  assert text('last_message')==expected,'animation overwrote real status'
 # Resize while settled is reflowed; native geometry does not retain stale position.
 run('Window.GetWidth = fun () { return 800; }; Window.GetHeight = fun () { return 600; };')
 refresh(state,data)
 assert num('width')==800 and num('height')==600 and math.isclose(num('scale'),.75), {n:num(n) for n in ('width','height','scale','settled','frame')}
 assert all(math.isfinite(num(n)) for n in ('cx','cy','width','height'))
 print(json.dumps({'variant':variant,'mode':mode,'scenario':scenario,'passed':True,'frame':num('frame'),'prompt_priority':scenario=='prompt','native_script_engine':True,'real_display':False}))
if __name__=='__main__':
 if len(sys.argv)>1:one(sys.argv[1],int(sys.argv[2]),sys.argv[3]);sys.exit()
 results=[]
 for variant in ['steins-lab-v3','steins-lab-v3-reduced','steins-lab-v3-static']:
  for mode in range(8):
   for scenario in ['animation','prompt']:
    completed=subprocess.run([sys.executable,__file__,variant,str(mode),scenario],text=True,capture_output=True,timeout=12)
    if completed.returncode:print(completed.stdout,completed.stderr);raise SystemExit(completed.returncode)
    results.append(json.loads(completed.stdout))
 report={'scope':'native Plymouth24.004.60 script engine with no display/daemon; not real boot qualification','checks_passed':len(results),'results':results}
 (ROOT/'evidence/native-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'native_cases_passed':len(results),'display_backend_opened':False,'plymouthd_started':False},indent=2))
