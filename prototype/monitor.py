#!/usr/bin/env python3
"""Guarded QMP for our standalone prototype, never the libvirt review VM."""
import argparse
import json
import socket
import time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument('command', choices=('screenshot', 'key', 'text', 'click', 'poweroff', 'query'))
ap.add_argument('value', nargs='?')
a = ap.parse_args()
with socket.socket(socket.AF_UNIX) as s:
    s.connect('/tmp/steins-design-qmp.sock')
    f = s.makefile('rwb', buffering=0)
    f.readline()
    def call(cmd, args=None):
        f.write((json.dumps({'execute': cmd, 'arguments': args or {}}) + '\n').encode())
        while True:
            r = json.loads(f.readline())
            if 'error' in r: raise RuntimeError(r)
            if 'return' in r: return r['return']
    call('qmp_capabilities')
    assert call('query-name')['name'] == 'SteinsOS-Design-Prototype'
    if a.command == 'screenshot':
        call('screendump', {'filename': str(Path(a.value).resolve()), 'format': 'png'})
    elif a.command == 'key':
        call('send-key', {'keys': [{'type': 'qcode', 'data': k} for k in a.value.split('-')], 'hold-time': 80})
        time.sleep(.2)
    elif a.command == 'click':
        x,y,width,height = map(int, a.value.split(','))
        call('input-send-event', {'events': [
            {'type':'abs', 'data':{'axis':'x', 'value':round(x/width*32767)}},
            {'type':'abs', 'data':{'axis':'y', 'value':round(y/height*32767)}},
            {'type':'btn', 'data':{'button':'left', 'down':True}}]})
        call('input-send-event', {'events':[{'type':'btn', 'data':{'button':'left', 'down':False}}]})
        time.sleep(.2)
    elif a.command == 'text':
        special = {'-':'minus', ' ':'spc', '.':'dot', '@':'shift-2', '_':'shift-minus', '/':'slash', ':':'shift-semicolon', '\n':'ret'}
        for ch in a.value:
            keys = special.get(ch, ('shift-' + ch.lower()) if ch.isupper() else ch)
            assert ch.isascii() and (ch.isalnum() or ch in special), ch
            call('send-key', {'keys':[{'type':'qcode','data':k} for k in keys.split('-')], 'hold-time':30})
            time.sleep(.07)
    elif a.command == 'poweroff': call('system_powerdown')
    else: print(json.dumps(call(a.value), indent=2))
