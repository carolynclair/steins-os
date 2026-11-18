#!/usr/bin/python3
"""Token loading and generated Qt/GTK appearance in a temporary home only."""
import configparser
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'prototype/worldline-v4/lib'),
               str(ROOT / 'config/includes.chroot/usr/local/lib/steins')]
import steinslib as sl
import steinsplasma
import v4style


class Style(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.tokens = self.home / 'tokens.json'
        self.tokens.write_bytes((ROOT / 'prototype/identity-v4/TOKENS.json').read_bytes())
        self.env = patch.dict(os.environ, {'STEINS_HOME': str(self.home),
            'STEINS_ETC_DIR': str(ROOT / 'config/includes.chroot/etc/steins'),
            'STEINS_V4_TOKENS': str(self.tokens)})
        self.env.start()
    def tearDown(self):
        self.env.stop(); self.tmp.cleanup()
    def test_neutral_identity_across_six_worlds_without_mutating_pack(self):
        palettes = []
        for pack in sl.load_packs():
            original = dict(pack.palette)
            palettes.append(v4style.palette(pack))
            self.assertEqual(original, pack.palette)
        self.assertEqual(len(palettes), 6)
        for key in ('bg', 'bg_alt', 'fg', 'selection', 'muted'):
            self.assertEqual(len({p[key] for p in palettes}), 1)
        self.assertEqual(len({p['accent'] for p in palettes}), 6)
    def test_missing_malformed_invalid_and_oversized_tokens_have_readable_fallback(self):
        pack = sl.load_packs()[0]
        for content in ('[]', '{', '{"schema":true}', 'x' * 65537):
            self.tokens.write_text(content)
            self.assertEqual(v4style.palette(pack)['selection'], '#303b43')
        self.tokens.unlink()
        self.assertEqual(v4style.palette(pack)['fg'], '#e6e8e7')
    def test_palette_revision_gets_distinct_scheme_id_and_apply_target(self):
        pack = sl.pick_pack('2.198306')
        first = steinsplasma.scheme_name(pack)
        self.assertNotEqual(first, 'Steins-' + pack.id)
        tokens = json.loads(self.tokens.read_text()); tokens['color']['canvas'] = '#12191f'
        self.tokens.write_text(json.dumps(tokens))
        second = steinsplasma.scheme_name(pack)
        self.assertNotEqual(first, second)
        with patch.object(steinsplasma, '_run') as run, patch.dict(sys.modules, {'dbus': Mock()}):
            steinsplasma.apply_prepared(pack, self.home / 'wallpaper.png')
        run.assert_called_once_with(['plasma-apply-colorscheme', second])
    def test_qt_and_gtk_generators_use_same_selection(self):
        pack = sl.pick_pack('2.198306')
        image = self.home / 'wallpaper.png'; image.touch()
        with patch.object(sl, '_png_for', return_value=image):
            steinsplasma.prepare(pack)
        colors = configparser.ConfigParser(); colors.read(self.home / '.local/share/color-schemes' / (steinsplasma.scheme_name(pack) + '.colors'))
        self.assertEqual(colors['Colors:Selection']['BackgroundNormal'], '48,59,67')
        self.assertEqual(colors['WM']['activeBackground'], '17,24,30')
        view = v4style.PaletteView(pack)
        sl._write_gtk_css(view, self.home, False)
        css = (self.home / '.config/gtk-3.0/gtk.css').read_text()
        self.assertIn('#303b43', css)
        self.assertEqual(view.id, pack.id)

if __name__ == '__main__': unittest.main()
