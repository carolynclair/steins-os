#!/usr/bin/env python3
"""Send input to the project test VM's QMP socket, never the host desktop."""
import argparse,json,socket,time
p=argparse.ArgumentParser();p.add_argument('--socket',default='/tmp/steins-qmp.sock');p.add_argument('action',choices=['text','key','click']);p.add_argument('value');a=p.parse_args()
s=socket.socket(socket.AF_UNIX);s.connect(a.socket);f=s.makefile('rwb',buffering=0)
def read():
 while True:
  v=json.loads(f.readline())
  if 'event' not in v:return v
def command(c,args):
 f.write((json.dumps({'execute':c,'arguments':args})+'\n').encode());r=read()
 if 'error' in r:raise RuntimeError(r)
read();command('qmp_capabilities',{})
def key(k):command('human-monitor-command',{'command-line':'sendkey '+k});time.sleep(.09)
if a.action=='key':key(a.value)
elif a.action=='click':
 x,y,w,h=map(int,a.value.split(','))
 command('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':round(x/w*32767)}},{'type':'abs','data':{'axis':'y','value':round(y/h*32767)}}]})
 command('input-send-event',{'events':[{'type':'btn','data':{'down':True,'button':'left'}}]});time.sleep(.12)
 command('input-send-event',{'events':[{'type':'btn','data':{'down':False,'button':'left'}}]})
else:
 mapping={' ':'spc','\n':'ret','-':'minus','_':'shift-minus','=':'equal','+':'shift-equal','/':'slash','.':'dot',',':'comma',':':'shift-semicolon',';':'semicolon',"'":'apostrophe','"':'shift-apostrophe','@':'shift-2','|':'shift-backslash','>':'shift-dot','<':'shift-comma','(':'shift-9',')':'shift-0','$':'shift-4','&':'shift-7','!':'shift-1','?':'shift-slash','\\':'backslash'}
 for c in a.value:
  if c in mapping:key(mapping[c])
  elif c.isascii() and c.isalnum():key(('shift-'+c.lower()) if c.isupper() else c)
  else:raise ValueError('Unsupported key '+repr(c))

time.sleep(0.8)
