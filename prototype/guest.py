#!/usr/bin/env python3
"""Serial control for the disposable design VM only; never targets the review VM."""
import argparse
import socket
import shlex
import sys
import time
import uuid

ap = argparse.ArgumentParser()
ap.add_argument('command')
ap.add_argument('--timeout', type=int, default=30)
a = ap.parse_args()
marker = 'DESIGN_DONE_' + uuid.uuid4().hex
with socket.socket(socket.AF_UNIX) as s:
    s.connect('/tmp/steins-design-serial.sock')
    s.settimeout(.5)
    s.sendall(('bash -c ' + shlex.quote(a.command) + ' </dev/null; printf "\\n' + marker + ': %s\\n" "$?"\n').encode())
    buf = b''
    end = time.monotonic() + a.timeout
    while time.monotonic() < end:
        try:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if (marker + ': ').encode() in buf:
                decoded = buf.decode(errors='replace')
                before, status = decoded.split(marker + ': ', 1)
                if '\n' not in status:
                    continue
                print(before.strip())
                sys.exit(int(status.splitlines()[0].strip()))
        except TimeoutError:
            pass
    print(buf.decode(errors='replace'))
    sys.exit('Serial command did not complete before deadline')
