#!/usr/bin/python3
"""Real GTK object/scheduler check in the isolated guest, not a compositor test."""
import json
import os
from pathlib import Path
import runpy
import sys
import time

os.environ.update(DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus',XDG_RUNTIME_DIR='/run/user/1000',
                  WAYLAND_DISPLAY='wayland-0',STEINS_DESKTOP_BACKEND='plasma')
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gio,GLib
import dbus

ns=runpy.run_path('/usr/bin/steins-meter',run_name='v2_real_meter_probe')
api=dbus.Interface(dbus.SessionBus().get_object('org.steinsos.Worldline1','/org/steinsos/Worldline'),'org.steinsos.Worldline1')
api.SetPreference('meter','false',timeout=40)
api.SetPreference('motion','"full"',timeout=40);api.SetDivergence('1.048596',timeout=40)
app=Gtk.Application(application_id='org.steinsos.V2MeterValidation',flags=Gio.ApplicationFlags.NON_UNIQUE)
app.register(None);window=ns['MeterWindow'](app);window.show_all()
def pump(seconds=.08):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        while GLib.MainContext.default().pending():GLib.MainContext.default().iteration(False)
        time.sleep(.005)
pump()
api.SetDivergence('2.198306',timeout=40);window.refresh()
full_started=window.animation is not None
assert full_started
api.SetPreference('motion','"reduced"',timeout=40);window.refresh()
reduced_cancelled=window.animation is None
assert reduced_cancelled
pump(.7)
confirmed=''.join(label.get_text() for label in window.tubes)
assert confirmed=='2.198306',confirmed
api.SetPreference('motion','"off"',timeout=40);api.SetDivergence('1.048596',timeout=40);window.refresh();pump(.1)
off_static=window.animation is None and ''.join(label.get_text() for label in window.tubes)=='1.048596'
assert off_static
result={'actual_gtk_window':True,'full_scheduled':full_started,'reduced_cancels_timer':reduced_cancelled,
        'confirmed_digits_after_stale_tick_window':confirmed,'off_static':off_static,'scope':'hotfixed files in disposable V2 fork only'}
Path('/tmp/v2-validation/meter-live-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
window.destroy()
