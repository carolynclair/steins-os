#!/usr/bin/env python3
"""Bounded one-file loopback transfer to the V3 guest's private /tmp folder."""
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import shlex
import re
import threading
import shutil
import sys
from vm_lab import Lab,regular

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('source',type=Path);ap.add_argument('--name')
a=ap.parse_args();source=regular(a.source);lab=Lab()
if not source.is_relative_to(lab.project):sys.exit('Transfer source must be inside this project')
name=a.name or source.name
if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,100}',name):sys.exit('Choose a plain guest filename')
destination='/tmp/v3-integration/'+name
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path!='/asset':self.send_error(404);return
        self.send_response(200);self.send_header('Content-Length',str(source.stat().st_size));self.end_headers()
        with source.open('rb') as f:shutil.copyfileobj(f,self.wfile)
    def log_message(self,*args):pass
lab.qmp('query-status')
with ThreadingHTTPServer(('127.0.0.1',0),Handler) as server:
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url='http://10.0.2.2:'+str(server.server_port)+'/asset'
    try:
        rc,output=lab.serial('umask 077; mkdir -p /tmp/v3-integration && test ! -e '+shlex.quote(destination)+
            ' && curl --fail --silent --show-error '+shlex.quote(url)+' -o '+shlex.quote(destination),55)
    finally:server.shutdown()
print(output or destination)
sys.exit(rc)
