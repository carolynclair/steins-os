#!/bin/bash
# Disposable VM fixture; the recorded Bash PID survives appearance changes.
set -eu
mkdir -p /tmp/v4-design
echo "$$" >/tmp/v4-design/probe.pid
PROBE_STDIN_TTY=0
[ ! -t 0 ] || PROBE_STDIN_TTY=1
export PROBE_STDIN_TTY
python3 - <<'PY'
import os,json,fcntl,termios,struct
from pathlib import Path
fd=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY)
rows,cols,_,_=struct.unpack('HHHH',fcntl.ioctl(fd,termios.TIOCGWINSZ,b'\0'*8));os.close(fd)
Path('/tmp/v4-design/pty.json').write_text(json.dumps({'stdin_tty':os.environ['PROBE_STDIN_TTY']=='1','stdout_tty':os.isatty(1),'rows':rows,'columns':cols,'term':os.environ.get('TERM')}))
print('Steins;OS  /  Laboratory Terminal')
print('────────────────────────────────────────')
print('Worldline link active · real Bash session')
print('Unicode: λ → Δ  日本語')
print('\x1b[38;2;180;191;153mHINAMIZAWA\x1b[0m  /  Quiet instruments. Familiar tools.')
PY
export PS1='\[\e[38;2;171;182;188m\]observer@steins\[\e[0m\] \w\n\$ '
exec /bin/bash --noprofile --norc -i
