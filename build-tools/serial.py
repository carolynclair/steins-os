#!/usr/bin/env python3
"""Bounded read/write on the disposable VM serial console."""
import argparse,socket,sys,time
p=argparse.ArgumentParser();p.add_argument('--socket',default='/tmp/steins-serial.sock');p.add_argument('--wait',type=float,default=3);p.add_argument('text',nargs='?',default='');a=p.parse_args()
s=socket.socket(socket.AF_UNIX);s.connect(a.socket);s.settimeout(.25)
if a.text:s.sendall(a.text.encode()+b'\n')
end=time.monotonic()+a.wait
while time.monotonic()<end:
 try:
  b=s.recv(65536)
  if not b:break
  sys.stdout.write(b.decode(errors='replace'));sys.stdout.flush()
 except socket.timeout:pass
