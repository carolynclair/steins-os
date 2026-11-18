#!/bin/bash
# Disposable guest only. Started by the existing Konsole to verify its real PTY.
set -eu
PROBE_SHELL_STDIN_TTY=0
[ ! -t 0 ] || PROBE_SHELL_STDIN_TTY=1
export PROBE_SHELL_STDIN_TTY
python3 - <<'PY'
import os,json,fcntl,termios,struct
from pathlib import Path
fd=os.open('/dev/tty',os.O_RDWR|os.O_NOCTTY)
size=struct.unpack('HHHH',fcntl.ioctl(fd,termios.TIOCGWINSZ,b'\0'*8));os.close(fd)
result={'stdin_tty':os.environ['PROBE_SHELL_STDIN_TTY']=='1','stdout_tty':os.isatty(1),'term':os.environ.get('TERM'),
        'rows':size[0],'columns':size[1],'shell':'bash','pid':os.getppid()}
Path('/tmp/v2-validation/pty-result.json').write_text(json.dumps(result,indent=2)+'\n')
print('Steins;OS existing terminal / real PTY validation')
print('Unicode: λ → Δ  日本語')
print('TTY:',os.ttyname(1),'  Geometry:',size[0], '×',size[1])
print('\x1b[38;2;239;173;96mTrue-colour sample / amber\x1b[0m')
PY
printf '\nBash process remains active; this is the existing Konsole engine.\n'
trap 'stty size >>/tmp/v2-validation/pty-resizes.log' WINCH
printf '%s\n' "$BASHPID" >/tmp/v2-validation/probe.pid
while IFS= read -r line; do
  printf 'Input received: %s\n' "$line"
  printf '%s\n' "$line" >>/tmp/v2-validation/pty-input.log
  [ "$line" != exit ] || break
done
