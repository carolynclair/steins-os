#!/usr/bin/env python3
"""Expose only dist/prototype on loopback for one bounded guest command."""
import functools
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import subprocess
import sys
import threading

root = Path(__file__).resolve().parents[1]
handler = functools.partial(SimpleHTTPRequestHandler, directory=str(root / 'dist/prototype'))
with ThreadingHTTPServer(('127.0.0.1', 0), handler) as server:
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = 'http://10.0.2.2:' + str(server.server_port)
    command = sys.argv[1].replace('{url}', url)
    try:
        result = subprocess.run([sys.executable, str(root / 'prototype/guest.py'), command, '--timeout', '55'])
    finally:
        server.shutdown()
    sys.exit(result.returncode)
