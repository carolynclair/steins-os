#!/usr/bin/python3
"""Cold storage operations using tiny disposable images; no actual VM mutation."""
import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from vm_lab import Lab, engine, PROJECT


class Freeze(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        for name in ('prototype/integration/vm_lab.py', 'design/worldline-v2/engineering/vm_lab.py'):
            target = self.project / name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / name, target)
        spec = importlib.util.spec_from_file_location('_v3_fixture', self.project / 'prototype/integration/vm_lab.py')
        old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
        self.previous = old.Lab(self.project)
        for name in ('assert_cold', 'space'):
            p = patch.object(self.previous, name); p.start(); self.addCleanup(p.stop)
        for folder in (self.previous.source.parent, self.previous.base.parent): folder.mkdir(parents=True, exist_ok=True)
        subprocess.run(['qemu-img', 'create', '-q', '-f', 'qcow2', str(self.previous.base), '16M'], check=True)
        subprocess.run(['qemu-img', 'create', '-q', '-f', 'qcow2', '-F', 'qcow2', '-b', str(self.previous.base), str(self.previous.source)], check=True)
        self.previous.vars.write_bytes(b'fixture NVRAM')
        self.previous.checkpoint('baseline'); self.previous.reset('baseline'); self.previous.freeze('native-v3')
        self.lab = Lab(self.project)
        for name in ('assert_cold', 'space'):
            p = patch.object(self.lab, name); p.start(); self.addCleanup(p.stop)
    def tearDown(self): self.tmp.cleanup()
    def test_seed_reset_freeze_preserves_v3_and_pins_every_ancestor(self):
        source = self.previous.root / 'checkpoints/native-v3/system.qcow2'
        before = engine.digest(source)
        data = self.lab.seed(); self.assertEqual(data['disk_sha256'], before)
        self.lab.reset('v3-base'); data = self.lab.freeze('native-v4')
        self.assertEqual(len(data['ancestors']), 3)
        self.lab.reset('native-v4'); self.assertEqual(engine.digest(source), before)
        self.lab.verify('native-v4')
    def test_seed_duplicate_is_never_overwritten(self):
        self.lab.seed()
        with self.assertRaises(FileExistsError): self.lab.seed()
    def test_tampered_v3_ancestor_is_rejected(self):
        self.lab.seed(); self.previous.base.write_bytes(self.previous.base.read_bytes() + b'changed')
        with self.assertRaises(ValueError): self.lab.verify('v3-base')
    def test_running_guard_prevents_seed(self):
        self.lab.assert_cold.side_effect = RuntimeError('running')
        with self.assertRaises(RuntimeError): self.lab.seed()
        self.assertFalse((self.lab.root / 'checkpoints/v3-base').exists())

if __name__ == '__main__': unittest.main()
