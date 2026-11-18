#!/usr/bin/python3
"""Exercise actual V4 QML with a deterministic backend; capture layout evidence.
This is not a real D-Bus or compositor/session test.
"""
import json
import os
from pathlib import Path
import sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
from PySide6.QtCore import QObject, Signal, Property, Slot, QUrl, Qt, QPointF
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow, QQuickItem
from PySide6.QtTest import QTest
from shiboken6 import delete
SOURCE = Path(__file__).resolve().parents[1]
ROOT = SOURCE.parents[1]
sys.path.insert(0, str(SOURCE / 'share'))
from surface_tokens import load_tokens
OUT = ROOT / 'dist/v4/surfaces'
OUT.mkdir(parents=True, exist_ok=True)


class Fixture(QObject):
    changed = Signal()
    def __init__(self):
        super().__init__()
        self.selected = []
        self.retries = 0
        self.meters = []
        self.tokens = load_tokens(ROOT / 'prototype/identity-v4/TOKENS.json')
        self._packs = [{'id': key, 'name': {'alpha': 'Alpha', 'steins-gate': 'Steins Gate', 'hinamizawa': 'Hinamizawa', 'hitogashima': 'Hitogashima', 'lugunica': 'Lugunica', 'mitakihara': 'Mitakihara'}[key],
                        'divergence': f'{i}.048596'} for i, key in enumerate(self.tokens['worldlines'])]
        self._state = dict(self._packs[2], preferences={'meter': False})
    @Property('QVariantMap', notify=changed)
    def state(self): return self._state
    @Property('QVariantList', notify=changed)
    def packs(self): return self._packs
    @Property(bool, notify=changed)
    def busy(self): return False
    @Property(str, notify=changed)
    def error(self): return ''
    @Slot(str)
    def select(self, value): self.selected.append(value)
    @Slot(bool)
    def meter(self, value): self.meters.append(value)
    @Slot()
    def retry(self): self.retries += 1


app = QGuiApplication([])
backend = Fixture()
engine = QQmlApplicationEngine()
warnings = []
engine.warnings.connect(lambda items: warnings.extend(item.toString() for item in items))
engine.rootContext().setContextProperty('worldline', backend)
engine.rootContext().setContextProperty('designTokens', backend.tokens)
engine.load(QUrl.fromLocalFile(str(SOURCE / 'share/Navigator.qml')))
assert engine.rootObjects(), 'QML failed to load'
window = engine.rootObjects()[0]
QTest.qWait(250)
def visual_items(item):
    yield item
    for child in item.childItems():
        yield from visual_items(child)

def find_item(name):
    return next((item for item in visual_items(window.contentItem()) if item.objectName() == name), None)

cards = [find_item('worldline-card-' + item['id']) for item in backend.packs]
assert all(cards), 'Missing worldline cards'
assert sum(bool(card.property('selected')) for card in cards) == 1
for width, name in [(880, 'navigator-wide'), (650, 'navigator-narrow')]:
    window.resize(width, 650)
    QTest.qWait(150)
    assert all(card.width() > 150 and card.height() >= 134 for card in cards)
    positions = [(card.mapToScene(QPointF(0, 0)).x(), card.mapToScene(QPointF(0, 0)).y(), card.width(), card.height()) for card in cards]
    for i, (x, y, w, h) in enumerate(positions):
        for xx, yy, ww, hh in positions[i+1:]:
            assert x+w <= xx+0.5 or xx+ww <= x+0.5 or y+h <= yy+0.5 or yy+hh <= y+0.5, 'Overlapping cards'
    assert window.grabWindow().save(str(OUT / (name + '.png')))
window.resize(880, 650)
QTest.qWait(100)
card = cards[3]
card.forceActiveFocus()
QTest.qWait(40)
assert card.property('activeFocus')
QTest.keyClick(window, Qt.Key_Space)
QTest.qWait(50)
assert backend.selected == [backend.packs[3]['divergence']], backend.selected
meter = find_item('meter-switch')
meter.forceActiveFocus()
QTest.keyClick(window, Qt.Key_Space)
QTest.qWait(50)
assert backend.meters == [True], backend.meters
retry = find_item('appearance-retry')
retry.forceActiveFocus()
QTest.keyClick(window, Qt.Key_Space)
QTest.qWait(50)
assert backend.retries == 1
assert not warnings, warnings
result = {'qml_loaded': True, 'cards': 6, 'current_label': True, 'layouts': [880, 650],
          'card_overlap': False, 'keyboard_switch_request': True, 'keyboard_meter_toggle': True,
          'keyboard_reapply': True, 'qml_warnings': warnings,
          'backend': 'deterministic fixture, no state files or session bus',
          'render': 'Qt Quick software offscreen; not compositor or Wayland qualification'}
window.close()
delete(window)
delete(engine)
assert not warnings, warnings
(OUT / 'QML-VERIFICATION.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
