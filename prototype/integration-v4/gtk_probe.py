#!/usr/bin/python3
"""Temporary VM-only GTK3 appearance fixture; no production app is added."""
import os,socket
assert os.getuid()==1000 and socket.gethostname()=='steins-prototype'
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,GLib
w=Gtk.Window(title='GTK appearance check — V4 test fixture')
w.set_default_size(540,300);w.set_border_width(24)
box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=14);w.add(box)
box.pack_start(Gtk.Label(label='Neutral selection · readable keyboard focus',xalign=0),False,False,0)
rows=Gtk.ListBox();rows.set_selection_mode(Gtk.SelectionMode.SINGLE)
for text in ['Files and settings remain familiar','Selected row uses shared graphite','Six atmospheres. One identity.']:
 row=Gtk.ListBoxRow();label=Gtk.Label(label=text,xalign=0);label.set_margin_top(8);label.set_margin_bottom(8);row.add(label);rows.add(row)
box.pack_start(rows,True,True,0)
entry=Gtk.Entry();entry.set_text('Focused GTK entry / λ → Δ');box.pack_start(entry,False,False,0)
button=Gtk.Button(label='Close test fixture');button.connect('clicked',lambda *_:w.destroy());box.pack_start(button,False,False,0)
w.connect('destroy',lambda *_:Gtk.main_quit());w.show_all()
rows.select_row(rows.get_row_at_index(1));entry.grab_focus();entry.select_region(0,7)
Gtk.main()
