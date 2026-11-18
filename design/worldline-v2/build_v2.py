#!/usr/bin/env python3
"""V2 refinement boards: design previews, never installed shell evidence."""
import json
from pathlib import Path
import common_board as base
from common_board import Board, C, WORLDS, ROOT, render


class V2(Board):
    def finish(self):
        return super().finish().replace('WORLDLINE / 01','STEINS;OS / V2')

    def window(self,x,y,w,h,title,kind='files',active=True,scale=1):
        super().window(x,y,w,h,title,kind,active,scale)
        with self.group(x,y,scale):
            # A restrained calibration corner is shared, not terminal-only decoration.
            self.add(f'<path d="M8 32V14Q8 8 14 8H37" fill="none" stroke="{self.acc if active else C["border"]}" stroke-width="1.5"/>')

    def panel(self,active='terminal'):
        yy=self.H-76;w=self.W
        self.rect(28,yy,w-56,56,C['panel'],16,C['border'],extra='filter="url(#shadow)"')
        self.add(f'<path d="M39 {yy+39}V{yy+20}Q39 {yy+11} 48 {yy+11}H78" fill="none" stroke="{self.acc}" stroke-width="1.5"/>')
        self.icon('launcher',50,yy+15,27,self.acc);self.text(94,yy+33,'Applications',14,C['text'],600)
        self.line(205,yy+10,205,yy+46,C['border'])
        self.rect(221,yy+5,184,46,C['input'],8,C['border'])
        self.tube(237,yy+7,scale=.84,compact=True)
        self.text(313,yy+46,self.p['name'],11,C['muted'],anchor='middle')
        # Workspaces and task state are practical controls, not decorative statistics.
        for i in range(3):
            xx=425+i*30
            self.rect(xx,yy+14,24,28,C['selection'] if i==0 else C['panel'],5,C['border'] if i==0 else None)
            self.text(xx+12,yy+33,str(i+1),12,self.acc if i==0 else C['muted'],600,anchor='middle')
        xx=535
        self.rect(xx,yy+7,130,42,C['raised'],9,C['border'])
        self.icon('terminal',xx+12,yy+17,22,self.acc);self.text(xx+44,yy+33,'Terminal',13,C['text'],600)
        self.line(xx+44,yy+48,xx+106,yy+48,self.acc,2)
        for i,name in enumerate(['files','dmail']):
            at=685+i*58;self.icon(name,at,yy+16,24,C['text']);self.circle(at+12,yy+47,1.5,C['muted'])
        self.line(w-324,yy+10,w-324,yy+46,C['border'])
        self.icon('network',w-304,yy+17,22,C['muted']);self.icon('volume',w-265,yy+17,22,C['muted'])
        self.text(w-190,yy+24,'20:17',17,C['text'],500);self.text(w-190,yy+43,'Sunday, 1 Nov',12,C['muted'])
        self.icon('power',w-68,yy+17,21,C['muted'])

    def flagship(self,x,y,w=1100,h=680,state='floating'):
        self.window(x,y,w,h,'Terminal','terminal')
        rail=176 if w>=900 else 48
        with self.group(x,y):
            self.rect(1,43,rail-1,h-69,C['canvas'])
            self.line(rail,43,rail,h-25,C['border'])
            if rail>60:
                self.text(16,77,'SESSIONS',11,C['muted'],600,spacing=1.4)
                sessions=[('Projects','bash · ~/Projects'),('Logs','bash · ~/Logs'),('SSH · lab','Not connected')]
                for i,(name,context) in enumerate(sessions):
                    yy=96+i*76
                    if i==0:
                        self.rect(8,yy,rail-16,64,C['selection'],7)
                        self.rect(8,yy+12,3,40,self.acc,1)
                    self.icon('terminal' if i<2 else 'network',20,yy+13,18,self.acc if i==0 else C['muted'])
                    self.text(47,yy+28,name,13,C['text'] if i==0 else C['muted'],600 if i==0 else 400)
                    self.text(20,yy+49,context,11,C['muted'])
                self.button(12,h-80,rail-24,'New session',False,'plus',36)
            else:
                for i in range(3):
                    if i==0:self.rect(6,54,36,36,C['selection'],6)
                    self.icon('terminal' if i<2 else 'network',14,62+i*53,20,self.acc if i==0 else C['muted'])
                self.icon('plus',14,h-64,20,C['muted'])
            self.rect(rail+1,43,w-rail-2,39,C['canvas'])
            self.rect(rail+10,49,156,33,C['raised'],7)
            self.circle(rail+24,65,3,self.acc);self.text(rail+37,70,'Projects',13,C['text'],600)
            self.icon('close',rail+143,58,14,C['muted'])
            self.text(rail+190,70,'Logs',13,C['muted']);self.icon('plus',rail+255,57,18,C['muted'])
            self.icon('search',w-47,57,18,C['muted'])
            self.rect(rail+1,82,w-rail-2,h-107,C['input'])
            self.line(rail+1,82,w-1,82,C['border'],1,.5)
            # Native PTY content is visually dominant. All example text is fictional.
            tx=rail+22;yy=116
            self.text(tx,yy,'observer@lab',14,self.acc,500,True)
            self.text(tx+135,yy,'~/Projects',14,C['muted'],mono=True)
            lines=[('❯ git status',C['text']),('On branch experiment',C['muted']),('nothing to commit, working tree clean',C['success']),
                ('',C['text']),('❯ python3 experiment.py',C['text']),('Observation saved · λ → Δ',C['muted']),('',C['text']),('❯',self.acc)]
            for i,(value,col) in enumerate(lines):self.text(tx,yy+36+i*27,value,15,col,mono=True)
            self.rect(tx+22,yy+36+7*27-16,9,19,self.acc)
            self.line(1,h-25,w-1,h-25,C['border'])
            self.text(16,h-8,'bash   /   UTF-8',12,C['muted'])
            self.text(w-18,h-8,'Local session',12,C['muted'],anchor='end')
            # Readout has a reserved interval, separate from caption actions.
            self.rect(w-290,5,148,32,C['input'],6,C['border'])
            self.tube(w-276,10,scale=.65,compact=True)

    def emblem_stage(self,x,y,size,stage):
        path=ROOT/'art/steins-os-emblem.svg'
        import re
        raw=path.read_text();view=re.search(r'viewBox="([^"]+)"',raw).group(1)
        body=re.sub(r'^.*?<svg\b[^>]*>','',raw,flags=re.S).rsplit('</svg>',1)[0]
        clip='assemble'+str(len(self.parts))
        fraction=[0,.26,.67,1,1][stage]
        self.add(f'<defs><clipPath id="{clip}"><rect x="{x}" y="{y+size*(1-fraction)}" width="{size}" height="{size*fraction}"/></clipPath></defs>')
        if stage:
            self.add(f'<g clip-path="url(#{clip})"><svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="{view}">{body}</svg></g>')
        if stage<3:
            for off in (-22,0,22):
                self.add(f'<path d="M{x-60} {y+size+off}H{x+size*.3}L{x+size*.6} {y+size*.5+off}H{x+size+60}" fill="none" stroke="{self.acc}" stroke-width="1.5" opacity=".45"/>')


def board(kind,world='steins-gate',width=1920,height=1080):
    labels={'terminal-floating':'Terminal V2 / floating session workspace','terminal-maximised':'Terminal V2 / maximised without wallpaper',
        'terminal-tiled':'Terminal V2 / tiled and compact rail','shell-plain':'V2 identity audit / neutral background',
        'workspace':'V2 workspace / shared visual grammar','navigator':'Navigator / established interaction preserved',
        'login':'Login continuity / visual target only'}
    b=V2(world,width,height,labels[kind],plain=kind in ('terminal-maximised','shell-plain'))
    W,H=width,height
    if kind=='terminal-floating':
        ww=min(1100,W-80);hh=min(680,H-120);b.flagship((W-ww)/2,(H-76-hh)/2,ww,hh)
    elif kind=='terminal-maximised':b.flagship(0,0,W,H-88,state='maximised')
    elif kind=='terminal-tiled':
        ww=(W-76)/2;hh=min(760,H-120);b.flagship(28,24,ww,hh,state='tiled');b.files(48+ww,24,1,ww,hh)
    elif kind in ('workspace','shell-plain'):
        if W>=1700:
            b.flagship(44,60,1100,680);b.files(1180,42,1,680,480);b.navigator(1060,366,.87)
        else:
            b.flagship(30,60,min(1100,W-90),min(620,H-145));b.navigator(W-560,H-76-666,1)
    elif kind=='navigator':b.navigator(W/2-265,H-76-666,1)
    elif kind=='login':
        b.rect(0,0,W,H,C['canvas'],opacity=.35);xx=W/2-240;yy=H/2-220
        b.rect(xx,yy,480,440,C['panel'],12,C['border']);b.emblem(xx+210,yy+28,60)
        b.text(W/2,yy+129,'Welcome back',27,C['text'],600,anchor='middle');b.text(W/2,yy+161,'Observer',15,C['muted'],anchor='middle')
        b.text(xx+38,yy+205,'Password',13,C['text']);b.rect(xx+36,yy+219,408,48,C['input'],8,b.acc,2)
        b.text(xx+54,yy+250,'••••••••',20,C['text']);b.button(xx+36,yy+287,408,'Sign in',True,h=44)
        b.text(W/2,yy+374,'Worldline session',12,C['muted'],anchor='middle')
    if kind!='login':b.panel()
    return b.finish()


def boot(stage,width=1366,height=768):
    names=['Signal emergence','Trace assembly','Provisional digits','Identity settles','Quiet handoff']
    b=V2('steins-gate',width,height,'Boot animation concept / '+names[stage],plain=True)
    W,H=width,height;cx=W/2;cy=H/2
    if stage<3:
        b.line(cx-200,cy+110,cx+200,cy+110,C['border'],1,.4)
        for i in range(3):b.line(cx-90,cy+112+i*7,cx+90,cy+112+i*7,b.acc,1,.14 if i else .3)
    if stage<4:b.emblem_stage(cx-68,cy-128,136,stage)
    if stage in (2,3):
        b.tube(cx-89,cy+45,'1.0·····' if stage==2 else '1.048596',scale=1,compact=True)
        b.text(cx,cy+101,'Visual identity sequence',12,C['muted'],anchor='middle')
    if stage==4:
        b.emblem(cx-56,cy-116,112);b.text(cx,cy+42,'Steins;OS',27,C['text'],600,anchor='middle')
        b.text(cx,cy+82,'Session ready',14,C['muted'],anchor='middle')
    return b.finish()


def main():
    out=ROOT/'boards';out.mkdir(exist_ok=True);items=[]
    for w,h in [(1920,1080),(1366,768),(1280,800)]:
        for kind in ('terminal-floating','terminal-maximised','terminal-tiled','login'):
            name=f'{kind}-steins-gate-{w}x{h}';p=out/(name+'.svg');p.write_text(board(kind,width=w,height=h));render(p)
            items.append({'id':name,'kind':kind,'worldline':'steins-gate','width':w,'height':h,'svg':'boards/'+p.name,'png':'boards/'+p.with_suffix('.png').name})
    for kind in ('workspace','shell-plain','navigator'):
        name=kind+'-steins-gate-1920x1080';p=out/(name+'.svg');p.write_text(board(kind));render(p)
        items.append({'id':name,'kind':kind,'worldline':'steins-gate','width':1920,'height':1080,'svg':'boards/'+p.name,'png':'boards/'+p.with_suffix('.png').name})
    for world in ('hinamizawa','hitogashima'):
        for kind in ('terminal-floating','workspace'):
            name=kind+'-'+world+'-1920x1080';p=out/(name+'.svg');p.write_text(board(kind,world));render(p)
            items.append({'id':name,'kind':kind,'worldline':world,'width':1920,'height':1080,'svg':'boards/'+p.name,'png':'boards/'+p.with_suffix('.png').name})
    for stage in range(5):
        name=f'boot-stage-{stage}';p=out/(name+'.svg');p.write_text(boot(stage));render(p)
        items.append({'id':name,'kind':'boot-stage','stage':stage,'worldline':'steins-gate','width':1366,'height':768,'svg':'boards/'+p.name,'png':'boards/'+p.with_suffix('.png').name})
    (ROOT/'BOARDS.json').write_text(json.dumps(items,indent=2)+'\n')
    print('V2 boards rendered:',len(items))


if __name__=='__main__':main()
