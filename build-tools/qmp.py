#!/usr/bin/env python3
"""Minimal QEMU monitor client for disposable VM verification only."""
import argparse,json,socket,time
p=argparse.ArgumentParser();p.add_argument('--socket',default='/tmp/steins-qmp.sock');p.add_argument('command');p.add_argument('arguments',nargs='?',default='{}');a=p.parse_args()
s=socket.socket(socket.AF_UNIX);s.connect(a.socket);f=s.makefile('rwb',buffering=0)
def read():
 while True:
  d=json.loads(f.readline())
  if 'event' not in d:return d
read();f.write(b'{"execute":"qmp_capabilities"}\n');read()
f.write((json.dumps({'execute':a.command,'arguments':json.loads(a.arguments)})+'\n').encode());print(json.dumps(read(),indent=2))
if a.command == 'screendump':
 from PIL import Image
 from pathlib import Path
 name=json.loads(a.arguments)['filename']
 Image.open(name).save(str(Path(name).with_suffix('.png')))
