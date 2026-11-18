#!/usr/bin/env python3
"""Generate the proposal's editable token/icon sources. Never touches OS configuration."""
from pathlib import Path
import json
import html
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
ICONS = ROOT / 'icons'
ICONS.mkdir(parents=True, exist_ok=True)
COLORS = {
    'canvas': '#101820', 'panel': '#151f28', 'raised': '#1d2a35',
    'raisedHover': '#293946', 'input': '#0c1319', 'border': '#435767',
    'text': '#eee9df', 'muted': '#a9b6bf', 'subtle': '#90a3af',
    'selection': '#334657', 'accent': '#efad60', 'onAccent': '#101820',
    'success': '#a9cd9a', 'warning': '#efc476', 'error': '#f3978b', 'info': '#8ecada',
}
WORLDS = {
    'alpha': {'name': 'Alpha', 'divergence': '0.571024', 'accent': '#ec887d', 'mood': 'copper dusk / experimental origin'},
    'steins-gate': {'name': 'Steins Gate', 'divergence': '1.048596', 'accent': '#efad60', 'mood': 'amber summer / urban laboratory'},
    'hinamizawa': {'name': 'Hinamizawa', 'divergence': '2.198306', 'accent': '#b8ca81', 'mood': 'moss green / rural summer stillness'},
    'hitogashima': {'name': 'Hitogashima', 'divergence': '3.072100', 'accent': '#72c9dc', 'mood': 'sea glass / luminous coast'},
    'lugunica': {'name': 'Lugunica', 'divergence': '4.250801', 'accent': '#b6a0ec', 'mood': 'violet / atmospheric fantasy stone'},
    'mitakihara': {'name': 'Mitakihara', 'divergence': '5.093001', 'accent': '#e6a7d4', 'mood': 'rose / elegant geometric city'},
}
SHAPES = {
    'launcher': '<path d="M4 7h5l6 10h5M4 17h5l6-10h5"/><circle cx="4" cy="7" r="1.25"/><circle cx="20" cy="17" r="1.25"/>',
    'terminal': '<rect x="3.5" y="4.5" width="17" height="15" rx="3"/><path d="m7.5 9 3.5 3-3.5 3M13.5 15h3"/>',
    'navigator': '<path d="M4 6h5l6 12h5M4 18h5L15 6h5"/><circle cx="4" cy="6" r="1.2"/><circle cx="20" cy="6" r="1.2"/><circle cx="4" cy="18" r="1.2"/><circle cx="20" cy="18" r="1.2"/>',
    'files': '<path d="M3.5 7.5V6a2 2 0 0 1 2-2h4l2 3h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2V7.5Z"/><path d="M4 10h16"/>',
    'dmail': '<rect x="3.5" y="7.5" width="17" height="12.5" rx="2.5"/><path d="m4.5 9 7.5 5 7.5-5M13 4h7m-2-2 2 2-2 2"/>',
    'settings': '<path d="M4 6h6m4 0h6M4 12h2m4 0h10M4 18h10m4 0h2"/><circle cx="12" cy="6" r="2"/><circle cx="8" cy="12" r="2"/><circle cx="16" cy="18" r="2"/>',
    'network': '<path d="M3 8.5a14 14 0 0 1 18 0M6 12a9 9 0 0 1 12 0M9 15.5a4.5 4.5 0 0 1 6 0"/><circle cx="12" cy="19" r=".8" fill="currentColor" stroke="none"/>',
    'volume': '<path d="M3.5 9h4l5-4v14l-5-4h-4Z M16 8a6 6 0 0 1 0 8M18.8 5.5a10 10 0 0 1 0 13"/>',
    'power': '<path d="M7.5 5.5a8.25 8.25 0 1 0 9 0M12 3v8"/>',
    'search': '<circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5 5"/>',
    'close': '<path d="m6 6 12 12M18 6 6 18"/>',
    'minimize': '<path d="M5 16h14"/>',
    'maximize': '<rect x="5" y="5" width="14" height="14" rx="2"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'arrow-right': '<path d="M4 12h15m-5-5 5 5-5 5"/>',
    'lock': '<rect x="5.5" y="10" width="13" height="10.5" rx="2.5"/><path d="M8.5 10V7a3.5 3.5 0 0 1 7 0v3"/><circle cx="12" cy="15.5" r=".8" fill="currentColor" stroke="none"/>',
}


def luminance(color):
    values = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
    return sum(a * b for a, b in zip(linear, (.2126, .7152, .0722)))


def contrast(a, b):
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return (x + .05) / (y + .05)


report = []
for role, fg, bg in [
    ('body on canvas', COLORS['text'], COLORS['canvas']),
    ('body on raised', COLORS['text'], COLORS['raised']),
    ('secondary on raised', COLORS['muted'], COLORS['raised']),
    ('subtle on raised', COLORS['subtle'], COLORS['raised']),
    ('selected text', COLORS['text'], COLORS['selection']),
    ('input text', COLORS['text'], COLORS['input']),
    ('error text on raised', COLORS['error'], COLORS['raised']),
]:
    ratio = contrast(fg, bg)
    assert ratio >= 4.5, (role, ratio)
    report.append({'role': role, 'foreground': fg, 'background': bg, 'ratio': round(ratio, 2), 'target': 4.5})
for world, data in WORLDS.items():
    for role, fg, bg, target in [
        ('accent text / focus on raised', data['accent'], COLORS['raised'], 4.5),
        ('primary button text', COLORS['onAccent'], data['accent'], 4.5),
    ]:
        ratio = contrast(fg, bg)
        assert ratio >= target, (world, role, ratio)
        report.append({'worldline': world, 'role': role, 'foreground': fg, 'background': bg, 'ratio': round(ratio, 2), 'target': target})

tokens = {
    'schema': 'org.steinsos.design-tokens', 'version': '0.1-proposal',
    'status': 'Design proposal. Not installed theme values or a complete desktop API.',
    'units': {'length': 'device-independent pixels at 100% scale', 'time': 'milliseconds',
              'font': 'DIP target sizes; implementations derive from user font/scale settings'},
    'color': COLORS,
    'worldlines': WORLDS,
    'typography': {
        'uiFamily': 'Noto Sans', 'terminalFamily': 'DejaVu Sans Mono', 'tubeFamily': 'preserve existing tube renderer',
        'sizes': {'caption': 12, 'body': 14, 'control': 14, 'section': 18, 'title': 24, 'display': 32, 'terminal': 14, 'panelDigits': 18},
        'weights': {'body': 400, 'label': 500, 'selected': 600}, 'lineHeightRatio': 1.45,
        'tracking': {'body': 0, 'smallLabel': 0.4, 'tubeDigits': 0.8},
        'rules': ['No decorative font for authentication or mail content.', 'No forced uppercase paragraphs.', 'Keep terminal selectable text and glyph fallback.'],
    },
    'space': [4, 8, 12, 16, 24, 32, 48],
    'radius': {'small': 4, 'control': 8, 'window': 12, 'panel': 16, 'tubeCell': 6},
    'stroke': {'icon': 1.75, 'border': 1, 'focus': 2, 'activeIndicator': 2},
    'geometry': {
        'panelHeight': 56, 'panelSideInset': 28, 'panelBottomInset': 20, 'controlTarget': 40, 'compactControlTarget': 36,
        'captionHeight': 42, 'windowControlTarget': 36, 'iconCanvas': 24, 'iconVisibleBounds': [2, 2, 22, 22],
        'compactMeterPreferredWidth': 184, 'compactMeterMinimumWidth': 160, 'compactMeterHeight': 46,
        'launcherPreferredWidth': 430, 'navigatorPreferredWidth': 530, 'navigatorCardWidth': 486,
    },
    'motion': {
        'microFeedback': 100, 'panelReveal': 160, 'windowOpen': 180,
        'proposedShiftFullMaximum': 900, 'proposedShiftReducedMaximum': 180,
        'curves': {'standard': [0.2, 0, 0, 1], 'exit': [0.4, 0, 1, 1]},
        'proposedShiftFullTarget': 800, 'default': 'reduced', 'settings': ['off', 'reduced', 'full'],
        'rules': ['No rapid flashing or full-screen luminance pulses.', 'No input interception during a worldline shift.', 'State/theme recovery does not depend on an effect.'],
    },
    'audio': {'defaultEnabled': False, 'navigationHoverSound': False, 'maximumConcurrentCues': 1,
              'rules': ['System mute and user volume always win.', 'No ambient track by default.', 'A failed shift never plays the success cue.']},
    'accessibility': {
        'normalTextContrastMinimum': 4.5, 'focusContrastMinimum': 3,
        'focus': '2 DIP accent ring with 2 DIP gap; retain visible shape difference from selection',
        'smallControlMaximumDensity': '36 DIP compact pointer target; 40 DIP preferred; touch uses 44 DIP',
        'status': 'label + geometry/icon, never colour alone',
    },
}
(ROOT / 'tokens.json').write_text(json.dumps(tokens, indent=2) + '\n')
(ROOT / 'contrast-report.json').write_text(json.dumps(report, indent=2) + '\n')

svg_attrs = 'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" color="#eee9df" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"'
for name, shape in SHAPES.items():
    icon = f'<svg {svg_attrs}><title>{html.escape(name)}</title>{shape}</svg>\n'
    ET.fromstring(icon)
    (ICONS / (name + '.svg')).write_text(icon)
symbols = ''.join(f'<symbol id="{name}" viewBox="0 0 24 24">{shape}</symbol>' for name, shape in SHAPES.items())
(ROOT / 'icons.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><defs>' + symbols + '</defs></svg>\n')

sheet = ['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="800" viewBox="0 0 1280 800">',
         '<rect width="1280" height="800" fill="#101820"/>',
         '<text x="48" y="56" fill="#efad60" font-family="Noto Sans,sans-serif" font-size="12" letter-spacing="2">WORLDLINE / DESIGN PROPOSAL</text>',
         '<text x="48" y="104" fill="#eee9df" font-family="Noto Sans,sans-serif" font-size="32" font-weight="600">One family. Clear at every scale.</text>',
         '<text x="48" y="136" fill="#a9b6bf" font-family="Noto Sans,sans-serif" font-size="15">Original 24-unit outline system · 1.75-unit stroke · native 16 / 24 / 32 sizes below</text>',
         '<defs>' + symbols + '</defs>']
for index, name in enumerate(SHAPES):
    col, row = index % 8, index // 8
    x, y = 48 + col * 150, 180 + row * 188
    sheet.append(f'<rect x="{x}" y="{y}" width="136" height="168" rx="12" fill="#1d2a35"/>')
    for size, dx in [(16, 16), (24, 50), (32, 92)]:
        sheet.append(f'<use href="#{name}" x="{x+dx}" y="{y+28+(32-size)/2}" width="{size}" height="{size}" fill="none" stroke="currentColor" color="#eee9df" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>')
    sheet.append(f'<text x="{x+16}" y="{y+98}" fill="#eee9df" font-family="Noto Sans,sans-serif" font-size="13">{html.escape(name)}</text>')
    sheet.append(f'<text x="{x+16}" y="{y+126}" fill="#a9b6bf" font-family="DejaVu Sans Mono,monospace" font-size="11">16   24    32</text>')
sheet += [
    '<text x="48" y="624" fill="#eee9df" font-family="Noto Sans,sans-serif" font-size="19" font-weight="600">Shared geometry, worldline accents</text>',
    '<text x="48" y="656" fill="#a9b6bf" font-family="Noto Sans,sans-serif" font-size="14">Monochrome by default. Accent marks active state; labels and indicators carry meaning.</text>',
    '<text x="48" y="756" fill="#90a3af" font-family="Noto Sans,sans-serif" font-size="12">Design coverage: 16 project/system concepts. Third-party trademarks and complete application-theme coverage are not supplied.</text>',
]
for index, data in enumerate(WORLDS.values()):
    x = 48 + index * 198
    sheet.append(f'<circle cx="{x+7}" cy="697" r="6" fill="{data["accent"]}"/><text x="{x+22}" y="702" fill="#eee9df" font-family="Noto Sans,sans-serif" font-size="13">{data["name"]}</text>')
sheet.append('</svg>')
ET.fromstring(''.join(sheet))
(ROOT / 'icon-sheet.svg').write_text(''.join(sheet))
print('Generated tokens, contrast report, 16 original SVG icons and icon-sheet.svg')
print('Minimum specified contrast:', min(x['ratio'] for x in report))
