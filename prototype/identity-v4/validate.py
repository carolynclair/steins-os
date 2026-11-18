#!/usr/bin/env python3
"""Check native Qt icon lookup, small renders, token contrast and package scope."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import xml.etree.ElementTree as ET

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtCore import QRectF, QSize
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QImage, QPainter

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
spec = importlib.util.spec_from_file_location('identity_build', ROOT/'build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
app = QGuiApplication([])
checks = []

def check(name, condition, detail=None):
    checks.append({'check': name, 'pass': bool(condition), 'detail': detail})
    if not condition:
        raise AssertionError(f'{name}: {detail}')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rgba_hash(im):
    data = im.convertToFormat(QImage.Format.Format_RGBA8888)
    return hashlib.sha256(data.constBits()).hexdigest()

def direct_svg(path, size):
    # Direct-file QIcon is the reference control; the theme lookup must resolve
    # to exactly this original asset, independently of the inherited themes.
    return QIcon(str(path)).pixmap(QSize(size,size)).toImage()

def rgb(hexcolor):
    return tuple(int(hexcolor[i:i+2], 16)/255 for i in [1, 3, 5])

def luminance(value):
    channels = rgb(value) if isinstance(value, str) else value
    linear = [x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4 for x in channels]
    return sum(a*b for a,b in zip(linear, [.2126, .7152, .0722]))

def contrast(a, b):
    x, y = sorted([luminance(a), luminance(b)])
    return (y+.05)/(x+.05)

def main():
    token = json.loads((ROOT/'TOKENS.json').read_text())
    check('schema', token['schema'] == 'org.steinsos.design-tokens')
    check('stable geometry', token['geometry']['panelHeight'] == 46 and token['geometry']['iconCanvas'] == 24)
    check('six restrained world accents', len(token['worldlines']) == 6 and all(set(w) == {'name', 'accent'} for w in token['worldlines'].values()))
    color = token['color']
    foregrounds = {name: color[name] for name in ['text', 'muted', 'subtle', 'icon']}
    foregrounds.update({name: w['accent'] for name,w in token['worldlines'].items()})
    backgrounds = {name: color[name] for name in ['canvas', 'panel', 'raised', 'raisedHover', 'input', 'selection']}
    alpha = token['opacity']['panel']
    backgrounds['panel on white wallpaper'] = tuple(x*alpha+1-alpha for x in rgb(color['panel']))
    ratios = {f'{fg} / {bg}': round(contrast(fv,bv), 3) for fg,fv in foregrounds.items() for bg,bv in backgrounds.items()}
    check('all normal text and semantic icon contrast >= 4.5', min(ratios.values()) >= 4.5, {'minimum': min(ratios.values()), 'ratios': ratios})
    check('white selection text >= 4.5', contrast('#ffffff',color['selection']) >= 4.5, round(contrast('#ffffff',color['selection']),3))
    check('dark text on world accent >= 4.5', all(contrast(color['onAccent'],w['accent']) >= 4.5 for w in token['worldlines'].values()))

    small = []
    for name in build.ICONS:
        svg = ROOT/'icons'/f'{name}.svg'
        el = ET.parse(svg).getroot()
        check('SVG '+name, el.get('viewBox') == '0 0 24 24' and el.get('stroke-width') == '1.75')
        for size in [16,24,32]:
            image = QImage(str(ROOT/'evidence/sizes'/f'{name}-{size}.png'))
            points = [(x,y) for y in range(size) for x in range(size) if image.pixelColor(x,y).alpha() >= 64]
            check(f'visible bounded {name} {size}', bool(points) and image.width() == size and image.height() == size)
            bounds = [min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)]
            check(f'clear canvas edges {name} {size}', bounds[0] > 0 and bounds[1] > 0 and bounds[2] < size-1 and bounds[3] < size-1, bounds)
            small.append({'icon': name, 'size': size, 'alpha64_bounds': bounds})

    original = PROJECT/'config/includes.chroot/usr/share/icons/hicolor/scalable/apps/steins-os.svg'
    check('existing emblem unchanged', digest(original) == digest(ROOT/'theme/SteinsLab/scalable/apps/steins-os.svg'),digest(original))
    for context,aliases in build.ALIASES.items():
        for alias,source in aliases.items():
            path = ROOT/'theme/SteinsLab/scalable'/context/(alias+'.svg')
            check('alias bytes '+alias, digest(path) == digest(ROOT/'icons'/(source+'.svg')))

    # QIcon resolves aliases through a real icon theme index, not a direct path.
    QIcon.setThemeSearchPaths([str(ROOT/'theme'), '/usr/share/icons'])
    QIcon.setFallbackThemeName('breeze')
    QIcon.setThemeName('SteinsLab')
    lookup = []
    for context,aliases in build.ALIASES.items():
        for alias,source in aliases.items():
            check('Qt has alias '+alias, QIcon.hasThemeIcon(alias))
            for size in [16,24,32]:
                resolved = QIcon.fromTheme(alias).pixmap(QSize(size,size)).toImage()
                expected = direct_svg(ROOT/'icons'/(source+'.svg'),size)
                check(f'Qt exact source {alias} {size}', not resolved.isNull() and rgba_hash(resolved) == rgba_hash(expected))
                lookup.append({'name':alias,'size':size,'source':source,'sha256_rgba':rgba_hash(resolved)})
    # Check inherited standard symbols remain available for apps outside this set.
    fallback_names = ['document-save', 'edit-copy', 'dialog-information']
    for name in fallback_names:
        inherited = QIcon.fromTheme(name).pixmap(24).toImage()
        QIcon.setThemeName('breeze-dark')
        upstream = QIcon.fromTheme(name).pixmap(24).toImage()
        QIcon.setThemeName('SteinsLab')
        check('Qt inherited Breeze Dark fallback '+name, not inherited.isNull() and rgba_hash(inherited) == rgba_hash(upstream))

    # Produce a contact sheet from actual QIcon lookups using the real Qt renderer.
    names = ['steins-launcher','utilities-terminal','system-file-manager','steins-dmail','steins-navigator-v4','preferences-system','system-shutdown','system-reboot','system-log-out','audio-volume-high','audio-volume-medium','audio-volume-low','audio-volume-muted']
    sheet = QImage(900, 92+len(names)*64, QImage.Format.Format_ARGB32_Premultiplied)
    sheet.fill(QColor(color['canvas']))
    painter = QPainter(sheet)
    painter.setPen(QColor(color['text']))
    font = painter.font();font.setPixelSize(20);painter.setFont(font)
    painter.drawText(24,34,'SteinsLab: actual Qt icon-theme resolution')
    font.setPixelSize(12);painter.setFont(font)
    painter.setPen(QColor(color['muted']))
    painter.drawText(24,58,'Offscreen QGuiApplication / QIcon.fromTheme / native 16, 24, 32 px; no host theme changes')
    for row,name in enumerate(names):
        y=86+row*64
        painter.setPen(QColor(color['text']));painter.drawText(24,y+24,name)
        for i,size in enumerate([16,24,32]):
            x=400+i*130
            painter.drawPixmap(x,y,QIcon.fromTheme(name).pixmap(size))
            painter.setPen(QColor(color['muted']));painter.drawText(x+46,y+19,str(size)+' px')
    painter.end()
    check('Qt preview saved',sheet.save(str(ROOT/'evidence/qt-theme-preview.png')))

    package = PROJECT/json.loads((PROJECT/'dist/v4/identity/BUILD.json').read_text())['package']
    data = subprocess.check_output(['dpkg-deb','--fsys-tarfile',str(package)])
    archive = tarfile.open(fileobj=io.BytesIO(data))
    members = archive.getmembers()
    files = [m.name.removeprefix('./') for m in members if m.isfile()]
    allowed = ['usr/share/icons/SteinsLab/', 'usr/share/steins-v4/tokens.json', 'usr/share/doc/steins-identity-v4/']
    check('package only identity share files',all(any(name.startswith(prefix) for prefix in allowed) for name in files),files)
    packaged_tokens = archive.extractfile('./usr/share/steins-v4/tokens.json').read()
    check('packaged tokens equal current source',packaged_tokens == (ROOT/'TOKENS.json').read_bytes())
    control_data = subprocess.check_output(['dpkg-deb','--ctrl-tarfile',str(package)])
    control_files = [m.name.removeprefix('./') for m in tarfile.open(fileobj=io.BytesIO(control_data)).getmembers() if m.isfile()]
    check('package does not ship maintainer scripts',control_files == ['control'],control_files)
    check('package metadata name',subprocess.check_output(['dpkg-deb','-f',str(package),'Package']).decode().strip() == 'steins-identity-v4')
    result = {'status':'PASS','checks':len(checks),'canonical_icons':len(build.ICONS),'small_renders':len(small),'qt_exact_alias_renders':len(lookup),'qt_version':__import__('PySide6.QtCore',fromlist=['qVersion']).qVersion(),'package_sha256':digest(package),'package':str(package),'small_bounds':small,'qt_lookup':lookup,'assertions':checks,'scope':'Offscreen native Qt icon lookup and asset/package checks; actual Plasma interaction and desktop screenshots are a separate guest test.'}
    (ROOT/'evidence/VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['small_bounds','qt_lookup','assertions']},indent=2))

if __name__ == '__main__':
    main()
