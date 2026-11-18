#!/usr/bin/env python3
"""Temporary qcow2 fixtures only. Never starts a VM or accesses real QA disks."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess as sp
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('vm_lab',Path(__file__).with_name('vm_lab.py'))
vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)


class ColdForkTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.project=Path(self.tmp.name)
        self.lab=vm.Lab(self.project)
        self.lab.source.parent.mkdir(parents=True);self.lab.base.parent.mkdir(parents=True)
        sp.run(['qemu-img','create','-f','qcow2',str(self.lab.base),'16M'],capture_output=True,check=True)
        sp.run(['qemu-img','create','-f','qcow2','-F','qcow2','-b',str(self.lab.base),str(self.lab.source)],capture_output=True,check=True)
        self.lab.vars.write_bytes(b'test UEFI variables, not firmware')
        self.cold=patch.object(self.lab,'assert_cold',return_value=None);self.cold.start()
        self.space=patch.object(self.lab,'space',return_value=None);self.space.start()
    def tearDown(self):
        self.cold.stop();self.space.stop();self.tmp.cleanup()
    def test_capture_preserves_source_and_pins_backing(self):
        before=vm.digest(self.lab.source);mode=self.lab.source.stat().st_mode
        self.lab.checkpoint('baseline');data=self.lab.verify('baseline')
        self.assertEqual(vm.digest(self.lab.source),before)
        self.assertEqual(self.lab.source.stat().st_mode,mode)
        self.assertEqual(data['base_sha256'],vm.digest(self.lab.base))
        self.assertEqual((self.lab.root/'checkpoints/baseline/system.qcow2').stat().st_mode&0o777,0o400)
    def test_reset_retains_old_run_and_matches_nvram(self):
        self.lab.checkpoint('baseline');first=self.lab.reset('baseline');second=self.lab.reset()
        self.assertNotEqual(first['run'],second['run'])
        for state in (first,second):
            folder=self.lab.root/'runs'/state['run']
            self.assertTrue((folder/'system.qcow2').is_file())
            self.assertEqual((folder/'OVMF_VARS.fd').read_bytes(),self.lab.vars.read_bytes())
        self.assertEqual(self.lab.state()['run'],second['run'])
    def test_duplicate_checkpoint_never_overwrites(self):
        self.lab.checkpoint('baseline')
        with self.assertRaises(FileExistsError):self.lab.checkpoint('baseline')
    def test_backing_mutation_is_detected(self):
        self.lab.checkpoint('baseline')
        with self.lab.base.open('ab') as f:f.write(b'changed')
        with self.assertRaises(ValueError):self.lab.verify('baseline')
    def test_checkpoint_tampering_is_detected(self):
        self.lab.checkpoint('baseline');p=self.lab.root/'checkpoints/baseline/OVMF_VARS.fd';p.chmod(0o600);p.write_bytes(b'changed')
        with self.assertRaises(ValueError):self.lab.reset('baseline')
    def test_rejects_path_escape_and_symlink_source(self):
        with self.assertRaises(ValueError):self.lab.checkpoint('../outside')
        target=self.lab.source.with_name('real.qcow2');self.lab.source.rename(target);self.lab.source.symlink_to(target)
        with self.assertRaises(ValueError):self.lab.checkpoint('baseline')
    def test_rejects_redirected_lab_directory(self):
        destination=self.project/'outside';destination.mkdir()
        self.lab.root.symlink_to(destination,target_is_directory=True)
        with self.assertRaises(ValueError):self.lab.checkpoint('baseline')
    def test_cold_guard_failure_prevents_creation(self):
        self.cold.stop()
        with patch.object(self.lab,'running',return_value={'running':True}):
            with self.assertRaises(RuntimeError):self.lab.checkpoint('baseline')
        self.assertFalse(self.lab.root.exists())
        self.cold.start()


if __name__=='__main__':unittest.main()
