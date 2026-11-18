#!/usr/bin/env python3
"""Original logo proposals; never changes the existing distribution emblem."""
import base64
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
CURRENT = PROJECT / 'config/includes.chroot/usr/share/icons/hicolor/scalable/apps/steins-os.svg'
INK = '#eee9df'
AMBER = '#efad60'
BG = '#101820'
PANEL = '#151f28'
MUTED = '#a9b6bf'

# Hand-authored geometry, unrelated to the supplied reference's circle/hex arrangement.
MARKS = {
    'divergence-gate': {
        'name': 'A / Divergence Gate',
        'kind': 'Minimal worldline mark',
        'rationale': ['Two routes converge into a shared future.', 'Compact, directional and deliberately open.'],
        'body': '<path d="M4 5h5l5 7h6M4 19h5l5-7"/>',
    },
    'phase-crossing': {
        'name': 'B / Phase Crossing',
        'kind': 'Abstract temporal intersection',
        'rationale': ['Two signal paths exchange positions.', 'A small, stable instrument-like silhouette.'],
        'body': '<path d="M4 6h5l6 12h5M4 18h5l6-12h5"/>',
    },
    'instrument-s': {
        'name': 'C / Instrument S',
        'kind': 'Steins monogram study',
        'rationale': ['A stepped S with sparse calibration corners.', 'More typographic; still readable in one colour.'],
        'body': '<path d="M18 6H8L6 8v2l2 2h8l2 2v2l-2 2H6"/><path d="M3 7V3h4M17 21h4v-4" stroke-width="1.6"/>',
    },
}


def svg(body, view='0 0 24 24'):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="'+view+'" '
            'fill="none" stroke="currentColor" color="'+INK+'" stroke-width="2.2" '
            'stroke-linecap="round" stroke-linejoin="round">'+body+'</svg>')


def render(source, target, width=None, height=None):
    args = ['docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',str(ROOT)+':/identity','-w','/identity','steins-os-builder:trixie',
            'rsvg-convert',source.name,'-o',str(target.relative_to(ROOT))]
    if width: args += ['-w',str(width)]
    if height: args += ['-h',str(height)]
    subprocess.run(args, check=True)


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    (ROOT/'sizes').mkdir(exist_ok=True)
    shutil.copyfile(CURRENT, ROOT/'current.svg')
    # Separate display study: the actual existing asset is copied unchanged above.
    current_mono = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" '
        'fill="none" stroke="currentColor" color="'+INK+'" stroke-width="5" '
        'stroke-linejoin="round"><path d="M30 30h68L30 98h68M48 30v20m32 28v20"/>'
        '<circle cx="64" cy="64" r="50" stroke-width="2"/></svg>')
    (ROOT/'current-monochrome.svg').write_text(current_mono)
    for pid, data in MARKS.items():
        (ROOT/(pid+'.svg')).write_text(svg('<title>'+escape(data['name'])+'</title>'+data['body']))
    ids=['current']+list(MARKS)
    for pid in ids:
        source=ROOT/('current-monochrome.svg' if pid=='current' else pid+'.svg')
        for size in (16,24,32):render(source,ROOT/'sizes'/f'{pid}-{size}.png',size,size)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1920" height="1420" viewBox="0 0 1920 1420">']
    def rect(x,y,w,h,fill,rx=0,stroke=None):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')
    def text(x,y,value,size=14,color=INK,weight=400,anchor='start'):
        parts.append(f'<text x="{x}" y="{y}" font-family="Noto Sans" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(value)}</text>')
    def mark(pid,x,y,size,color=INK,actual=False):
        if pid=='current' and actual:
            source=(ROOT/'current.svg').read_text()
            body=re.sub(r'^.*?<svg\b[^>]*>','',source,flags=re.S).rsplit('</svg>',1)[0]
            parts.append(f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 128 128">{body}</svg>')
        elif pid=='current':
            parts.append(f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 128 128" fill="none" stroke="{color}" stroke-width="5" stroke-linejoin="round"><path d="M30 30h68L30 98h68M48 30v20m32 28v20"/><circle cx="64" cy="64" r="50" stroke-width="2"/></svg>')
        else:
            parts.append(f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{MARKS[pid]["body"]}</svg>')
    rect(0,0,1920,1420,BG)
    text(40,57,'Steins;OS / identity alternatives',32,INK,600)
    text(40,91,'Original vector studies · current emblem retained · no candidate selected or installed',16,MUTED)
    for col,pid in enumerate(ids):
        x=40+col*466;mid=x+221
        rect(x,128,442,1184,PANEL,16,'#435767')
        title='Current / retained' if pid=='current' else MARKS[pid]['name']
        subtitle='Existing circular emblem' if pid=='current' else MARKS[pid]['kind']
        text(x+22,171,title,23,INK,600)
        text(x+22,202,subtitle,14,MUTED)
        rect(x+22,234,398,292,'#0b1117',12)
        mark(pid,mid-70,263,140,AMBER,actual=True)
        text(mid,446,'Steins;OS',22,INK,500,'middle')
        text(mid,479,'Large boot-emblem study',12,MUTED,anchor='middle')
        text(x+22,565,'PANEL / ACTUAL PIXEL SIZES',11,MUTED,600)
        for n,size in enumerate((16,24,32)):
            bx=x+36+n*84
            rect(bx-10,591,56,56,BG,8)
            raw=(ROOT/'sizes'/f'{pid}-{size}.png').read_bytes()
            data=base64.b64encode(raw).decode()
            parts.append(f'<image x="{bx+(36-size)/2}" y="{619-size/2}" width="{size}" height="{size}" xlink:href="data:image/png;base64,{data}"/>')
            text(bx+18,674,str(size)+' px',12,MUTED,anchor='middle')
        raw=(ROOT/'sizes'/f'{pid}-16.png').read_bytes();data=base64.b64encode(raw).decode()
        parts.append(f'<image x="{x+320}" y="591" width="96" height="96" xlink:href="data:image/png;base64,{data}" style="image-rendering:pixelated"/>')
        text(x+368,712,'16 px enlarged',10,MUTED,anchor='middle')
        text(x+22,755,'MONOCHROME / LIGHT SURFACE',11,MUTED,600)
        rect(x+22,776,398,132,INK,10)
        mark(pid,x+63,814,56,BG)
        mark(pid,x+178,826,32,BG)
        mark(pid,x+283,834,16,BG)
        text(x+22,953,'LOGIN / COMPACT IDENTITY STUDY',11,MUTED,600)
        rect(x+22,974,398,169,BG,10,'#435767')
        mark(pid,x+45,998,40,INK,actual=False)
        text(x+104,1018,'Welcome back',18,INK,600)
        text(x+104,1043,'Observer',13,MUTED)
        rect(x+43,1070,356,40,'#1d2a35',7,'#435767')
        text(x+59,1095,'Password',13,MUTED)
        lines=['Existing full asset stays unchanged.', 'Thin circular detail is less robust at 16 px.'] if pid=='current' else MARKS[pid]['rationale']
        for i,line in enumerate(lines):text(x+22,1190+i*28,line,14,MUTED)
    text(40,1361,'DESIGN PROPOSAL · inspired by instrument/route geometry; reference artwork was not traced or reused',14,MUTED)
    text(40,1391,'All alternatives need Chairman approval before replacing the current symbol. Raster exports verify visible ink and bounds; recognition needs owner review.',12,MUTED)
    sheet=ROOT/'comparison-sheet.svg';sheet.write_text('\n'.join(parts+['</svg>']))
    render(sheet,ROOT/'comparison-sheet.png')
    for path in ROOT.glob('*.svg'):ET.parse(path)
    assert (ROOT/'current.svg').read_bytes()==CURRENT.read_bytes()
    manifest={
        'status':'Original design concepts; no mark selected or installed',
        'preserved_current_sha256':hashlib.sha256(CURRENT.read_bytes()).hexdigest(),
        'current_exact_copy':True,
        'candidate_ids':list(MARKS),
        'rendered_sizes':[16,24,32],
        'svg_xml_valid':True,
        'source':'Hand-authored SVG path geometry using standard Python, rendered with existing librsvg builder',
        'references':'User-supplied visual inspiration inspected; no screenshot/logo art copied or traced',
        'files':[{'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(ROOT.rglob('*')) if p.is_file() and p.suffix in ('.svg','.png')]
    }
    (ROOT/'VALIDATION.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(ROOT/'comparison-sheet.png')


if __name__=='__main__':main()
