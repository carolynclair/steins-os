#!/usr/bin/python3
"""Run with dbus-run-session -- /usr/bin/python3 this-file. No desktop is touched."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'prototype/worldline/lib'),
               str(ROOT / 'config/includes.chroot/usr/local/lib/steins')]
import steinslib as sl
import worldline_service as ws
import dbus
from dbus.mainloop.glib import DBusGMainLoop


class Timers:
    """Deterministic timer dispatch: no real sleeps or desktop loop are needed."""
    def __init__(self):
        self.next_id = 0
        self.sources = {}
    def add(self, delay, callback, *args):
        self.next_id += 1
        self.sources[self.next_id] = (delay, callback, args)
        return self.next_id
    def remove(self, source):
        return self.sources.pop(source, None) is not None
    def fire(self, source):
        delay, callback, args = self.sources.pop(source)
        return callback(*args)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {'STEINS_HOME': str(self.home),
                    'STEINS_STATE_DIR': str(self.home / 'state'),
                    'STEINS_ETC_DIR': str(ROOT / 'config/includes.chroot/etc/steins')})
        self.env.start()
        self.timers = Timers()
        self.timer_patches = [
            patch.object(ws.GLib, 'timeout_add_seconds', side_effect=self.timers.add),
            patch.object(ws.GLib, 'idle_add', side_effect=lambda fn: self.timers.add(0, fn)),
            patch.object(ws.GLib, 'source_remove', side_effect=self.timers.remove),
        ]
        for p in self.timer_patches: p.start()
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
        self.service._cancel_retry()
        self.service.remove_from_connection()
        # Release both Object/Service references while the private bus is open.
        # Fake timer call histories can otherwise keep the name alive past close().
        self.service.name = None
        self.service._name = None
        self.bus.close()
        self.apply.stop(); self.prepare.stop(); self.env.stop(); self.tmp.cleanup()
        for p in reversed(self.timer_patches): p.stop()

    def transient(self, name='ServiceUnknown'):
        result = sl.ApplyResult()
        result.add('wallpaper', False, 'org.freedesktop.DBus.Error.' + name + ': plasmashell not ready')
        return result

    def test_startup_dependency_recovers_without_rewriting_divergence(self):
        sl.set_divergence('3.072100')
        with patch.object(ws.steinsplasma, 'apply_pack', side_effect=[self.transient(), sl.ApplyResult()]) as apply, \
                patch.object(sl, 'set_divergence', wraps=sl.set_divergence) as save:
            self.service.check()
            revision = self.service.last
            self.assertFalse(json.loads(self.service.GetState())['applied'])
            source = self.service._retry_source
            self.assertEqual(self.timers.sources[source][0], 1)
            self.timers.fire(source)
            self.assertTrue(json.loads(self.service.GetState())['applied'])
            self.assertEqual(self.service.last, revision)
            self.assertEqual(sl.get_divergence(), '3.072100')
            self.assertEqual(apply.call_count, 2)
            save.assert_not_called()
            self.assertIsNone(self.service._retry_source)

    def test_retry_budget_is_bounded_and_checks_do_not_restart_it(self):
        with patch.object(ws.steinsplasma, 'apply_pack', return_value=self.transient()) as apply:
            self.service.check()
            for delay in (1, 2, 4, 8, 16):
                source = self.service._retry_source
                self.assertEqual(self.timers.sources[source][0], delay)
                self.timers.fire(source)
            self.assertIsNone(self.service._retry_source)
            self.assertFalse(json.loads(self.service.GetState())['applied'])
            self.service.check(); self.service.check()
            self.assertEqual(apply.call_count, 6)  # Initial attempt plus five retries.

    def test_new_revision_invalidates_queued_retry(self):
        sl.set_divergence('1.048596')
        with patch.object(ws.steinsplasma, 'apply_pack', side_effect=[self.transient(), sl.ApplyResult()]) as apply:
            self.service.check()
            source = self.service._retry_source
            queued = self.timers.sources[source][1]
            sl.set_divergence('2.198306')
            self.service.check()
            self.assertNotIn(source, self.timers.sources)
            queued()  # Simulate a callback already queued when source_remove ran.
            self.assertEqual(apply.call_count, 2)
            self.assertEqual(json.loads(self.service.GetState())['id'], 'hinamizawa')
            self.assertTrue(json.loads(self.service.GetState())['applied'])

    def test_pending_retry_applies_latest_external_state_not_old_destination(self):
        sl.set_divergence('1.048596')
        with patch.object(ws.steinsplasma, 'apply_pack', side_effect=[self.transient(), sl.ApplyResult()]) as apply:
            self.service.check()
            source = self.service._retry_source
            sl.set_divergence('3.072100')
            self.timers.fire(source)
            self.assertEqual(apply.call_args.args[0].id, 'hitogashima')
            self.assertEqual(json.loads(self.service.GetState())['id'], 'hitogashima')

    def test_manual_success_cancels_pending_retry_and_stale_callback(self):
        with patch.object(ws.steinsplasma, 'apply_pack', side_effect=[self.transient(), sl.ApplyResult()]) as apply:
            self.service.check()
            source = self.service._retry_source
            queued = self.timers.sources[source][1]
            self.service.ApplyCurrent()
            self.assertNotIn(source, self.timers.sources)
            queued()
            self.assertEqual(apply.call_count, 2)
            self.assertIsNone(self.service._retry_source)

    def test_manual_transient_failure_keeps_only_one_pending_timer(self):
        with patch.object(ws.steinsplasma, 'apply_pack', return_value=self.transient()):
            self.service.check()
            source = self.service._retry_source
            for _ in range(3): self.service.ApplyCurrent()
            self.assertEqual(self.service._retry_source, source)
            self.assertEqual(self.service._retry_attempt, 1)

    def test_permanent_or_mixed_errors_do_not_schedule_retries(self):
        for step, message in [('GTK selection', 'Permission denied'),
                              ('wallpaper', 'Invalid image'), ('prepare', 'Renderer unavailable')]:
            failure = sl.ApplyResult(); failure.add(step, False, message)
            with patch.object(ws.steinsplasma, 'apply_pack', return_value=failure):
                self.service.ApplyCurrent()
            self.assertIsNone(self.service._retry_source)
        mixed = self.transient(); mixed.add('GTK selection', False, 'Permission denied')
        with patch.object(ws.steinsplasma, 'apply_pack', return_value=mixed):
            self.service.ApplyCurrent()
        self.assertIsNone(self.service._retry_source)

    def test_supported_transient_names_and_new_revision_budget(self):
        for name in ('ServiceUnknown', 'NameHasNoOwner', 'NoReply'):
            with patch.object(ws.steinsplasma, 'apply_pack', return_value=self.transient(name)):
                self.service.ApplyCurrent()
            self.assertIsNotNone(self.service._retry_source)
            self.service._cancel_retry()
        with patch.object(ws.steinsplasma, 'apply_pack', return_value=self.transient()):
            self.service.ApplyCurrent()
            while self.service._retry_source is not None:
                self.timers.fire(self.service._retry_source)
            sl.set_divergence('2.198306')
            self.service.check()
            self.assertEqual(self.service._retry_attempt, 1)
            self.assertEqual(self.timers.sources[self.service._retry_source][0], 1)

    def test_preserves_existing_numeric_state(self):
        sl.set_divergence('2.198306')
        self.assertEqual(json.loads(self.service.GetState())['id'], 'hinamizawa')
        self.assertEqual(list(self.home.joinpath('state').glob('divergence*')), [sl.state_file()])

    def test_navigator_uses_fixed_desktop_entry_without_changing_worldline(self):
        sl.set_divergence('2.198306')
        app = Mock(); app.launch.return_value = True
        with patch.object(ws.Gio.DesktopAppInfo, 'new', return_value=app) as lookup:
            result = json.loads(self.service.OpenNavigator())
        lookup.assert_called_once_with('steins-navigator.desktop')
        app.launch.assert_called_once_with([], None)
        self.assertEqual(result['divergence'], '2.198306')
        self.assertEqual(sl.get_divergence(), '2.198306')

    def test_navigator_missing_entry_reports_failure_without_state_write(self):
        with patch.object(ws.Gio.DesktopAppInfo, 'new', return_value=None):
            with self.assertRaises(RuntimeError): self.service.OpenNavigator()
        self.assertFalse(sl.state_file().exists())

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

    def test_local_messages_compute_from_latest_service_state(self):
        sl.set_divergence('1.048596')
        expected = sl.send_dmail('first fixture', '1.048596')
        self.assertEqual(json.loads(self.service.ShiftMessage('first fixture'))['divergence'], expected)
        next_value = sl.send_dmail('second fixture', expected)
        self.assertEqual(json.loads(self.service.ShiftMessage('second fixture'))['divergence'], next_value)
        self.assertEqual(sl.get_divergence(), next_value)

    def test_reply_captures_serialized_previous_state_without_persisting_history(self):
        sl.set_divergence('2.198306')
        reply = json.loads(self.service.SetDivergence('3.072100'))
        self.assertEqual(reply['previous_divergence'], '2.198306')
        self.assertNotIn('previous_divergence', json.loads(self.service.GetState()))
        reply = json.loads(self.service.ShiftMessage('fixture'))
        self.assertEqual(reply['previous_divergence'], '3.072100')

    def test_local_message_prepare_failure_preserves_state(self):
        sl.set_divergence('1.048596')
        self.prepare_mock.side_effect = RuntimeError('renderer unavailable')
        with self.assertRaises(RuntimeError): self.service.ShiftMessage('fixture')
        self.assertEqual(sl.get_divergence(), '1.048596')

    def test_empty_and_oversized_local_message_never_write(self):
        for text in ('', '  ', 'x' * 4097):
            with self.assertRaises(ValueError): self.service.ShiftMessage(text)
        self.assertFalse(sl.state_file().exists())
        self.prepare_mock.assert_not_called()

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
