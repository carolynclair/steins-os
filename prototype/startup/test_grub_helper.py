#!/usr/bin/env python3
"""Meaningful filesystem/rollback tests; never runs update-grub on the host."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('grub_lab',ROOT/'tools/grub-lab.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Fixture(unittest.TestCase):
 def setUp(self):
  self.previous_umask=os.umask(0o022);self.addCleanup(os.umask,self.previous_umask)
  self.temp=tempfile.TemporaryDirectory(prefix='steins-grub-fixture-');self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name)
  self.events=[];self.lab=module.GuestGrub(self.root,lambda:self.events.append('update-grub'))
  self.lab.compiled.parent.mkdir(parents=True);self.lab.compiled.write_bytes(b'old generated boot menu\n');self.lab.compiled.chmod(0o400)
  self.lab.cfg.parent.mkdir(parents=True)
  for size in module.SIZES:
   p=self.root/f'usr/share/steins/startup/grub-background-{size}.png';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
 def test_existing_configuration_byte_and_mode_restore(self):
  old=b'# previous own config\nGRUB_BACKGROUND="previous.png"\n';self.lab.cfg.write_bytes(old);self.lab.cfg.chmod(0o600)
  info=self.lab.apply('1280x800');self.assertEqual(self.events,['update-grub'])
  self.assertIn(b'grub-background-1280x800.png',self.lab.cfg.read_bytes())
  self.assertNotIn(b'GRUB_CMDLINE',self.lab.cfg.read_bytes());self.assertNotIn(b'GRUB_TIMEOUT',self.lab.cfg.read_bytes())
  result=self.lab.rollback();self.assertEqual(self.lab.cfg.read_bytes(),old)
  self.assertEqual(stat.S_IMODE(self.lab.cfg.stat().st_mode),0o600)
  self.assertTrue((self.lab.store/info['id']/'previous.cfg').exists());self.assertTrue(result['backups_retained'])
 def test_absent_own_configuration_removed_neighbour_preserved(self):
  neighbour=self.lab.cfg.parent/'other.cfg';neighbour.write_bytes(b'keep me')
  self.lab.apply('1366x768');self.lab.rollback()
  self.assertFalse(self.lab.cfg.exists());self.assertEqual(neighbour.read_bytes(),b'keep me')
 def test_failed_generation_restores_both_files(self):
  self.lab.cfg.write_bytes(b'old own file');self.lab.cfg.chmod(0o600)
  def fail():
   self.lab.compiled.write_bytes(b'bad generated output');raise RuntimeError('fixture update failure')
  self.lab.runner=fail
  with self.assertRaisesRegex(RuntimeError,'restored'):self.lab.apply('1280x800')
  self.assertEqual(self.lab.cfg.read_bytes(),b'old own file');self.assertEqual(self.lab.compiled.read_bytes(),b'old generated boot menu\n')
  self.assertEqual(stat.S_IMODE(self.lab.compiled.stat().st_mode),0o400);self.assertFalse(self.lab.state.exists())
 def test_failed_rollback_generation_restores_verified_compiled_backup(self):
  self.lab.cfg.write_bytes(b'original');self.lab.apply('1280x800')
  def fail():
   self.lab.compiled.write_bytes(b'failed regeneration');raise RuntimeError('fixture failure')
  self.lab.runner=fail
  with self.assertRaisesRegex(RuntimeError,'prior generated grub.cfg restored'):self.lab.rollback()
  self.assertEqual(self.lab.cfg.read_bytes(),b'original')
  self.assertEqual(self.lab.compiled.read_bytes(),b'old generated boot menu\n')
  self.assertEqual(stat.S_IMODE(self.lab.compiled.stat().st_mode),0o400)
  self.assertFalse(self.lab.state.exists())
 def test_later_edits_refuse_overwrite_and_repeat_apply_refused(self):
  self.lab.apply('1280x800')
  with self.assertRaisesRegex(ValueError,'active'):self.lab.apply('1366x768')
  self.lab.cfg.write_bytes(b'new manual changes')
  with self.assertRaisesRegex(ValueError,'changed since apply'):self.lab.rollback()
  self.assertEqual(self.lab.cfg.read_bytes(),b'new manual changes')
 def test_tampered_backup_refused(self):
  self.lab.cfg.write_bytes(b'original');info=self.lab.apply('1280x800')
  (self.lab.store/info['id']/'previous.cfg').write_bytes(b'tampered')
  with self.assertRaisesRegex(ValueError,'hash mismatch'):self.lab.rollback()
  self.assertIn(b'grub-background-',self.lab.cfg.read_bytes())
 def test_symlink_configuration_refused_without_destination_change(self):
  target=self.root/'never-change';target.write_bytes(b'unrelated')
  self.lab.cfg.symlink_to(target)
  with self.assertRaisesRegex(ValueError,'non-symlink'):self.lab.apply('1280x800')
  self.assertEqual(target.read_bytes(),b'unrelated');self.assertEqual(self.events,[])
 @unittest.skipIf(os.geteuid()==0,'non-root guard fixture requires ordinary user')
 def test_public_cli_refuses_nonroot_before_any_guest_operation(self):
  result=subprocess.run([sys.executable,str(ROOT/'tools/grub-lab.py'),'apply'],text=True,capture_output=True)
  self.assertNotEqual(result.returncode,0);self.assertIn('guest-only operation requires root',result.stderr)
if __name__=='__main__':unittest.main(verbosity=2)
