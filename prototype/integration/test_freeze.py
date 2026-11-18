#!/usr/bin/python3
"""Verify cold freeze/reset with temporary QCOW2 fixtures; no real VM touched."""
import json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from vm_lab import Lab,engine
class Freeze(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.project=Path(self.tmp.name);self.lab=Lab(self.project)
  self.cold=patch.object(self.lab,'assert_cold');self.cold.start();patcher=patch.object(self.lab,'space');patcher.start();self.addCleanup(patcher.stop)
  for p in [self.lab.source.parent,self.lab.base.parent]:p.mkdir(parents=True,exist_ok=True)
  subprocess.run(['qemu-img','create','-q','-f','qcow2',str(self.lab.base),'16M'],check=True)
  subprocess.run(['qemu-img','create','-q','-f','qcow2','-F','qcow2','-b',str(self.lab.base),str(self.lab.source)],check=True)
  self.lab.vars.write_bytes(b'fixture NVRAM')
  self.lab.checkpoint('baseline');self.lab.reset('baseline')
 def tearDown(self):self.cold.stop();self.tmp.cleanup()
 def test_freeze_and_reset_preserve_old_run_and_pin_every_ancestor(self):
  state=self.lab.state();run=self.lab.root/'runs'/state['run']/'system.qcow2';before=engine.digest(run)
  data=self.lab.freeze('native-v3');self.assertEqual(data['disk_sha256'],before);self.assertEqual(len(data['ancestors']),2)
  next_state=self.lab.reset('native-v3');self.assertNotEqual(next_state['run'],state['run']);self.assertEqual(engine.digest(run),before)
  self.assertEqual(self.lab.chain(self.lab.root/'runs'/next_state['run']/'system.qcow2')[1]['filename'],str(self.lab.root/'checkpoints/native-v3/system.qcow2'))
 def test_ancestor_tamper_detected(self):
  self.lab.freeze('native-v3');self.lab.base.write_bytes(self.lab.base.read_bytes()+b'changed')
  with self.assertRaises(ValueError):self.lab.verify('native-v3')
 def test_duplicate_freeze_refused(self):
  self.lab.freeze('native-v3')
  with self.assertRaises(FileExistsError):self.lab.freeze('native-v3')
 def test_running_guard_prevents_any_capture(self):
  self.lab.assert_cold.side_effect=RuntimeError('running')
  with self.assertRaises(RuntimeError):self.lab.freeze('native-v3')
  self.assertFalse((self.lab.root/'checkpoints/native-v3').exists())
if __name__=='__main__':unittest.main()
