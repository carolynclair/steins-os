"""Small read-only adapter for the packaged V4 design contract (MIT)."""
import json
import re
from pathlib import Path

DEFAULTS = {
    'color': {'canvas': '#11181e', 'panel': '#151d23', 'raised': '#1d272f',
              'raisedHover': '#27343e', 'input': '#0e151b', 'border': '#3c4b55',
              'text': '#e6e8e7', 'muted': '#abb6bc', 'selection': '#303b43',
              'accent': '#d9ad72', 'error': '#ddaaa1'},
    'radius': {'small': 4, 'control': 6, 'window': 10},
    'typography': {'uiFamily': 'Noto Sans', 'terminalFamily': 'DejaVu Sans Mono',
                   'sizes': {'caption': 11, 'body': 14, 'control': 14, 'title': 23}},
    'worldlines': {key: {'accent': color} for key, color in {
        'alpha': '#c39b91', 'steins-gate': '#d9ad72', 'hinamizawa': '#b4bf99',
        'hitogashima': '#92bebc', 'lugunica': '#b5a9cf', 'mitakihara': '#c5a8bb'}.items()}}


def load_tokens(path=Path('/usr/share/steins-v4/tokens.json')):
    """Keep known defaults for malformed/missing fields; ignore unrelated keys."""
    fallback = json.loads(json.dumps(DEFAULTS))
    try:
        if path.stat().st_size > 256 * 1024:
            return fallback
        source = json.loads(path.read_text())
    except (OSError, ValueError, TypeError):
        return fallback
    def merge(target, supplied):
        if not isinstance(supplied, dict):
            return
        for key, old in target.items():
            value = supplied.get(key)
            if isinstance(old, dict):
                merge(old, value)
            elif isinstance(old, int):
                if type(value) is int and 2 <= value <= 40:
                    target[key] = value
            elif old.startswith('#'):
                if isinstance(value, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', value):
                    target[key] = value.lower()
            elif isinstance(value, str) and 0 < len(value) <= 80 and '\n' not in value:
                target[key] = value
    merge(fallback, source)
    return fallback
