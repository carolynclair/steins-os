"""Version 1 per-user worldline bus; state remains the legacy divergence file."""
import hashlib
import json
import logging
import os
import signal
from pathlib import Path

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib, Gio

import steinslib as sl
import steinsplasma

BUS = 'org.steinsos.Worldline1'
PATH = '/org/steinsos/Worldline'
DEFAULTS = {'meter': False, 'motion': 'reduced'}
RETRY_DELAYS = (1, 2, 4, 8, 16)
TRANSIENT_WALLPAPER_ERRORS = frozenset(
    'org.freedesktop.DBus.Error.' + name
    for name in ('ServiceUnknown', 'NameHasNoOwner', 'NoReply'))


def preferences():
    try:
        data = json.loads((sl.state_dir() / 'preferences.json').read_text())
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    return {k: data.get(k, v) for k, v in DEFAULTS.items()
            if type(data.get(k, v)) is type(v) and
            (k != 'motion' or data.get(k, v) in ('off', 'reduced', 'full'))}


def snapshot():
    d, p = sl.current()
    prefs = {**DEFAULTS, **preferences()}
    state = {'interface': 1, 'divergence': d, 'id': p.id if p else '',
             'name': p.name if p else 'Unavailable', 'palette': p.palette if p else {},
             'preferences': prefs}
    state['revision'] = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:16]
    return state


def dump(obj):
    return json.dumps(obj, ensure_ascii=True)


class Service(dbus.service.Object):
    def __init__(self, bus):
        self.name = dbus.service.BusName(BUS, bus=bus, do_not_queue=True)
        super().__init__(self.name, PATH)
        self.last = ''
        self.result = None
        self.meter = None
        self._retry_source = None
        self._retry_revision = None
        self._retry_attempt = 0
        self._retry_generation = 0
        sl.state_dir().mkdir(parents=True, exist_ok=True)
        self.monitor = Gio.File.new_for_path(str(sl.state_dir())).monitor_directory(Gio.FileMonitorFlags.NONE, None)
        self.monitor.connect('changed', lambda *args: self.queue_check())
        self.pending = False
        GLib.timeout_add_seconds(3, lambda: (self.check(), True)[1])
        GLib.idle_add(self.check)

    def queue_check(self):
        if not self.pending:
            self.pending = True
            GLib.timeout_add(150, self.check)

    def check(self):
        self.pending = False
        state = snapshot()
        if state['revision'] != self.last:
            self.apply(state)
        return False

    def apply(self, state=None, wallpaper=None):
        state = state or snapshot()
        if self._retry_revision is not None and self._retry_revision != state['revision']:
            self._cancel_retry()
        try:
            pack = sl.pick_pack(state['divergence'])
            result = (steinsplasma.apply_prepared(pack, wallpaper) if wallpaper
                      else steinsplasma.apply_pack(pack))
            errors = [{'step': k, 'message': detail} for k, ok, detail in result.steps if not ok]
        except Exception as e:
            errors = [{'step': 'apply', 'message': str(e)}]
        # Keep partial failure explicit. ApplyCurrent retries without rewriting state.
        self.last = state['revision']
        state['applied'] = not errors
        state['errors'] = errors
        self.result = state
        self._update_retry(state['revision'], errors)
        self.sync_meter(state['preferences']['meter'])
        self.StateChanged(dump(state))
        self.ApplyFinished(dump(state))
        logging.info('worldline %s applied=%s errors=%s', state['id'], state['applied'], errors)
        return dump(state)

    def _cancel_retry(self):
        # A removed source may already have queued a callback. Invalidate that too.
        self._retry_generation += 1
        if self._retry_source is not None:
            GLib.source_remove(self._retry_source)
        self._retry_source = None
        self._retry_revision = None
        self._retry_attempt = 0

    def _update_retry(self, revision, errors):
        # The session bus can exist before plasmashell owns its name at login.
        # Retry only this narrow dependency failure, never arbitrary file/GTK errors.
        transient = bool(errors) and all(
            error['step'] == 'wallpaper' and
            error['message'].partition(':')[0].strip() in TRANSIENT_WALLPAPER_ERRORS
            for error in errors)
        if not transient:
            self._cancel_retry()
            return
        if self._retry_revision != revision:
            self._cancel_retry()
            self._retry_revision = revision
        if self._retry_source is not None or self._retry_attempt >= len(RETRY_DELAYS):
            return
        delay = RETRY_DELAYS[self._retry_attempt]
        self._retry_attempt += 1
        self._retry_generation += 1
        generation = self._retry_generation

        def retry():
            if generation != self._retry_generation:
                return False
            self._retry_source = None
            self._retry_generation += 1  # This callback is single-use, even if queued twice.
            current = snapshot()
            if current['revision'] != revision:
                self._cancel_retry()
                self.check()             # Apply the latest state, never the stale destination.
            else:
                self.apply(current)      # Reapply only; do not rewrite divergence.
            return False

        self._retry_source = GLib.timeout_add_seconds(delay, retry)
        logging.info('Transient wallpaper dependency; retry %s/%s in %ss',
                     self._retry_attempt, len(RETRY_DELAYS), delay)

    def sync_meter(self, visible):
        import subprocess
        if visible and (self.meter is None or self.meter.poll() is not None):
            self.meter = subprocess.Popen(['/usr/bin/steins-meter'], start_new_session=True)
        elif not visible and self.meter is not None and self.meter.poll() is None:
            self.meter.terminate()  # Only our child, never a user's independently opened widget.
            self.meter = None

    @dbus.service.method(BUS, in_signature='', out_signature='s')
    def GetState(self):
        state = snapshot()
        return dump(self.result if self.result and self.result['revision'] == state['revision'] else state)

    @dbus.service.method(BUS, in_signature='', out_signature='s')
    def ListWorldlines(self):
        return dump([{'id': p.id, 'name': p.name, 'divergence': p.divergence, 'palette': p.palette}
                     for p in sorted(sl.load_packs(), key=lambda p: p.low)])

    @dbus.service.method(BUS, in_signature='s', out_signature='s')
    def SetDivergence(self, value):
        value = sl.normalize(str(value))
        pack = sl.pick_pack(value)
        wallpaper = steinsplasma.prepare(pack)  # No state change if preparation fails.
        sl.set_divergence(value)
        return self.apply(wallpaper=wallpaper)

    @dbus.service.method(BUS, in_signature='ss', out_signature='s')
    def SetPreference(self, key, encoded):
        value = json.loads(str(encoded))
        if key == 'meter' and type(value) is bool:
            pass
        elif key == 'motion' and value in ('off', 'reduced', 'full'):
            pass
        else:
            raise ValueError('Unknown preference or invalid value')
        prefs = {**DEFAULTS, **preferences(), str(key): value}
        sl.atomic_write(sl.state_dir() / 'preferences.json', dump(prefs) + '\n')
        return self.apply()

    @dbus.service.method(BUS, in_signature='', out_signature='s')
    def ApplyCurrent(self):
        return self.apply()

    @dbus.service.signal(BUS, signature='s')
    def StateChanged(self, state):
        pass

    @dbus.service.signal(BUS, signature='s')
    def ApplyFinished(self, result):
        pass


def main():
    logging.basicConfig(level=logging.INFO)
    DBusGMainLoop(set_as_default=True)
    service = Service(dbus.SessionBus())
    loop = GLib.MainLoop()
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (loop.quit(), False)[1])
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, lambda: (loop.quit(), False)[1])
    try:
        loop.run()
    finally:
        service._cancel_retry()
        service.sync_meter(False)


if __name__ == '__main__':
    main()
