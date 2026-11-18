#!/usr/bin/env python3
"""Original editable boot-concept storyboard. Does not install a Plymouth theme."""
from html import escape
from pathlib import Path
import hashlib
import json
import os
import re
import struct
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
CURRENT=PROJECT/'config/includes.chroot/usr/share/icons/hicolor/scalable/apps/steins-os.svg'
source=CURRENT.read_text()
mark=re.search(r'(<g\b.*</g>)',source,re.S).group(1)
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">',
       '<rect width="1920" height="1080" fill="#101820"/>']
def add(s):parts.append(s)
def text(x,y,value,size=16,color='#eee9df',weight=400,anchor='start',mono=False):
    add(f'<text x="{x}" y="{y}" fill="{color}" font-family="'+('DejaVu Sans Mono' if mono else 'Noto Sans')+f'" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')
def rect(x,y,w,h,fill='#151f28',rx=10,stroke='#435767'):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>')
def emblem(x,y,size=106,opacity=1,partial=False):
    add(f'<g opacity="{opacity}"><svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 128 128">')
    if partial:
        add('<defs><clipPath id="assembly-mask"><path d="M0 0H128V51H71V128H0Z"/></clipPath></defs><g clip-path="url(#assembly-mask)">')
    add(mark)
    if partial:add('</g>')
    add('</svg></g>')

text(44,62,'Startup / signal to session',34,weight=600)
text(44,99,'Existing emblem retained · original motion study · silent default · real readiness wins over the timeline',16,'#a9b6bf')
phases=[('01','Signal','0–120 ms',['Low-contrast trace emergence.','No full-screen flashes.']),
        ('02','Assemble','120–480 ms',['Light resolves into the current mark.','No logo replacement.']),
        ('03','Calibrate','480–720 ms',['Brief public theme digits.','Never personal pre-login state.']),
        ('04','Settle','720–940 ms',['The mark stabilises.','Temporary traces recede.']),
        ('05','Handoff','940–1,100 ms',['Continue only when login is ready.','Do not delay authentication.']),
        ('06','Authenticate','Readiness-driven',['Greeter controls stay practical.','Cue belongs after login, if enabled.'])]
for i,(n,title,timing,lines) in enumerate(phases):
    x=44+i*307;y=152;w=288
    rect(x,y,w,252,'#0b1218',12)
    if i==0:
        for k in range(5):
            yy=y+72+k*22
            add(f'<path d="M{x+28} {yy}H{x+112+k*11}l14 -12h40" fill="none" stroke="#efad60" stroke-width="1.5" opacity="{.12+k*.06}"/>')
    elif i==1:
        emblem(x+90,y+52,108,.85,True)
        add(f'<path d="M{x+22} {y+152}h74m98 -62h70" stroke="#efad60" stroke-width="1.5" opacity=".45"/>')
    elif i in (2,3):
        emblem(x+89,y+40,110)
        if i==2:
            text(x+144,y+203,'1.048596',24,'#efad60',anchor='middle',mono=True)
            text(x+144,y+228,'THEME CALIBRATION',9,'#a9b6bf',anchor='middle')
        else:
            text(x+144,y+193,'Steins;OS',24,weight=500,anchor='middle')
    elif i==4:
        emblem(x+107,y+43,74)
        text(x+144,y+162,'Steins;OS',24,weight=500,anchor='middle')
        text(x+144,y+198,'Preparing the login screen',12,'#a9b6bf',anchor='middle')
    else:
        rect(x+40,y+27,208,196,'#151f28',10)
        emblem(x+122,y+40,44)
        text(x+144,y+110,'Welcome back',18,weight=600,anchor='middle')
        text(x+59,y+137,'Password',11,'#a9b6bf')
        rect(x+58,y+146,172,29,'#0c1319',5,'#efad60')
        rect(x+58,y+184,172,26,'#efad60',5,'#efad60')
        text(x+144,y+202,'Sign in',12,'#101820',600,anchor='middle')
    text(x,y+290,n+' / '+title,21,weight=600)
    text(x,y+322,timing,14,'#efad60',mono=True)
    for j,line in enumerate(lines):text(x,y+356+j*24,line,13,'#a9b6bf')

add('<path d="M44 622H1876" stroke="#435767"/>')
rows=[('FULL','≤1,200 ms preview','One assembly; no mandatory waiting.','Native port remains unimplemented.'),
      ('REDUCED','150 ms or static','No trace travel, scanning or digit roll.','Authentication remains usable.'),
      ('OFF / SILENT','Immediate when ready','Static mark and real status messages.','No audio prerequisite for startup.')]
for i,(name,duration,line1,line2) in enumerate(rows):
    x=44+i*620;rect(x,661,594,164)
    text(x+22,697,name,12,'#efad60',600)
    text(x+22,735,duration,25,weight=600)
    text(x+22,772,line1,14,'#a9b6bf');text(x+22,799,line2,14,'#a9b6bf')
text(44,886,'Integration boundaries',23,weight=600)
text(44,923,'Plymouth: early boot/status/passwords  →  SDDM: authentication  →  user session: worldline state and optional readiness cue',15,'#a9b6bf')
text(44,961,'No initramfs audio service. No user-home or session-bus reads before authentication. No screenshot-matched success claim.',15,'#a9b6bf')
add('<rect x="0" y="1014" width="1920" height="66" fill="#0b1218"/>')
text(44,1043,'DESIGN PREVIEW / NOT A PLYMOUTH CAPTURE',14,weight=600)
text(44,1066,'V2 startup direction · current emblem unchanged · cinematic timing is a proposal, not measured boot performance',12,'#a9b6bf')
add('</svg>')
p=ROOT/'boot-storyboard.svg';p.write_text('\n'.join(parts)+'\n');ET.parse(p)
subprocess.run(['docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}',
                '-v',str(ROOT)+':/work','-w','/work','steins-os-builder:trixie',
                'rsvg-convert','boot-storyboard.svg','-o','boot-storyboard.png'],check=True)
raw=(ROOT/'boot-storyboard.png').read_bytes()
assert struct.unpack('>II',raw[16:24])==(1920,1080)
report={'svg_xml_valid':True,'png_dimensions':[1920,1080],
        'current_emblem_source':str(CURRENT.relative_to(PROJECT)),
        'current_emblem_sha256':hashlib.sha256(CURRENT.read_bytes()).hexdigest(),
        'runtime_theme_modified':False,'audio_played':False,'integration_tested':False}
(ROOT/'STORYBOARD-VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(p)
