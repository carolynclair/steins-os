#!/usr/bin/python3
"""Run with dbus-run-session -- /usr/bin/python3 this-file. No desktop is touched."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'prototype/worldline/lib'),
               str(ROOT / 'config/includes.chroot/usr/local/lib/steins')]
import steinslib as sl
import worldline_service as ws
import dbus
from dbus.mainloop.glib import DBusGMainLoop


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {'STEINS_HOME': str(self.home),
                    'STEINS_STATE_DIR': str(self.home / 'state'),
                    'STEINS_ETC_DIR': str(ROOT / 'config/includes.chroot/etc/steins')})
        self.env.start()
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SessionBus(private=True)
        self.service = ws.Service(self.bus)
        self.wallpaper = self.home / 'image.png'
        self.wallpaper.touch()
        result = sl.ApplyResult()
        result.add('fake desktop', True, 'Applied in test')
        self.prepare = patch.object(ws.steinsplasma, 'prepare', return_value=self.wallpaper)
        self.apply = patch.object(ws.steinsplasma, 'apply_prepared', return_value=result)
        self.prepare_mock = self.prepare.start()
        self.apply_mock = self.apply.start()

    def tearDown(self):
        self.service.remove_from_connection()
        self.bus.close()
        self.apply.stop(); self.prepare.stop(); self.env.stop(); self.tmp.cleanup()

    def test_preserves_existing_numeric_state(self):
        sl.set_divergence('2.198306')
        self.assertEqual(json.loads(self.service.GetState())['id'], 'hinamizawa')
        self.assertEqual(list(self.home.joinpath('state').glob('divergence*')), [sl.state_file()])

    def test_prepare_failure_does_not_commit(self):
        sl.set_divergence('1.048596')
        self.prepare_mock.side_effect = RuntimeError('renderer unavailable')
        with self.assertRaises(RuntimeError): self.service.SetDivergence('3.072100')
        self.assertEqual(sl.get_divergence(), '1.048596')
        self.apply_mock.assert_not_called()

    def test_invalid_number_never_reaches_desktop(self):
        with self.assertRaises(ValueError): self.service.SetDivergence('NaN')
        self.prepare_mock.assert_not_called()
        self.assertFalse(sl.state_file().exists())

    def test_partial_failure_is_reported_and_retryable(self):
        failed = sl.ApplyResult(); failed.add('wallpaper', False, 'shell unavailable')
        self.apply_mock.return_value = failed
        result = json.loads(self.service.SetDivergence('3.072100'))
        self.assertFalse(result['applied'])
        self.assertEqual(sl.get_divergence(), '3.072100')
        self.assertFalse(json.loads(self.service.GetState())['applied'])
        with patch.object(ws.steinsplasma, 'apply_pack', return_value=sl.ApplyResult()):
            retry = json.loads(self.service.ApplyCurrent())
        self.assertTrue(retry['applied'])
        self.assertEqual(retry['revision'], result['revision'])

    def test_preferences_do_not_duplicate_divergence(self):
        with patch.object(ws.steinsplasma, 'apply_pack', return_value=sl.ApplyResult()):
            self.service.SetPreference('motion', '"off"')
        saved = json.loads((sl.state_dir() / 'preferences.json').read_text())
        self.assertNotIn('divergence', saved)
        self.assertFalse(saved['meter'])

    def test_rejects_unknown_and_mistyped_preferences(self):
        for key, value in [('meter', '"false"'), ('motion', '"flash"'), ('shell', 'true')]:
            with self.assertRaises(ValueError): self.service.SetPreference(key, value)
        self.assertFalse((sl.state_dir() / 'preferences.json').exists())

    def test_corrupt_preference_shape_uses_safe_defaults(self):
        for text in ('[]', 'null', '"invalid"', '{broken'):
            sl.atomic_write(sl.state_dir() / 'preferences.json', text)
            self.assertEqual(ws.snapshot()['preferences'], ws.DEFAULTS)

    def test_external_legacy_write_is_observed(self):
        with patch.object(ws.steinsplasma, 'apply_pack', return_value=sl.ApplyResult()) as apply:
            self.service.check()
            previous = self.service.last
            sl.set_divergence('2.198306')
            self.service.check()
            self.assertNotEqual(previous, self.service.last)
            self.assertEqual(apply.call_args.args[0].id, 'hinamizawa')

    def test_plasma_dispatch_does_not_start_conky(self):
        with patch.dict(os.environ, {'STEINS_DESKTOP_BACKEND': 'plasma'}), \
                patch.object(ws.steinsplasma, 'apply_pack', return_value=sl.ApplyResult()) as apply, \
                patch.object(sl, '_restart_conky') as conky:
            sl.apply_pack(sl.pick_pack('1.048596'))
            apply.assert_called_once()
            conky.assert_not_called()


if __name__ == '__main__': unittest.main()
