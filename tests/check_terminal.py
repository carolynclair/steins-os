#!/usr/bin/env python3
"""Everyday terminal contracts: default profile, window styling, prompt and steins-info.

The prompt tests drive a real interactive Bash on a pseudo-terminal with a
temporary HOME. Nothing is installed and no user or system file is touched.
"""
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "config/includes.chroot"
PROMPT = OVERLAY / "usr/share/steins/shell/prompt.bash"
PROFILE = OVERLAY / "etc/profile.d/steins.sh"
INFO = OVERLAY / "usr/local/bin/steins-info"
SKEL_RC = OVERLAY / "etc/skel/.config/xfce4/terminal/terminalrc"
sys.path.insert(0, str(OVERLAY / "usr/local/lib/steins"))
os.environ.setdefault("STEINS_ETC_DIR", str(OVERLAY / "etc/steins"))
import steinslib as sl  # noqa: E402

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)")
# Debian 13's /etc/skel/.bashrc prompt for xterm-256color, title prefix included.
# The title prefix is assigned in double quotes there, so ${debian_chroot} is already expanded.
DEBIAN_PS1 = (r"\[\e]0;\u@\h: \w\a\]"
              r"${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ ")


def bash_supports_arrays():
    out = subprocess.run(["bash", "-c", "echo ${BASH_VERSINFO[0]}.${BASH_VERSINFO[1]}"],
                         capture_output=True, text=True).stdout.strip()
    major, minor = (int(x) for x in out.split("."))
    return (major, minor) >= (5, 1)


class Shell:
    """An interactive Bash on a PTY whose rc file mimics profile.d then ~/.bashrc."""

    def __init__(self, home, rc_lines, env=None):
        self.home = Path(home)
        rc = self.home / "rc.bash"
        rc.write_text("\n".join(rc_lines) + "\n")
        environment = {"HOME": str(self.home), "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                       "TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        environment.update(env or {})
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(str(self.home))
            os.execvpe("bash", ["bash", "--noprofile", "--rcfile", str(rc), "-i"], environment)
        self.pid, self.fd, self.buffer = pid, fd, b""

    def read_until(self, token, timeout=10):
        end = time.time() + timeout
        while token.encode() not in self.buffer:
            remaining = end - time.time()
            if remaining <= 0:
                raise AssertionError("timed out waiting for %r; got %r" % (token, self.buffer[-600:]))
            ready, _, _ = select.select([self.fd], [], [], remaining)
            if ready:
                try:
                    chunk = os.read(self.fd, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                self.buffer += chunk
        return self.buffer.decode("utf-8", "replace")

    def run(self, command, marker):
        """Send command; wait until marker is printed. The marker is quoted in
        the typed line ('MA'RKER) so the terminal's echo of input cannot match."""
        assert marker in command
        command = command.replace(marker, "'%s'%s" % (marker[:2], marker[2:]))
        start = len(self.buffer)
        os.write(self.fd, (command + "\n").encode())
        self.read_until(marker)
        # Wait for the next prompt to be printed after the marker.
        time.sleep(0.15)
        self._drain()
        return self.buffer[start:].decode("utf-8", "replace")

    def _drain(self):
        while True:
            ready, _, _ = select.select([self.fd], [], [], 0.2)
            if not ready:
                return
            try:
                chunk = os.read(self.fd, 65536)
            except OSError:
                return
            if not chunk:
                return
            self.buffer += chunk

    def close(self):
        try:
            os.write(self.fd, b"exit\n")
            os.waitpid(self.pid, 0)
        except OSError:
            pass
        os.close(self.fd)

    def text(self):
        return self.buffer.decode("utf-8", "replace")


class PromptBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.shells = []

    def tearDown(self):
        for shell in self.shells:
            shell.close()
        self.tmp.cleanup()

    def shell(self, bashrc_ps1=DEBIAN_PS1, before=(), after=(), env=None):
        lines = list(before) + [". %s" % PROMPT]
        if bashrc_ps1 is not None:          # what ~/.bashrc does after profile.d
            lines.append("PS1=%s" % shlex_quote(bashrc_ps1))
        lines += list(after)
        shell = Shell(self.home, lines, env)
        self.shells.append(shell)
        shell.run("echo READY", "READY")
        return shell

    def state(self, shell):
        out = shell.run('echo STATE"<$__steins_prompt_state>"', "STATE")
        return re.search(r"STATE<([a-z]*)>", ANSI.sub("", out)).group(1)


GLYPH = "#" if os.geteuid() == 0 else "❯"      # the prompt marks root sessions


def shlex_quote(value):
    return "'" + value.replace("'", "'\"'\"'") + "'"


@unittest.skipUnless(shutil.which("bash") and bash_supports_arrays(), "needs Bash 5.1 or newer")
class Prompt(PromptBase):
    def test_debian_stock_prompt_is_adopted_with_greeting(self):
        shell = self.shell()
        self.assertEqual(self.state(shell), "on")
        plain = ANSI.sub("", shell.text())
        self.assertEqual(plain.count("Steins;OS"), 1, "greeting is printed once per shell")
        self.assertIn("steins-info", plain)
        self.assertIn("\x1b[33m", shell.text())         # accent = ANSI 3, recoloured by the worldline palette
        self.assertIn(GLYPH, plain)

    def test_plain_bash_prompt_is_adopted(self):
        self.assertEqual(self.state(self.shell(bashrc_ps1=r"${debian_chroot:+($debian_chroot)}\u@\h:\w\$ ")), "on")

    def test_customised_prompt_is_respected(self):
        shell = self.shell(bashrc_ps1="mine> ")
        self.assertEqual(self.state(shell), "off")
        self.assertIn("mine> ", shell.text())
        self.assertIn("Steins;OS", ANSI.sub("", shell.text()))   # greeting is independent of the prompt

    def test_opt_out_and_force(self):
        self.assertEqual(self.state(self.shell(env={"STEINS_PROMPT": "off"})), "off")
        self.assertEqual(self.state(self.shell(bashrc_ps1="mine> ", env={"STEINS_PROMPT": "on"})), "on")

    def test_greeting_opt_outs(self):
        shell = self.shell(env={"STEINS_GREETING": "off"})
        self.assertNotIn("Steins;OS", ANSI.sub("", shell.text()))
        (self.home / ".hushlogin").write_text("")
        shell = self.shell()
        self.assertNotIn("Steins;OS", ANSI.sub("", shell.text()))
        self.assertEqual(self.state(shell), "on")

    def test_greeting_reads_the_saved_divergence(self):
        state = self.home / ".local/state/steins"
        state.mkdir(parents=True)
        (state / "divergence").write_text("2.198306\n")
        self.assertIn("divergence 2.198306", ANSI.sub("", self.shell().text()))

    def test_failed_command_shows_status_then_clears(self):
        shell = self.shell()
        out = shell.run("(exit 3); echo DONE1", "DONE1")
        self.assertNotIn("exit 3", ANSI.sub("", out.split("DONE1", 1)[1]))   # the last command (echo) succeeded
        out = shell.run("echo DONE2; (exit 3)", "DONE2")
        prompt = out.split("DONE2", 1)[1]
        self.assertIn("exit 3", ANSI.sub("", prompt))
        self.assertIn("\x1b[31m" + GLYPH, prompt)        # chevron turns red
        out = shell.run("echo DONE3", "DONE3")
        self.assertNotIn("exit 3", ANSI.sub("", out.split("DONE3", 1)[1]))

    def test_long_command_reports_duration(self):
        shell = self.shell()
        # Assigning SECONDS moves bash's clock; the PS0 timer then sees 75 s pass instantly.
        out = shell.run("echo DONE; SECONDS=75", "DONE")
        self.assertIn("took 1m 15s", ANSI.sub("", out))
        out = shell.run("echo AGAIN", "AGAIN")
        self.assertNotIn("took", ANSI.sub("", out.split("AGAIN", 1)[1]))

    def test_git_branch_detached_head_and_worktree_file(self):
        repo = self.home / "repo"
        (repo / ".git").mkdir(parents=True)
        (repo / ".git/HEAD").write_text("ref: refs/heads/feature/terminal\n")
        (repo / "src/deep").mkdir(parents=True)
        shell = self.shell()
        out = shell.run("cd ~/repo/src/deep && echo IN", "IN")
        self.assertIn("on feature/terminal", ANSI.sub("", out))
        (repo / ".git/HEAD").write_text("0123456789abcdef0123456789abcdef01234567\n")
        self.assertIn("on 0123456", ANSI.sub("", shell.run("echo DET", "DET")))
        linked = self.home / "linked"
        linked.mkdir()
        (self.home / "wt").mkdir()
        (self.home / "wt/HEAD").write_text("ref: refs/heads/side\n")
        (linked / ".git").write_text("gitdir: ../wt\n")
        self.assertIn("on side", ANSI.sub("", shell.run("cd ~/linked && echo WT", "WT")))
        out = shell.run("cd / && echo OUT", "OUT")
        self.assertNotIn(" on ", ANSI.sub("", out.split("OUT", 1)[1]))

    def test_coexists_with_vte_integration(self):
        # Debian's vte-2.91.sh appends to an array PROMPT_COMMAND and puts an
        # ESC-backslash terminated sequence in PS0 (it runs after steins.sh).
        vte = ["__vte_precmd() { :; }",
               'if [[ "$(declare -p PROMPT_COMMAND 2>&1)" =~ "declare -a" ]]; then PROMPT_COMMAND+=(__vte_precmd);'
               ' else PROMPT_COMMAND="__vte_precmd"; fi',
               r"""PS0='\e]133;C\e\\\r'"$(printf '\033]666;vte.shell.preexec!\033\\')" """]
        shell = Shell(self.home, [". %s" % PROMPT] + vte + ["PS1=%s" % shlex_quote(DEBIAN_PS1)])
        self.shells.append(shell)
        shell.run("echo READY", "READY")
        out = shell.run('declare -p PROMPT_COMMAND; echo PC_DONE', "PC_DONE")
        self.assertIn("__steins_prompt_hook", out)
        self.assertIn("__vte_precmd", out)
        self.assertNotIn("__steins_nil", shell.text())   # PS0 timer never leaks as text
        self.assertEqual(self.state(shell), "on")

    def test_existing_prompt_command_is_kept(self):
        shell = self.shell(before=["PROMPT_COMMAND='touch \"$HOME/pc-ran\"'"])
        shell.run("echo X", "X")
        self.assertTrue((self.home / "pc-ran").exists())
        self.assertEqual(self.state(shell), "on")

    def test_root_prompt_is_distinct(self):
        # EUID is read-only, so check the builder's root branch textually.
        text = PROMPT.read_text()
        self.assertIn("glyph='#'", text)
        self.assertIn(r"who='\[\e[31m\]\u@\h\[\e[0m\]'", text)


class NonInteractive(unittest.TestCase):
    def test_profile_snippet_is_silent_for_scripts_and_other_shells(self):
        for shell in ("sh", "bash"):
            if not shutil.which(shell):
                continue
            out = subprocess.run([shell, "-c", ". %s; echo ok; type __steins_prompt_hook >/dev/null 2>&1 && echo leaked" % PROFILE],
                                 capture_output=True, text=True, env={"PATH": os.environ["PATH"], "HOME": "/nonexistent"})
            self.assertEqual(out.stdout, "ok\n", shell)
            self.assertEqual(out.stderr, "", shell)

    def test_snippet_is_posix_sh(self):
        if shutil.which("dash"):
            subprocess.run(["dash", "-n", str(PROFILE)], check=True)
        subprocess.run(["bash", "-n", str(PROMPT)], check=True)


class Info(unittest.TestCase):
    def run_info(self, *args, env=None):
        with tempfile.TemporaryDirectory() as home:
            environment = {"PATH": os.environ["PATH"], "HOME": home, "TERM": "xterm-256color", "SHELL": "/bin/bash"}
            environment.update(env or {})
            result = subprocess.run(["sh", str(INFO), *args], capture_output=True, text=True, env=environment, timeout=30)
            self.assertEqual(list(Path(home).iterdir()), [], "steins-info must not write to HOME")
            return result

    def test_plain_output_is_readable_and_complete(self):
        result = self.run_info("--plain")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("\x1b", result.stdout)
        for label in ("OS", "Kernel", "Uptime", "Shell", "CPU", "Memory", "Disk /"):
            self.assertRegex(result.stdout, r"(?m)^  %s +\S" % re.escape(label))
        self.assertNotRegex(result.stdout, r"[▄▀█▌▐]")       # no emblem in plain mode

    def test_pipe_is_plain_and_options_are_checked(self):
        self.assertNotIn("\x1b", self.run_info().stdout)       # stdout is not a TTY here
        self.assertEqual(self.run_info("--help").returncode, 0)
        self.assertEqual(self.run_info("--bogus").returncode, 2)

    def test_colour_layout_on_a_terminal(self):
        with tempfile.TemporaryDirectory() as home:
            pid, fd = pty.fork()
            if pid == 0:
                os.execvpe("sh", ["sh", str(INFO)], {"PATH": os.environ["PATH"], "HOME": home,
                                                    "TERM": "xterm-256color", "SHELL": "/bin/bash"})
            data = b""
            while True:
                try:
                    chunk = os.read(fd, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                data += chunk
            os.waitpid(pid, 0)
            os.close(fd)
        out = data.decode("utf-8", "replace")
        plain = ANSI.sub("", out)
        self.assertIn("\x1b[33m", out)                 # accent from the worldline palette
        self.assertIn("\x1b[32G", out)                 # info column aligned by column move
        self.assertRegex(plain, r"[▄▀█]")              # emblem rendered
        self.assertNotRegex(plain, r"[rz][▄▀█▌▐▗▖▘▝▙▛▜▟]")   # colour markers never leak
        for i in range(8):
            self.assertIn("\x1b[4%dm" % i, out)        # palette swatches
            self.assertIn("\x1b[10%dm" % i, out)


class Profile(unittest.TestCase):
    def rc(self):
        lines = SKEL_RC.read_text().splitlines()
        self.assertEqual(lines[0], "[Configuration]")
        return dict(line.split("=", 1) for line in lines[1:] if line.strip())

    def test_default_profile_matches_default_worldline(self):
        rc = self.rc()
        default = sl.pick_pack((OVERLAY / "etc/steins/default-divergence").read_text().strip())
        self.assertEqual(rc["ColorBackground"], default.palette["bg_alt"])
        self.assertEqual(rc["ColorForeground"], default.palette["fg"])
        self.assertEqual(rc["ColorCursor"], default.palette["accent"])
        self.assertEqual(rc["ColorCursorForeground"], default.palette["bg_alt"])
        self.assertEqual(rc["ColorSelectionBackground"], default.palette["selection"])
        self.assertEqual(rc["TabActivityColor"], default.palette["accent"])
        self.assertEqual(rc["ColorPalette"].split(";"), default.terminal_palette)

    def test_default_profile_keeps_function(self):
        rc = self.rc()
        self.assertEqual(rc["CommandLoginShell"], "TRUE")     # profile.d (prompt, PATH) needs a login shell
        self.assertEqual(rc["MiscMenubarDefault"], "FALSE")
        self.assertTrue(rc["FontName"].startswith("JetBrains Mono "))
        self.assertGreaterEqual(int(rc["ScrollingLines"]), 10000)
        for key, value in rc.items():
            self.assertRegex(key, r"^[A-Z][A-Za-z]+$")
            if value in ("TRUE", "FALSE"):
                continue
            self.assertNotIn(" ;", value)

    def test_font_is_a_declared_debian_dependency(self):
        packages = (ROOT / "config/package-lists/steins.list.chroot").read_text().split()
        self.assertIn("fonts-jetbrains-mono", packages)
        self.assertIn("fonts-jetbrains-mono", (ROOT / "build-tools/build_packages.py").read_text())


class Styling(unittest.TestCase):
    def test_theme_rules_are_balanced_and_scoped(self):
        css = (ROOT / "packaging/theme-overrides.css").read_text()
        body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        self.assertEqual(body.count("{"), body.count("}"))
        terminal = body[body.index("#xfce4-terminal-notebook"):]
        for rule in re.findall(r"([^{}]+)\{", terminal):
            for selector in rule.split(","):
                self.assertIn("#xfce4-terminal-notebook", selector, "terminal rules must not restyle other apps")

    def test_every_world_styles_the_terminal(self):
        for pack in sl.load_packs():
            css = sl.gtk_css(pack)
            self.assertIn("vte-terminal { padding:", css)
            self.assertIn("tab:checked { background-color: %s; border-bottom-color: %s; }"
                          % (pack.palette["bg_alt"], pack.palette["accent"]), css)


if __name__ == "__main__":
    unittest.main(verbosity=2)
