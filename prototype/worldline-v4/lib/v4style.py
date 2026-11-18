"""Stable V4 chrome. World packs keep their artwork, identity and ANSI colours."""
import json
import os
from pathlib import Path
import re

DEFAULT = {'bg': '#11181e', 'bg_alt': '#151d23', 'fg': '#e6e8e7',
           'selection': '#303b43', 'muted': '#abb6bc', 'accent': '#d9ad72'}
WORLD = {'alpha': '#c39b91', 'steins-gate': '#d9ad72', 'hinamizawa': '#b4bf99',
         'hitogashima': '#92bebc', 'lugunica': '#b5a9cf', 'mitakihara': '#c5a8bb'}
KEYS = {'bg': 'canvas', 'bg_alt': 'panel', 'fg': 'text', 'selection': 'selection',
        'muted': 'muted', 'accent': 'accent'}
HEX = re.compile(r'#[0-9a-fA-F]{6}\Z')


def palette(pack):
    result = {**DEFAULT, 'accent': WORLD.get(pack.id, DEFAULT['accent'])}
    try:
        path = Path(os.environ.get('STEINS_V4_TOKENS', '/usr/share/steins-v4/tokens.json'))
        if path.stat().st_size > 65536:
            return result
        tokens = json.loads(path.read_text())
        if tokens['schema'] != 'org.steinsos.design-tokens':
            return result
        colors = {k: tokens['color'][v] for k, v in KEYS.items()}
        accent = tokens['worldlines'].get(pack.id, {}).get('accent', colors['accent'])
        if not all(isinstance(v, str) and HEX.fullmatch(v) for v in [*colors.values(), accent]):
            return result
        return {**colors, 'accent': accent}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return result


class PaletteView:
    """Supply neutral selection to the maintained GTK writer without mutating packs."""
    def __init__(self, pack):
        self._pack = pack
        self.palette = palette(pack)

    def __getattr__(self, key):
        return getattr(self._pack, key)
