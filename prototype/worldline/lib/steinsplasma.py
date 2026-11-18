"""Opt-in Plasma adapter. No commands here target a system bus or another user."""
import configparser
import json
import os
from pathlib import Path
import subprocess

import steinslib as sl


def _run(args):
    p = subprocess.run(args, text=True, capture_output=True, timeout=20)
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or '%s exited %s' % (args[0], p.returncode))
    return p.stdout.strip()


def prepare(pack):
    """Generate private assets before changing the authoritative state."""
    home = sl.home_dir()
    scene = Path('/usr/share/backgrounds/steins-prototype') / (pack.id + '.png')
    wallpaper = scene if scene.is_file() else sl._png_for(pack, home, False)
    if wallpaper is None or not wallpaper.is_file():
        raise RuntimeError('Wallpaper preparation failed; divergence was not changed')
    colors = configparser.ConfigParser(interpolation=None)
    colors.optionxform = str
    colors.read('/usr/share/color-schemes/BreezeDark.colors')
    p = pack.palette
    rgb = lambda x: ','.join(str(int(x[i:i+2], 16)) for i in (1, 3, 5))
    for section in ('Window', 'View', 'Button', 'Tooltip', 'Complementary', 'Header'):
        s = 'Colors:' + section
        if not colors.has_section(s):
            colors.add_section(s)
        colors[s].update(BackgroundNormal=rgb(p['bg']), BackgroundAlternate=rgb(p['bg_alt']),
                         ForegroundNormal=rgb(p['fg']), ForegroundInactive=rgb(p['muted']),
                         DecorationFocus=rgb(p['accent']), DecorationHover=rgb(p['accent']))
    colors['Colors:Selection'] = {'BackgroundNormal': rgb(p['selection']),
                                 'ForegroundNormal': '255,255,255',
                                 'BackgroundAlternate': rgb(p['selection'])}
    colors['General'] = {'Name': 'Steins ' + pack.name, 'ColorScheme': 'Steins-' + pack.id}
    colors['WM'] = {'activeBackground': rgb(p['bg']), 'activeForeground': rgb(p['fg']),
                    'inactiveBackground': rgb(p['bg_alt']), 'inactiveForeground': rgb(p['muted'])}
    import io
    stream = io.StringIO()
    colors.write(stream, space_around_delimiters=False)
    sl.atomic_write(home / '.local/share/color-schemes' / ('Steins-' + pack.id + '.colors'), stream.getvalue())
    # Each pack has its own profile: existing user profiles/defaults remain intact.
    terminal = ['[General]', 'Description=Steins ' + pack.name, 'Opacity=1',
                '[Background]', 'Color=' + rgb(p['bg_alt']), '[Foreground]', 'Color=' + rgb(p['fg'])]
    for i, color in enumerate(pack.terminal_palette):
        terminal += ['[Color%d%s]' % (i % 8, 'Intense' if i >= 8 else ''), 'Color=' + rgb(color)]
    target = home / '.local/share/konsole'
    sl.atomic_write(target / ('Steins-' + pack.id + '.colorscheme'), '\n'.join(terminal) + '\n')
    sl.atomic_write(target / ('Steins-' + pack.id + '.profile'),
                    '[Appearance]\nColorScheme=Steins-' + pack.id + '\nFont=DejaVu Sans Mono,11,-1,5,50,0,0,0,0,0\n'
                    '[General]\nName=Steins ' + pack.name + '\nParent=FALLBACK/\nCommand=/bin/bash\n'
                    '[Scrolling]\nHistoryMode=1\nHistorySize=10000\n')
    return wallpaper


def apply_prepared(pack, wallpaper):
    result = sl.ApplyResult()
    def step(name, fn):
        try:
            result.add(name, True, fn() or (name + ' applied'))
        except Exception as e:
            result.add(name, False, str(e))
    def backdrop():
        import dbus
        shell = dbus.Interface(dbus.SessionBus().get_object('org.kde.plasmashell', '/PlasmaShell'),
                               'org.kde.PlasmaShell')
        script = '''var ds=desktops(); for(var i=0;i<ds.length;i++) {
          ds[i].wallpaperPlugin='org.kde.image';
          ds[i].currentConfigGroup=['Wallpaper','org.kde.image','General'];
          ds[i].writeConfig('Image',%s);
        }''' % json.dumps(Path(wallpaper).as_uri())
        answer = str(shell.evaluateScript(script, timeout=20))
        if answer and ('Error' in answer or 'Exception' in answer):
            raise RuntimeError(answer)
    step('Qt palette', lambda: _run(['plasma-apply-colorscheme', 'Steins-' + pack.id]))
    step('wallpaper', backdrop)
    step('GTK selection', lambda: sl._write_gtk_css(pack, sl.home_dir(), False))
    return result


def apply_pack(pack, dry_run=False):
    result = sl.ApplyResult()
    if dry_run:
        result.add('plasma', True, 'Plasma palette, wallpaper, GTK and Konsole profile would be generated')
        return result
    try:
        wallpaper = prepare(pack)
    except Exception as e:
        result.add('prepare', False, str(e))
        return result
    return apply_prepared(pack, wallpaper)
