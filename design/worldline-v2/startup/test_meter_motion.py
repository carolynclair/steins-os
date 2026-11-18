#!/usr/bin/python3
"""Headless regression checks of real MeterWindow methods with fake GTK state."""
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
PROJECT=Path(__file__).resolve().parents[3]
ns=runpy.run_path(str(PROJECT/'config/includes.chroot/usr/local/bin/steins-meter'),run_name='steins_meter_motion_test')
Window=ns['MeterWindow'];sl=ns['sl'];meterlib=ns['meterlib'];glib=ns['GLib']
PALETTE={'bg':'#151b20','bg_alt':'#141a1e','fg':'#e7e2d6','accent':'#e99a45',
         'selection':'#a2652a','muted':'#9cab9f'}
PACK=SimpleNamespace(name='Steins Gate',palette=PALETTE)


class FakeMeter:
    refresh=Window.refresh
    cancel_animation=Window.cancel_animation
    animate=Window.animate
    on_file_event=Window.on_file_event
    refresh_once=Window.refresh_once
    def __init__(self):
        self.shown='1.048596';self.animation=None;self.animation_generation=0
        self.provider=Mock();self.world=Mock();self.button=Mock();self.display=[]
    def show_text(self,text,scrambling=False):self.display.append((text,scrambling))


class MotionPolicy(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name)
        self.prefs=self.folder/'preferences.json'
    def tearDown(self):self.tmp.cleanup()
    def test_absent_file_uses_explicit_session_default(self):
        self.assertEqual(meterlib.motion_profile(self.prefs,'reduced'),'reduced')
        self.assertEqual(meterlib.motion_profile(self.prefs,'full'),'full')
    def test_valid_profiles(self):
        for mode in ('full','reduced','off'):
            self.prefs.write_text(json.dumps({'motion':mode}))
            self.assertEqual(meterlib.motion_profile(self.prefs),mode)
    def test_corrupt_shapes_or_values_fail_to_reduced(self):
        for text in ('{bad','[]','null','"full"','{"motion":"flash"}','{"motion":true}'):
            self.prefs.write_text(text)
            self.assertEqual(meterlib.motion_profile(self.prefs,'full'),'reduced')
    def test_unreadable_preferences_fail_to_reduced(self):
        with patch.object(Path,'read_text',side_effect=PermissionError('test only')):
            self.assertEqual(meterlib.motion_profile(self.prefs,'full'),'reduced')


class ActualMeterFlow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.folder=Path(self.tmp.name)
        self.prefs=self.folder/'preferences.json';self.timer_calls=[];self.removed=[]
        self.meter=FakeMeter()
        self.patches=[patch.object(sl,'state_dir',return_value=self.folder),
                      patch.object(sl,'state_file',return_value=self.folder/'divergence'),
                      patch.object(sl,'current',return_value=('2.198306',PACK)),
                      patch.object(glib,'timeout_add',side_effect=self.timeout),
                      patch.object(glib,'source_remove',side_effect=self.removed.append),
                      patch.dict(os.environ,{'STEINS_DESKTOP_BACKEND':'plasma'})]
        self.mocks=[p.start() for p in self.patches]
        self.current=self.mocks[2]
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()
    def timeout(self,interval,callback):
        source=101+len(self.timer_calls);self.timer_calls.append((interval,callback,source));return source
    def mode(self,value):self.prefs.write_text(json.dumps({'motion':value}))
    def test_plasma_default_changes_digits_without_animation(self):
        self.meter.refresh()
        self.assertEqual(self.meter.display[-1],('2.198306',False))
        self.assertEqual(self.meter.shown,'2.198306');self.assertFalse(self.timer_calls)
    def test_reduced_and_off_cancel_even_when_confirmed_number_unchanged(self):
        for mode in ('reduced','off'):
            with self.subTest(mode=mode):
                self.mode(mode);self.meter.shown='2.198306';self.meter.animation=77
                self.meter.refresh()
                self.assertEqual(self.meter.display[-1],('2.198306',False))
                self.assertIsNone(self.meter.animation);self.assertIn(77,self.removed)
        self.assertFalse(self.timer_calls)
    def test_full_retains_fifteen_frames_and_settles_exactly(self):
        self.mode('full');self.meter.refresh()
        interval,callback,source=self.timer_calls[0]
        self.assertEqual(interval,40);self.assertEqual(self.meter.animation,source)
        active=[callback() for _ in range(15)]
        self.assertTrue(all(active[:-1]));self.assertFalse(active[-1])
        self.assertEqual(self.meter.display[-1],('2.198306',False));self.assertIsNone(self.meter.animation)
    def test_same_value_poll_does_not_restart_full_animation(self):
        self.mode('full');self.meter.refresh();generation=self.meter.animation_generation
        self.meter.refresh()
        self.assertEqual(len(self.timer_calls),1)
        self.assertEqual(self.meter.animation_generation,generation)
    def test_queued_old_tick_cannot_overwrite_reduced_value(self):
        self.mode('full');self.meter.refresh();old_tick=self.timer_calls[0][1]
        old_tick();self.mode('reduced');self.meter.refresh()
        count=len(self.meter.display)
        self.assertFalse(old_tick());self.assertEqual(len(self.meter.display),count)
        self.assertEqual(self.meter.display[-1],('2.198306',False));self.assertIsNone(self.meter.animation)
    def test_replaced_full_animation_rejects_old_callback(self):
        self.mode('full');self.meter.refresh();old_tick=self.timer_calls[0][1]
        self.current.return_value=('3.072100',PACK);self.meter.refresh()
        new_tick=self.timer_calls[1][1];new_source=self.timer_calls[1][2]
        self.assertIn(101,self.removed)
        self.assertFalse(old_tick());self.assertEqual(self.meter.animation,new_source)
        for _ in range(15):new_tick()
        self.assertEqual(self.meter.display[-1],('3.072100',False))
    def test_atomic_preference_destination_refreshes_synchronously(self):
        self.mode('full');self.meter.refresh();self.mode('off')
        file=SimpleNamespace(get_basename=lambda:'.preferences.json.tmp')
        other=SimpleNamespace(get_basename=lambda:'preferences.json')
        self.meter.on_file_event(None,file,other,None)
        self.assertIsNone(self.meter.animation)
        self.assertEqual(self.meter.display[-1],('2.198306',False))
        self.assertEqual(len(self.timer_calls),1)  # no delayed extra source for preferences
    def test_legacy_absence_preserves_existing_full_animation(self):
        with patch.dict(os.environ,{'STEINS_DESKTOP_BACKEND':'xfce'}):self.meter.refresh()
        self.assertEqual(len(self.timer_calls),1)


if __name__=='__main__':unittest.main()
