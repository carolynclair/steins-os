#!/usr/bin/env python3
"""Native frame contract + contrast checks for token-derived panel assets."""
from pathlib import Path
import json,re,xml.etree.ElementTree as ET,subprocess,hashlib
HERE=Path(__file__).resolve().parent
T=json.loads((HERE.parent/'identity-v4/TOKENS.json').read_text());C=T['color']
def lum(c):
    s=[int(c[i:i+2],16)/255 for i in (1,3,5)];return sum(v*k for v,k in zip([v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in s],[.2126,.7152,.0722]))
def contrast(a,b):
    a,b=sorted([lum(a),lum(b)]);return (b+.05)/(a+.05)
def ids(p):
    r=ET.parse(p).getroot();i=[e.attrib['id'] for e in r.iter() if 'id' in e.attrib];assert len(i)==len(set(i)),p;return set(i)
parts={'center','top','bottom','left','right','topleft','topright','bottomleft','bottomright'}
panel=HERE/'theme/widgets/panel-background.svg';assert parts<=ids(panel)
assert 'fill-opacity="0.94"' in panel.read_text()
assert 'fill-opacity="1"' in (HERE/'theme/opaque/widgets/panel-background.svg').read_text()
popup_report={}
for variant in ('','opaque/','translucent/'):
    for background,margin in [('dialogs/background.svg',4),('widgets/background.svg',14)]:
        path=HERE/'theme'/variant/background
        assert path.read_bytes()==(HERE/'theme'/background).read_bytes(),'popup opacity differs between theme variants'
        elements=ids(path);assert parts<=elements and {'mask-'+p for p in parts}<=elements
        tree=ET.parse(path).getroot()
        center=next(e for e in tree.iter() if e.attrib.get('id')=='center')
        assert center.attrib['fill']==C['raised'] and center.attrib['fill-opacity']=='1'
        assert float(center.attrib['width'])==28 and float(center.attrib['height'])==28
        for side in ('top','bottom','left','right'):
            hint=next(e for e in tree.iter() if e.attrib.get('id')=='hint-'+side+'-margin')
            assert float(hint.attrib['height' if side in ('top','bottom') else 'width'])==margin
        popup_report[variant+background]={'center_opacity':1,'center_size':[28,28],'content_margin':margin}
frames=ids(HERE/'theme/widgets/tasks.svg')
for direction in ('','north-','west-','east-'):
    for state in ('normal','hover','focus','attention','minimized','progress'):
        assert {direction+state+'-'+p for p in parts}<=frames,(direction,state)
for state in ('normal','hover','pressed','section'):assert {state+'-'+p for p in parts}<=ids(HERE/'theme/widgets/listitem.svg')
for p in (HERE/'theme').rglob('*.svg'):assert 'hint-stretch-borders' in ids(p),p
contrast_report={}
for name,bg in [('text','input'),('muted','input'),('text','selection'),('muted','panel')]:
    value=contrast(C[name],C[bg]);assert value>=4.5,(name,bg,value);contrast_report[name+'/'+bg]=round(value,2)
for name,world in T['worldlines'].items():
    value=contrast(world['accent'],C['input']);assert value>=4.5,(name,value);contrast_report[name+'/digits']=round(value,2)
value=contrast(C['accent'],C['raisedHover']);assert value>=3,value;contrast_report['focus/hover']=round(value,2)
qml=(HERE/'package/contents/ui/DesignTokens.qml').read_text()
assert f'panelHeight: {T["geometry"]["panelHeight"]}' in qml
assert f'meterHeight: {T["geometry"]["compactMeterHeight"]}' in qml
assert 'enabled=false' in (HERE/'theme/plasmarc').read_text()
print(json.dumps({'passed':True,'contract':'native Plasma nine-slice frames, non-blur opaque fallback, shared tokens','contrast':contrast_report,'popup_frames':popup_report},indent=2))
