#!/usr/bin/python3
"""Plasma commands must use one service; failures cannot write independently."""
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
OVERLAY = ROOT / 'config/includes.chroot'
sys.path.insert(0, str(OVERLAY / 'usr/local/lib/steins'))
import steinslib as sl


def command(name):
    loader = importlib.machinery.SourceFileLoader('cli_' + name.replace('-', '_'), str(OVERLAY / 'usr/local/bin' / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class Dispatch(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'STEINS_HOME': self.temp.name,
            'STEINS_STATE_DIR': self.temp.name + '/state', 'STEINS_ETC_DIR': str(OVERLAY / 'etc/steins'),
            'STEINS_DESKTOP_BACKEND': 'plasma', 'STEINS_FAST': '1'})
        self.env.start()
        os.environ.pop('STEINS_NO_APPLY', None)
        self.state = {'interface': 1, 'divergence': '2.198306', 'name': 'Hinamizawa', 'applied': True, 'errors': []}
        self.stdout = patch('sys.stdout', new_callable=io.StringIO); self.stdout.start()
    def tearDown(self):
        self.stdout.stop(); self.env.stop(); self.temp.cleanup()

    def test_cli_set_has_no_independent_write_or_apply(self):
        cli = command('steins-worldline')
        with patch.object(sl, 'session_request', return_value=self.state) as request, \
             patch.object(sl, 'set_divergence') as save, patch.object(sl, 'apply_pack') as apply:
            self.assertEqual(cli.cmd_set(SimpleNamespace(value='2.198306', no_apply=False, dry_run=False)), 0)
        request.assert_called_once_with('SetDivergence', '2.198306')
        save.assert_not_called(); apply.assert_not_called()

    def test_cli_service_failure_preserves_persisted_state(self):
        sl.set_divergence('1.048596')
        cli = command('steins-worldline')
        with patch.object(sl, 'session_request', side_effect=RuntimeError('unavailable')), patch('sys.stderr', io.StringIO()):
            self.assertNotEqual(cli.cmd_set(SimpleNamespace(value='2.198306', no_apply=False, dry_run=False)), 0)
        self.assertEqual(sl.get_divergence(), '1.048596')

    def test_local_dmail_sends_text_to_serialized_service(self):
        cli = command('dmail')
        with patch.object(sl, 'session_request', return_value=self.state) as request, \
             patch.object(sl, 'set_divergence') as save, patch.object(sl, 'apply_pack') as apply, \
             patch.object(sys, 'argv', ['dmail', 'fixture message']):
            self.assertEqual(cli.main(), 0)
        request.assert_called_once_with('ShiftMessage', 'fixture message')
        save.assert_not_called(); apply.assert_not_called()

    def test_ibn_uses_service_for_number_and_message(self):
        cli = command('ibm5100')
        with patch.object(sl, 'session_request', return_value=self.state) as request, \
             patch.object(sl, 'set_divergence') as save, patch.object(sl, 'apply_pack') as apply:
            cli.change('2.198306'); cli.change(message='fixture message')
        self.assertEqual(request.call_args_list[0].args, ('SetDivergence', '2.198306'))
        self.assertEqual(request.call_args_list[1].args, ('ShiftMessage', 'fixture message'))
        save.assert_not_called(); apply.assert_not_called()

    def test_dmail_reports_service_previous_world_after_intervening_shift(self):
        sl.set_divergence('1.048596')
        cli = command('dmail')
        reply = {**self.state, 'previous_divergence': '2.198306', 'divergence': '1.133592', 'name': 'Steins Gate'}
        with patch.object(sl, 'session_request', return_value=reply), patch.object(sys, 'argv', ['dmail', 'race fixture']):
            self.assertEqual(cli.main(), 0)
        self.assertIn('2.198306 -> 1.133592', sys.stdout.getvalue())
        self.assertIn('Hinamizawa -> Steins Gate', sys.stdout.getvalue())
        self.assertNotIn('Worldline unchanged', sys.stdout.getvalue())

    def test_dry_run_stays_without_session_mutation(self):
        cli = command('steins-worldline')
        with patch.object(sl, 'session_request') as request, patch.object(sl, 'apply_pack', return_value=sl.ApplyResult()):
            cli.cmd_set(SimpleNamespace(value='2.198306', no_apply=False, dry_run=True))
        request.assert_not_called()
        self.assertFalse(sl.state_file().exists())

    def test_malformed_reply_fails_without_file_fallback(self):
        interface = SimpleNamespace(SetDivergence=lambda *a, **k: json.dumps({**self.state, 'errors': ['bad shape']}))
        fake = SimpleNamespace(SessionBus=lambda: SimpleNamespace(get_object=lambda *a: object()), Interface=lambda *a: interface)
        with patch.dict(sys.modules, {'dbus': fake}):
            with self.assertRaises(RuntimeError): sl.session_request('SetDivergence', '2.198306')
        self.assertFalse(sl.state_file().exists())


if __name__ == '__main__': unittest.main()
