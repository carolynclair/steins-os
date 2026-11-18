#!/usr/bin/env python3
"""Editable concept boards. These are design mockups, never runtime evidence."""
from contextlib import contextmanager
from html import escape
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
TOKENS = json.loads((ROOT/'system/tokens.json').read_text())
C = TOKENS['color']; WORLDS = TOKENS['worldlines']
SCENES = ('steins-gate', 'hinamizawa', 'hitogashima')
ART = {'steins-gate':'Urban summer / laboratory rooftops', 'hinamizawa':'Rural summer / forest and rice fields',
       'hitogashima':'Island summer / sea and open sky'}


class Board:
    def __init__(self, world='steins-gate', width=1920, height=1080, title='Worldline Shell', plain=False):
        self.world, self.W, self.H = world, width, height
        self.p = WORLDS[world]; self.acc = self.p['accent']; self.title=title
        self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height+72}" viewBox="0 0 {width} {height+72}">',
          '''<defs><filter id="shadow" x="-15%" y="-15%" width="135%" height="150%"><feDropShadow dx="0" dy="10" stdDeviation="18" flood-color="#000" flood-opacity=".25"/></filter>
          <linearGradient id="glass" x1="0" x2="0" y1="0" y2="1"><stop stop-color="#334653"/><stop offset=".35" stop-color="#101d26"/><stop offset="1" stop-color="#0b151d"/></linearGradient>
          <filter id="glow" x="-70%" y="-50%" width="240%" height="200%"><feGaussianBlur stdDeviation="2"/></filter></defs>''']
        self.rect(0,0,width,height+72,C['canvas'])
        if not plain:self.image(0,0,width,height,world)
        self.rect(0,height,width,72,'#0c1319')
        self.text(32,height+30,title,18,C['text'],600)
        self.text(32,height+54,f'DESIGN PROPOSAL · {width} × {height} target · Not installed or a running shell',13,C['muted'])
        self.text(width-32,height+44,'WORLDLINE / 01',13,C['muted'],anchor='end',spacing=2)

    def add(self,s): self.parts.append(s)
    def rect(self,x,y,w,h,fill,rx=0,stroke=None,sw=1,opacity=1,extra=''):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" opacity="{opacity}"'+(f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')+f' {extra}/>')
    def line(self,x1,y1,x2,y2,color=None,sw=1,opacity=1):
        self.add(f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color or C["border"]}" stroke-width="{sw}" opacity="{opacity}"/>')
    def text(self,x,y,value,size=14,color=None,weight=400,mono=False,anchor='start',spacing=0):
        self.add(f'<text x="{x}" y="{y}" fill="{color or C["text"]}" font-family="{("DejaVu Sans Mono" if mono else "Noto Sans")}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" letter-spacing="{spacing}">{escape(str(value))}</text>')
    def circle(self,x,y,r,fill,stroke=None,sw=1):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')+'/>')
    def image(self,x,y,w,h,world,opacity=1,rx=0):
        path=ROOT/'art'/f'{world}.png'
        if not path.exists(): self.rect(x,y,w,h,C['raised'],rx);return
        clip='clip'+str(len(self.parts))
        self.add(f'<defs><clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/></clipPath></defs>')
        self.add(f'<image x="{x}" y="{y}" width="{w}" height="{h}" xlink:href="../art/{world}.png" preserveAspectRatio="xMidYMid slice" opacity="{opacity}" clip-path="url(#{clip})"/>')
    @contextmanager
    def group(self,x=0,y=0,scale=1):
        self.add(f'<g transform="translate({x} {y}) scale({scale})">');yield;self.add('</g>')
    def icon(self,name,x,y,size=24,color=None):
        src=(ROOT/'system/icons'/f'{name}.svg').read_text()
        body=re.sub(r'^.*?<svg\b[^>]*>','',src,flags=re.S).rsplit('</svg>',1)[0]
        body=re.sub(r'<title\b[^>]*>.*?</title>','',body,flags=re.S)
        self.add(f'<g transform="translate({x} {y}) scale({size/24})" color="{color or C["text"]}" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">{body}</g>')
    def emblem(self,x,y,size):
        src=(ROOT/'art/steins-os-emblem.svg').read_text()
        view=re.search(r'viewBox="([^"]+)"',src).group(1)
        body=re.sub(r'^.*?<svg\b[^>]*>','',src,flags=re.S).rsplit('</svg>',1)[0]
        self.add(f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{view}">{body}</svg>')
    def button(self,x,y,w,label,primary=False,icon=None,h=38):
        self.rect(x,y,w,h,self.acc if primary else C['raised'],8,None if primary else C['border'])
        if icon:self.icon(icon,x+12,y+(h-18)/2,18,C['onAccent'] if primary else C['text'])
        self.text(x+(w/2 if not icon else 38),y+h/2+5,label,14,C['onAccent'] if primary else C['text'],600,anchor='middle' if not icon else 'start')
    def tube(self,x,y,number=None,scale=1,compact=False):
        number=number or self.p['divergence']
        with self.group(x,y,scale):
            at=0
            for char in number:
                cw=(10 if char=='.' else 21) if compact else (18 if char=='.' else 43)
                hh=32 if compact else 68
                self.rect(at,0,cw,hh,'url(#glass)',5 if compact else 9,C['border'])
                self.line(at+3,3,at+cw-3,3,'#b4c9d4',1,.19)
                fs=22 if compact else 46; yy=24 if compact else 51
                self.add(f'<text x="{at+cw/2}" y="{yy}" fill="{self.acc}" opacity=".33" font-family="DejaVu Sans Mono" font-size="{fs}" text-anchor="middle" filter="url(#glow)">{char}</text>')
                self.text(at+cw/2,yy,char,fs,self.acc,500,True,'middle')
                at+=cw+(3 if compact else 6)
    def window(self,x,y,w,h,title,kind='files',active=True,scale=1):
        with self.group(x,y,scale):
            self.rect(0,0,w,h,C['panel'],12,C['border'],extra='filter="url(#shadow)"')
            self.rect(1,1,w-2,39,C['raised'] if active else C['panel'],11)
            self.rect(1,26,w-2,16,C['raised'] if active else C['panel'])
            self.line(18,1,74,1,self.acc if active else C['border'],2)
            self.icon(kind,16,11,20,self.acc if active else C['muted'])
            self.text(46,26,title,14,C['text'] if active else C['muted'],600)
            self.icon('minimize',w-113,12,18,C['muted']);self.icon('maximize',w-77,12,18,C['muted']);self.icon('close',w-41,12,18,C['text'])
            self.line(0,42,w,42,C['border'],1,.65)

    def panel(self,active='terminal'):
        w,h=self.W,self.H; yy=h-76
        self.rect(28,yy,w-56,56,C['panel'],16,C['border'],opacity=.98,extra='filter="url(#shadow)"')
        self.icon('launcher',48,yy+13,30,self.acc)
        self.text(94,yy+33,'Applications',14,C['text'],600)
        self.line(204,yy+10,204,yy+46,C['border'])
        self.rect(221,yy+5,184,46,C['canvas'],8)
        self.tube(237,yy+7,scale=.84,compact=True)
        self.text(313,yy+46,self.p['name'],10,C['muted'],anchor='middle',spacing=.5)
        tasks=[('terminal','Terminal'),('files','Files'),('dmail','D-Mail')]
        start=434
        for i,(icon,label) in enumerate(tasks):
            xx=start+i*70
            if active==icon:self.rect(xx-8,yy+7,54,42,C['raised'],9)
            self.icon(icon,xx+4,yy+14,26,self.acc if icon==active else C['text'])
            self.line(xx+10,yy+48,xx+24,yy+48,self.acc if icon==active else C['muted'],2)
        self.line(w-326,yy+10,w-326,yy+46,C['border'])
        self.icon('network',w-305,yy+17,22,C['muted']);self.icon('volume',w-266,yy+17,22,C['muted'])
        self.circle(w-218,yy+28,3,C['success'])
        self.text(w-175,yy+24,'20:17',17,C['text'],500)
        self.text(w-175,yy+43,'Sunday, 1 Nov',11,C['muted'])
        self.icon('power',w-68,yy+17,21,C['muted'])

    def terminal(self,x,y,scale=1,w=850,h=540):
        self.window(x,y,w,h,'Terminal', 'terminal',scale=scale)
        with self.group(x,y,scale):
            self.rect(1,43,w-2,38,C['canvas'])
            self.rect(12,49,180,31,C['raised'],6)
            self.circle(26,64,3,self.acc);self.text(40,69,'~/Projects',13,C['text'],500)
            self.icon('close',166,57,14,C['muted'])
            self.text(213,69,'SSH · lab',13,C['muted']);self.icon('plus',330,56,18,C['muted'])
            self.icon('navigator',w-310,13,16,self.acc)
            self.rect(w-286,5,144,32,C['canvas'],6,C['border'])
            self.tube(w-274,10,scale=.64,compact=True)
            self.rect(1,81,w-2,h-106,C['input'])
            self.text(22,114,'observer',14,self.acc,500,True);self.text(109,114,'~/Projects',14,C['muted'],mono=True)
            rows=[('❯ git status',C['text']),('On branch experiment',C['muted']),('nothing to commit, working tree clean',C['success']),('',C['text']),('❯ python3 experiment.py',C['text']),('Observation saved · 20:17:42',C['muted']),('',C['text']),('❯',self.acc)]
            for i,(line,col) in enumerate(rows):self.text(22,147+i*27,line,15,col,mono=True)
            self.rect(43,321,9,19,self.acc)
            self.line(1,h-25,w-1,h-25,C['border'],1,.6)
            self.text(19,h-8,'bash   /   UTF-8',11,C['muted'])
            self.text(w-18,h-8,'Local session',11,C['muted'],anchor='end')
    def files(self,x,y,scale=1,w=700,h=460):
        self.window(x,y,w,h,'Files', 'files',active=False,scale=scale)
        with self.group(x,y,scale):
            self.icon('arrow-right',17,57,20,C['muted']);self.text(50,72,'Home  /  Projects',13,C['text'])
            self.icon('search',w-39,57,20,C['muted']);self.line(0,87,w,87,C['border'],1,.7)
            self.rect(1,88,149,h-102,C['canvas'])
            for i,(icon,title) in enumerate([('files','Home'),('files','Documents'),('files','Downloads'),('network','Network')]):
                if i==0:self.rect(9,101,130,34,C['selection'],6)
                self.icon(icon,20,110+i*43,18,self.acc if i==0 else C['muted']);self.text(48,124+i*43,title,12)
            self.text(171,119,'Name',12,C['muted']);self.text(w-126,119,'Modified',12,C['muted'])
            for i,(name,modified) in enumerate([('Experiments','Today'),('Worldline','Yesterday'),('Notes','Yesterday'),('Research','26 Oct')]):
                yy=145+i*55
                if i==1:self.rect(163,yy-7,w-176,45,C['selection'],7)
                self.icon('files',176,yy+1,24,self.acc if i==1 else C['muted']);self.text(213,yy+20,name,14)
                self.text(w-126,yy+20,modified,12,C['muted'])
    def mail(self,x,y,scale=1,w=650,h=300):
        # This is a supported-theme target, not a replacement client layout promise.
        self.window(x,y,w,h,'D-Mail · Thunderbird', 'dmail',active=False,scale=scale)
        with self.group(x,y,scale):
            self.button(15,54,146,'New message',False,'plus',36)
            self.rect(1,99,157,h-112,C['canvas']);self.rect(9,113,140,32,C['selection'],6)
            for i,label in enumerate(['Inbox','Sent','Drafts']):self.text(24,134+i*36,label,13)
            self.text(180,121,'Laboratory briefing',16,C['text'],600)
            self.text(180,147,'observer@lab.invalid',12,C['muted'])
            self.line(178,164,w-20,164,C['border'],1,.7)
            for i,line in enumerate(['The next experiment is ready.','Notes and attachments are included.']):self.text(180,191+i*25,line,13,C['text'])
            self.text(180,h-26,'1 attachment',12,C['muted'])
    def navigator(self,x,y,scale=1,current=None,selected=None,error=False):
        w,h=530,650
        selected=selected or ('hinamizawa' if self.world=='steins-gate' else 'steins-gate')
        self.window(x,y,w,h,'Worldlines','navigator',scale=scale)
        with self.group(x,y,scale):
            self.text(22,78,'Choose a worldline',24,C['text'],600)
            self.circle(25,101,3,C['success']);self.text(37,106,'Stable · '+self.p['name'],12,C['muted'])
            self.rect(22,125,486,40,C['input'],7,C['border']);self.icon('search',34,136,18,C['muted']);self.text(63,151,'Find a worldline',13,C['muted'])
            for i,pid in enumerate(SCENES):
                yy=184+i*106;wp=WORLDS[pid];sel=(pid==selected)
                self.rect(22,yy,486,94,C['raised'] if not sel else C['selection'],10,wp['accent'] if sel else C['border'],2 if sel else 1)
                self.image(30,yy+8,120,78,pid,rx=6)
                self.text(166,yy+29,wp['name'],16,C['text'],600)
                self.text(166,yy+52,wp['divergence'],13,wp['accent'],500,True)
                self.text(166,yy+73,'Current worldline' if pid==self.world else ('Selected destination' if sel else 'Select destination'),11,C['muted'])
                if pid==self.world:self.circle(483,yy+28,4,C['success'])
                elif sel:self.icon('arrow-right',474,yy+33,20,wp['accent'])
            self.text(22,528,'ALL WORLDS',10,C['muted'],600,spacing=1.5)
            for i,pid in enumerate(['alpha','lugunica','mitakihara']):
                xx=22+i*164;self.rect(xx,542,158,36,C['raised'],6,C['border']);self.text(xx+12,565,WORLDS[pid]['name'],12)
            if error:self.text(22,596,'Wallpaper could not load. Still on '+self.p['name']+'.',11,C['error'])
            else:self.text(22,596,'Motion follows your accessibility preference.',11,C['muted'])
            self.button(22,602,110,'Cancel',False,h=36)
            self.button(146,602,362,'Retry shift' if error else 'Shift to '+WORLDS[selected]['name'],True,h=36)
    def launcher(self,x,y,scale=1):
        w,h=430,512
        self.window(x,y,w,h,'Applications','launcher',scale=scale)
        with self.group(x,y,scale):
            self.rect(20,63,390,42,C['input'],8,C['border']);self.icon('search',32,75,18,C['muted']);self.text(62,90,'Search apps, files and actions',13,C['muted'])
            self.text(22,137,'PINNED',10,C['muted'],600,spacing=1.5)
            entries=[('terminal','Terminal'),('files','Files'),('dmail','D-Mail'),('navigator','Worldlines'),('settings','Settings'),('lock','Lock screen')]
            for i,(icon,title) in enumerate(entries):
                xx=22+(i%2)*197;yy=153+(i//2)*83
                self.rect(xx,yy,187,71,C['raised'],9,self.acc if i==0 else C['border'])
                self.icon(icon,xx+14,yy+22,28,self.acc if i==0 else C['text']);self.text(xx+54,yy+40,title,14,C['text'],500)
            self.line(22,420,408,420,C['border'])
            self.text(22,451,'Recently used',12,C['muted']);self.text(22,478,'Project notes',13,C['text'])
            self.text(408,478,'Enter to open',11,C['muted'],anchor='end')
    def notification(self,x,y):
        self.rect(x,y,340,100,C['panel'],12,C['border'],extra='filter="url(#shadow)"')
        self.icon('dmail',x+17,y+19,22,self.acc);self.text(x+51,y+31,'New message',14,C['text'],600)
        self.text(x+51,y+56,'Laboratory briefing',13,C['muted']);self.text(x+51,y+80,'D-Mail',11,C['muted'])
    def finish(self):return '\n'.join(self.parts+['</svg>'])


def build_board(kind='desktop',world='steins-gate',width=1920,height=1080):
    b=Board(world,width,height,{'desktop':'Worldline Shell / integrated divergence', 'launcher':'Applications / original shell interaction',
      'multi-app':'One desktop / four everyday applications','plain':'Identity test / wallpaper hidden',
      'terminal':'Terminal / everyday flagship','navigator':'Worldlines / compact and expanded',
      'system':'System surfaces / shared visual language','error':'Appearance recovery / explicit state',
      'login':'Login / familiar secure authentication','lock':'Lock / quiet continuity',
      'boot':'Boot / original emblem and restrained identity',
      'large-text':'Larger text / navigator reflow study'}[kind],plain=kind in ('plain','boot'))
    W,H=width,height;s=min(1,(W-80)/1300,(H-150)/780)
    if kind in ('desktop','launcher'):
        b.panel('files')
        if kind=='launcher':b.launcher(28,H-76-532,scale=1)
    elif kind in ('multi-app','plain'):
        if W>=1700:
            b.terminal(48,70,1,850,540);b.files(980,44,.98,820,480)
            b.mail(1120,575,1,720,300);b.navigator(680,318,.9)
        else:
            b.terminal(32,70,1,850,540);b.files(W-732,12,1,700,460)
            b.mail(W-682,H-76-316,1,650,300)
            b.navigator(W*.365,H-76-666,1)
        b.panel()
    elif kind=='terminal':
        ss=min(1.3,(W-80)/1000,(H-96)/650)
        b.terminal((W-1000*ss)/2,(H-76-650*ss)/2,ss,1000,650);b.panel()
    elif kind in ('navigator','error'):
        ns=min(1,(H-135)/650)
        b.navigator(W*.51,H-115-650*ns,ns,error=kind=='error')
        ex,ey=48,100
        b.window(ex,ey,430,210,'Divergence meter','navigator',scale=ns)
        with b.group(ex,ey,ns):
            b.tube(43,68);b.text(215,167,b.p['name'],14,b.acc,600,anchor='middle');b.text(215,193,'Expanded meter · shared worldline state',11,C['muted'],anchor='middle')
        b.panel()
    elif kind=='system':
        b.window(70,110,590,430,'Appearance','settings')
        with b.group(70,110):
            b.text(24,87,'Worldline appearance',24,C['text'],600)
            for i,(title,val) in enumerate([('Current worldline',b.p['name']),('Motion','Reduced'),('Shift sounds','Off'),('Compact divergence','Always visible')]):
                yy=126+i*64;b.text(24,yy,title,14);b.text(555,yy,val,14,b.acc,anchor='end');b.line(24,yy+23,566,yy+23,C['border'],1,.5)
            b.button(24,366,190,'Open worldlines',True)
        xx=730 if W>1500 else 690
        b.notification(xx,110)
        b.window(xx,249,440,238,'Power','power')
        with b.group(xx,249):
            b.text(22,85,'Ready to shut down?',22,C['text'],600);b.text(22,120,'Your open apps can save their work first.',13,C['muted'])
            b.button(22,171,110,'Cancel');b.button(150,171,268,'Shut down',True,'power')
        b.text(74,H-141,'Boot / login / lock: same surfaces, type and original emblem.',15,C['text'])
        b.panel('settings')
    elif kind=='boot':
        b.emblem(W/2-58,H/2-130,116)
        b.text(W/2,H/2+28,'Steins;OS',32,C['text'],500,anchor='middle')
        b.rect(W/2-72,H/2+67,144,3,C['border'],2)
        b.rect(W/2-72,H/2+67,63,3,b.acc,2)
        b.text(W/2,H/2+105,'Starting your session',14,C['muted'],anchor='middle')
    elif kind=='lock':
        b.rect(0,0,W,H,C['canvas'],opacity=.4)
        b.text(W/2,H*.37,'20:17',76,C['text'],400,anchor='middle')
        b.text(W/2,H*.37+43,'Sunday, 1 November',21,C['text'],anchor='middle')
        b.icon('lock',W/2-12,H*.73,24,C['text'])
        b.text(W/2,H*.73+57,'Press a key to unlock',15,C['text'],anchor='middle')
    elif kind=='login':
        b.rect(0,0,W,H,C['canvas'],opacity=.32)
        xx=W/2-240;yy=H/2-220
        b.rect(xx,yy,480,440,C['panel'],16,C['border'],extra='filter="url(#shadow)"')
        b.emblem(xx+210,yy+28,60)
        b.text(W/2,yy+129,'Welcome back',27,C['text'],600,anchor='middle')
        b.text(W/2,yy+161,'Observer',15,C['muted'],anchor='middle')
        b.text(xx+38,yy+205,'Password',13,C['text'])
        b.rect(xx+36,yy+219,408,48,C['input'],8,b.acc,2)
        b.text(xx+54,yy+250,'••••••••',20,C['text'])
        b.button(xx+36,yy+287,408,'Sign in',True,h=44)
        b.text(W/2,yy+374,'Worldline session',12,C['muted'],anchor='middle')
        b.icon('power',W-67,H-64,24,C['text'])
    elif kind=='large-text':
        xx=W/2-340;yy=24;ww=680;hh=H-124
        b.window(xx,yy,ww,hh,'Worldlines','navigator')
        with b.group(xx,yy):
            b.text(24,86,'Choose a worldline',29,C['text'],600)
            b.circle(28,111,4,C['success']);b.text(43,117,'Stable · Steins Gate',16,C['muted'])
            b.rect(24,139,632,48,C['input'],8,C['border']);b.icon('search',37,151,24,C['muted']);b.text(77,171,'Find a worldline',18,C['muted'])
            for i,pid in enumerate(['steins-gate','hinamizawa']):
                cy=208+i*140;p=WORLDS[pid]
                b.rect(24,cy,616,124,C['selection'] if i else C['raised'],10,p['accent'] if i else C['border'],2 if i else 1)
                b.image(34,cy+10,144,104,pid,rx=7)
                b.text(197,cy+38,p['name'],22,C['text'],600)
                b.text(197,cy+71,p['divergence'],18,p['accent'],mono=True)
                b.text(197,cy+101,'Selected destination' if i else 'Current worldline',16,C['muted'])
            b.rect(651,208,5,286,C['border'],2);b.rect(651,208,5,140,C['muted'],2)
            b.text(24,513,'Scroll for more worlds',16,C['muted'])
            b.line(24,532,656,532,C['border'])
            b.rect(24,550,632,48,b.acc,8)
            b.text(340,581,'Shift to Hinamizawa',18,C['onAccent'],600,anchor='middle')
        b.panel()
    return b.finish()


def storyboard():
    b=Board(width=1920,height=1080,title='Worldline shift / target sequence, not a compositor capture',plain=True)
    b.text(50,66,'A change of reality, in 800 ms',32,C['text'],600)
    b.text(50,102,'Proposed full-motion sequence after preparation · input remains available · sound optional',16,C['muted'])
    stages=[('01','Activate','0–90 ms','Immediate feedback on the trigger.'),('02','Instability','90–220 ms','Tube digits roll once; no flashing.'),
      ('03','Distort','220–400 ms','One low-amplitude spatial ripple.'),('04','Transform','400–620 ms','Palette and scene commit together.'),('05','Stabilise','620–800 ms','Digits settle; quiet success cue.')]
    for i,(n,title,timing,desc) in enumerate(stages):
        x=50+i*366;y=150
        b.image(x,y,346,220,'steins-gate' if i<3 else 'hinamizawa',rx=10)
        b.rect(x+10,y+180,326,30,C['panel'],6,opacity=.97)
        b.tube(x+20,y+184,'1.048596' if i<2 else ('2.1·····' if i==2 else '2.198306'),.66,True)
        if i==2:
            for off in range(4):b.add(f'<path d="M{x+65+off*48} {y+8} Q{x+155+off*28} {y+90} {x+80+off*54} {y+220}" fill="none" stroke="#b8ca81" stroke-width="2" opacity=".6"/>')
        b.text(x,y+263,n+' / '+title,21,C['text'],600);b.text(x,y+294,timing,14,b.acc,mono=True)
        # Short enough to avoid pseudo-browser/canvas line wrapping.
        for line_no,line in enumerate(desc.split('; ')):b.text(x,y+325+line_no*23,line,13,C['muted'])
    b.line(50,570,1870,570,C['border'])
    for i,(title,timing,text) in enumerate([('FULL','800 ms','Single spatial pulse; optional soft cues.'),('REDUCED','180 ms','Short crossfade; static digits; no warp.'),('OFF','Immediate','Apply state; keep confirmation visible.')]):
        x=50+i*610;b.rect(x,616,580,134,C['panel'],12,C['border']);b.text(x+22,650,title,12,b.acc,600,spacing=1.4);b.text(x+22,689,timing,25,C['text'],600);b.text(x+22,722,text,14,C['muted'])
    b.text(50,823,'If preparation fails',20,C['text'],600);b.text(50,858,'Keep the old worldline and offer Retry. Never play a successful transition for a failed change.',16,C['muted'])
    b.text(50,922,'If the effect is unavailable',20,C['text'],600);b.text(50,957,'Apply without distortion. Apps, authentication surfaces and user data remain intact.',16,C['muted'])
    return b.finish()


def render(svg_path):
    # Render from the asset root, so librsvg's local-resource rules are respected.
    relative=svg_path.relative_to(ROOT)
    temporary=ROOT/('.render-'+svg_path.name)
    temporary.write_text(svg_path.read_text().replace('../art/','art/'))
    png=svg_path.with_suffix('.png')
    try:
        subprocess.run(['docker','run','--rm','--user',f'{__import__("os").getuid()}:{__import__("os").getgid()}',
            '-v',str(ROOT)+':/design','-w','/design','steins-os-builder:trixie','rsvg-convert',
            temporary.name,'-o',str(png.relative_to(ROOT))],check=True)
    finally:temporary.unlink(missing_ok=True)


def main():
    out=ROOT/'boards';out.mkdir(exist_ok=True)
    index=[]
    cases=[(kind,'steins-gate',1920,1080) for kind in ['desktop','launcher','multi-app','plain','terminal','navigator','system','error','boot','login','lock']]
    cases += [('desktop',world,1920,1080) for world in ['hinamizawa','hitogashima']]
    cases += [(kind,world,1920,1080) for world in ['hinamizawa','hitogashima'] for kind in ['launcher','multi-app','plain','terminal','navigator','error']]
    cases += [(kind,'steins-gate',w,h) for w,h in [(1280,800),(1366,768)] for kind in ['desktop','launcher','multi-app','terminal','navigator']]
    cases += [('desktop',world,w,h) for world in ['hinamizawa','hitogashima'] for w,h in [(1280,800),(1366,768)]]
    cases += [('large-text','steins-gate',1366,768)]
    for kind,world,w,h in cases:
        name=f'{kind}-{world}-{w}x{h}'
        p=out/(name+'.svg');p.write_text(build_board(kind,world,w,h));render(p)
        index.append({'id':name,'kind':kind,'worldline':world,'width':w,'height':h,'svg':'boards/'+p.name,'png':'boards/'+p.with_suffix('.png').name})
        print('Rendered',name,flush=True)
    p=out/'shift-storyboard.svg';p.write_text(storyboard());render(p)
    index.append({'id':'shift-storyboard','kind':'storyboard','worldline':'steins-gate','width':1920,'height':1080,'svg':'boards/'+p.name,'png':'boards/'+p.with_suffix('.png').name})
    (ROOT/'BOARDS.json').write_text(json.dumps(index,indent=2)+'\n')


if __name__=='__main__':raise SystemExit('Use build_v2.py to render this version; common_board.py is a helper only.')
