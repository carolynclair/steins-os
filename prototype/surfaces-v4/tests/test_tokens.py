#!/usr/bin/python3
"""Defensive adapter and cross-surface contract checks; no desktop writes."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
ROOT = SOURCE.parents[1]
sys.path.insert(0, str(SOURCE / 'share'))
from surface_tokens import load_tokens, DEFAULTS


class TokenContracts(unittest.TestCase):
    def test_shared_contract_is_used_without_colour_drift(self):
        contract = json.loads((ROOT / 'prototype/identity-v4/TOKENS.json').read_text())
        tokens = load_tokens(ROOT / 'prototype/identity-v4/TOKENS.json')
        self.assertEqual(tokens['color'], {k: contract['color'][k] for k in DEFAULTS['color']})
        self.assertEqual(tokens['worldlines'], {k: {'accent': v['accent']} for k, v in contract['worldlines'].items()})
        source = (SOURCE / 'terminal/src/main.cpp').read_text()
        for entry in tokens['color'].values():
            # The terminal need not expose error/hover colours it does not draw.
            if entry not in ('#ddaaa1', '#27343e'):
                self.assertIn(entry, source)
        for entry in tokens['worldlines'].values():
            self.assertIn(entry['accent'], source)

    def test_missing_malformed_and_oversized_contract_fall_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'tokens.json'
            self.assertEqual(load_tokens(p), DEFAULTS)
            for value in ('{', 'null', '[]', 'x' * (256 * 1024 + 1)):
                p.write_text(value)
                self.assertEqual(load_tokens(p), DEFAULTS)

    def test_invalid_fields_cannot_erase_known_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'tokens.json'
            p.write_text(json.dumps({'color': {'panel': 'transparent', 'text': '#AABBCC'},
                                     'radius': {'control': 9000},
                                     'typography': {'uiFamily': 'bad\nfont'},
                                     'worldlines': {'hitogashima': {'accent': '#00000000'}}}))
            obj = load_tokens(p)
            self.assertEqual(obj['color']['panel'], DEFAULTS['color']['panel'])
            self.assertEqual(obj['color']['text'], '#aabbcc')
            self.assertEqual(obj['radius']['control'], 6)
            self.assertEqual(obj['typography']['uiFamily'], 'Noto Sans')
            self.assertEqual(obj['worldlines']['hitogashima']['accent'], '#92bebc')

    def test_contract_load_does_not_mutate_fallback(self):
        old = json.dumps(DEFAULTS, sort_keys=True)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'tokens.json'
            p.write_text('{"color":{"text":"#123456"}}')
            self.assertEqual(load_tokens(p)['color']['text'], '#123456')
        self.assertEqual(json.dumps(DEFAULTS, sort_keys=True), old)


if __name__ == '__main__':
    unittest.main()
