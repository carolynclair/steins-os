# Synthetic local SSH fixture

`python3 prototype/terminal/ssh-fixture/lab.py start` creates one labelled Docker container, installs OpenSSH **inside it**, generates test-only keys/account and binds its SSH port to **host 127.0.0.1 at a Docker-assigned port**. No host sshd, account, SSH configuration, personal credential or package is changed. Password/root login and forwarding are disabled. The server is a qualification fixture, not part of Steins;OS packages or ISO content.

Runtime state, generated client key and pinned server host key are in the already ignored private `evidence/v3-integration/lab/ssh-fixture/` folder. `state.json` reports the port and public server fingerprint. Do not distribute this runtime folder or include it in a handoff. The key is synthetic, but still has no reason to leave this isolated test.

The V3 user-NAT guest reaches host loopback at `10.0.2.2`. Transfer only `client_key` and `known_hosts` into its private fixture directory, set permissions 600 and launch the ordinary guest OpenSSH client inside the actual terminal:

```sh
ssh -tt -F /dev/null -i /tmp/v3-ssh/client_key \
  -o IdentitiesOnly=yes -o PasswordAuthentication=no \
  -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/tmp/v3-ssh/known_hosts \
  -p PORT labremote@10.0.2.2
```

Use the port in `state.json`. No host-key verification bypass is needed. The remote login prints its actual TTY/PID and Unicode. To test continued interaction/resizing, run `stty size`, a controlled shell command and `stty size` again after resizing the terminal; verify the remote PID stays the same. Exit normally and confirm the local shell remains available. A server banner or a subprocess `ssh` probe is not a substitute for this real-terminal check.

After capture, remove only the guest `/tmp/v3-ssh/` fixture files and run:

```sh
python3 prototype/terminal/ssh-fixture/lab.py stop
```

Cleanup checks the exact labelled container identity, removes only that owned container and generated key files, and retains nonsecret state/log evidence. It never stops an unrelated container or modifies host SSH settings. `status` is read-only. The launcher refuses to overwrite existing fixture state.
