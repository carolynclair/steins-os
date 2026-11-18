#!/usr/bin/python3
import unittest
from vm_lab import completed_frame
class Protocol(unittest.TestCase):
    def test_echoed_command_is_not_a_completed_status(self):
        echo=b'printf "\\nV4_DONE_fixture: %s\\n" "$?"\r\n'
        self.assertIsNone(completed_frame(echo,'V4_DONE_fixture'))
        match=completed_frame(echo+b'payload\r\nV4_DONE_fixture: 0\r\n','V4_DONE_fixture')
        self.assertEqual(match.group(1),b'0')
    def test_partial_stale_and_non_numeric_frames_are_not_completion(self):
        for value in [b'\nV4_DONE_old: 0\n',b'\nV4_DONE_fixture: 1',b'\nV4_DONE_fixture: bad\n']:
            self.assertIsNone(completed_frame(value,'V4_DONE_fixture'))
        self.assertEqual(completed_frame(b'\nV4_DONE_fixture: 127\n','V4_DONE_fixture').group(1),b'127')
if __name__=='__main__':unittest.main()
