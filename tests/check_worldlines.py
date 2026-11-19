#!/usr/bin/env python3
"""Tests for the worldline system. Runs entirely in temporary directories."""
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True      # importing the scripts must not create __pycache__ inside the source tree
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "config/includes.chroot"
ETC = OVERLAY / "etc/steins"
BIN = OVERLAY / "usr/local/bin"
sys.path.insert(0, str(OVERLAY / "usr/local/lib/steins"))
import steinslib as sl  # noqa: E402


class Env(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.env = {"STEINS_ETC_DIR": str(ETC), "STEINS_HOME": str(self.home),
                    "STEINS_STATE_DIR": str(self.home / "state"), "STEINS_FAST": "1",
                    "STEINS_NO_APPLY": "1", "PATH": os.environ["PATH"], "PYTHONDONTWRITEBYTECODE": "1"}
        self._saved = {k: os.environ.get(k) for k in self.env}
        self._saved["DISPLAY"] = os.environ.get("DISPLAY")
        os.environ.update(self.env)
        os.environ.pop("DISPLAY", None)

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def run_bin(self, name, *args, stdin=None):
        return subprocess.run([sys.executable, str(BIN / name), *args], input=stdin, text=True,
                              capture_output=True, env={**self.env}, timeout=30)


class Numbers(Env):
    def test_normalize(self):
        self.assertEqual(sl.normalize("1.048596"), "1.048596")
        self.assertEqual(sl.normalize("1"), "1.000000")
        self.assertEqual(sl.normalize("5.5"), "5.500000")        # last band is valid now (span 6)
        self.assertEqual(sl.normalize("6.5"), "0.500000")        # wraps
        self.assertEqual(sl.normalize("-0.5"), "5.500000")       # wraps
        self.assertEqual(sl.normalize("0"), "0.000001")          # never exactly zero
        with self.assertRaises(ValueError):
            sl.normalize("abc")
        with self.assertRaises(ValueError):
            sl.normalize("NaN")


class Packs(Env):
    def test_packs_valid_and_cover_range(self):
        packs = sl.load_packs()
        self.assertGreaterEqual(len(packs), 6)
        ids = [p.id for p in packs]
        self.assertEqual(len(ids), len(set(ids)))
        for p in packs:
            self.assertTrue(p.contains(p.divergence), p.id)
            self.assertTrue(p.wallpaper_path().is_file(), p.id)
            ET.parse(p.wallpaper_path())
            for key in sl.REQUIRED_PALETTE:
                self.assertRegex(p.palette[key], r"^#[0-9a-fA-F]{6}$")
            self.assertEqual(len(p.terminal_palette), 16)
        for x in ("0.000001", "0.5", "1.0", "2.5", "3.999999", "4.0", "4.999999", "5.0", "5.999999"):
            self.assertTrue(any(p.contains(x) for p in packs), "gap at " + x)
        ranges = sorted((p.low, p.high) for p in packs)
        for (a, b), (c, d) in zip(ranges, ranges[1:]):
            self.assertLess(b, c, "overlapping ranges")

    def test_pick(self):
        self.assertEqual(sl.pick_pack("1.048596").id, "steins-gate")
        self.assertEqual(sl.pick_pack("0.571024").id, "alpha")
        self.assertEqual(sl.pick_pack("2.198306").id, "hinamizawa")
        self.assertEqual(sl.pick_pack("3.0721").id, "hitogashima")
        self.assertEqual(sl.pick_pack("4.250801").id, "lugunica")
        self.assertEqual(sl.pick_pack("5.093001").id, "mitakihara")

    def test_no_third_party_imagery(self):
        for svg in ETC.glob("worldlines/*/wallpaper.svg"):
            text = svg.read_text()
            self.assertNotIn("<image", text)
            self.assertNotIn("http://", text.replace("http://www.w3.org/2000/svg", ""))


class State(Env):
    def test_state_roundtrip_and_default(self):
        self.assertEqual(sl.get_divergence(), "1.048596")
        self.assertEqual(sl.set_divergence("2.5"), "2.500000")
        self.assertEqual(sl.get_divergence(), "2.500000")
        sl.state_file().write_text("garbage")
        self.assertEqual(sl.get_divergence(), "1.048596")

    def test_dmail(self):
        a = sl.dmail_delta("hello past")
        self.assertEqual(a, sl.dmail_delta("  HELLO PAST "))
        self.assertTrue(Decimal(-2) <= a <= Decimal(2))
        self.assertNotEqual(a, sl.dmail_delta("something else"))
        self.assertTrue(Decimal("0") < Decimal(sl.send_dmail("x", "5.9")) < Decimal(6))

    def test_codes(self):
        self.assertEqual(sl.lookup_code("el  psy kongroo"), "1.048596")
        self.assertEqual(sl.lookup_code("cicada"), "2.198306")
        self.assertIsNone(sl.lookup_code("not a code"))
        for v in json.loads((ETC / "codes.json").read_text())["codes"].values():
            sl.normalize(v)


class Apply(Env):
    def test_current_terminal_uses_xfconf(self):
        pack = sl.pick_pack("2.198306")
        with patch.dict(os.environ, {"DISPLAY": ":0"}), patch.object(sl.shutil, "which", return_value="/usr/bin/xfconf-query"), patch.object(sl.subprocess, "run") as run:
            sl._write_terminal(pack, self.home, False)
        calls = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(calls), 10)
        background = next(c for c in calls if "/color-background" in c)
        self.assertEqual(background[-1], pack.palette["bg_alt"])
        self.assertTrue(all("xfce4-terminal" in c for c in calls))
        by_property = {c[c.index("-p") + 1]: c for c in calls}
        self.assertEqual(by_property["/color-selection-background"][-1], pack.palette["selection"])
        self.assertEqual(by_property["/tab-activity-color"][-1], pack.palette["accent"])
        self.assertEqual(by_property["/color-cursor-foreground"][-1], pack.palette["bg_alt"])
        # Booleans are typed as xfconf booleans, everything else as strings.
        self.assertEqual(by_property["/color-selection-use-default"][-4:], ["-t", "bool", "-s", "false"])
        self.assertEqual(by_property["/color-cursor-use-default"][-4:], ["-t", "bool", "-s", "false"])
        self.assertEqual(by_property["/color-palette"][-4:-2], ["-t", "string"])

    def test_apply_writes_user_files(self):
        term = self.home / ".config/xfce4/terminal/terminalrc"
        term.parent.mkdir(parents=True)
        term.write_text("[Configuration]\nFontName=Foo 11\nColorBackground=#000000\n")
        css = self.home / ".config/gtk-3.0/gtk.css"
        css.parent.mkdir(parents=True)
        css.write_text("/* user's own css */\n")
        pack = sl.pick_pack("2.198306")
        notes = sl.apply_pack(pack)
        self.assertTrue(sl.state_file().is_file())
        self.assertTrue(notes)
        self.assertIn(pack.palette["selection"], css.read_text())
        self.assertIn("steins-worldline:hinamizawa", css.read_text())
        self.assertIn("/* user's own css */", css.read_text())   # user CSS stays in the live file
        t = term.read_text()
        self.assertIn("FontName=Foo 11", t)                       # untouched keys kept
        self.assertIn("ColorBackground=" + pack.palette["bg_alt"], t)
        self.assertIn("ColorCursor=" + pack.palette["accent"], t)
        self.assertIn("ColorSelectionBackground=" + pack.palette["selection"], t)
        self.assertIn("TabActivityColor=" + pack.palette["accent"], t)
        self.assertEqual(t.count("ColorBackground="), 1)           # replaced, never duplicated
        self.assertIn("vte-terminal { padding:", css.read_text())   # terminal margin follows the user block
        conky = (self.home / ".config/steins/conky.conf").read_text()
        self.assertNotIn("1.048596", conky)
        self.assertIn("cat " + str(sl.state_file()), conky)
        self.assertIn(pack.palette["accent"].lstrip("#").upper(), conky)

    def test_dry_run_writes_nothing(self):
        sl.apply_pack(sl.pick_pack("3.2"), dry_run=True)
        self.assertEqual(list(self.home.rglob("*")), [])


class Commands(Env):
    def test_set_dry_run_preserves_state(self):
        result = self.run_bin("steins-worldline", "set", "2.198306", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(sl.state_file().exists())
        sl.set_divergence("1.048596")
        result = self.run_bin("steins-worldline", "set", "2.198306", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sl.get_divergence(), "1.048596")

    def test_cli(self):
        r = self.run_bin("steins-worldline", "set", "0.571024", "--no-apply")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Alpha", r.stdout)
        self.assertEqual(self.run_bin("steins-worldline", "get", "--number").stdout.strip(), "0.571024")
        self.assertEqual(self.run_bin("steins-worldline", "id").stdout.strip(), "alpha")
        self.assertIn("steins-gate", self.run_bin("steins-worldline", "list").stdout)
        self.assertEqual(self.run_bin("steins-worldline", "set", "nope").returncode, 2)
        self.assertEqual(self.run_bin("steins-worldline", "apply", "--dry-run").returncode, 0)

    def test_dmail_command(self):
        self.assertEqual(self.run_bin("dmail", stdin="").returncode, 2)
        r = self.run_bin("dmail", "hello", "past")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("D-Mail sent", r.stdout)
        self.assertNotEqual(sl.get_divergence(), "1.048596")

    def test_ibm5100_session(self):
        script = "help\nlist\ncicada\nbogus\ndmail hello\nset 3.1\ndivergence\nexit\n"
        r = self.run_bin("ibm5100", stdin=script)
        self.assertEqual(r.returncode, 0, r.stderr)
        for needle in ("SYNTAX ERROR", "CODE ACCEPTED", "WORLDLINE SHIFT DETECTED", "HITOGASHIMA", "CLOSED"):
            self.assertIn(needle, r.stdout)
        self.assertEqual(sl.get_divergence(), "3.100000")

    def test_ibm5100_eof_is_clean(self):
        self.assertEqual(self.run_bin("ibm5100", stdin="").returncode, 0)


# ---------------------------------------------------------------------------
# Regression tests for bugs found in review (see docs/CLAUDE-CHANGES.md, R1-R10)
# ---------------------------------------------------------------------------
import shutil  # noqa: E402
import stat  # noqa: E402
import importlib.machinery  # noqa: E402
import importlib.util  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 300


def load_script(name):
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(BIN / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class PackCopy(Env):
    """Env with a private, editable copy of the packs."""
    def setUp(self):
        super().setUp()
        self.packs = self.home / "packs"
        shutil.copytree(ETC / "worldlines", self.packs)
        os.environ["STEINS_WORLDLINES_DIR"] = str(self.packs)
        self.env["STEINS_WORLDLINES_DIR"] = str(self.packs)
        self._saved["STEINS_WORLDLINES_DIR"] = None

    def edit(self, pack_id, **changes):
        f = self.packs / pack_id / "worldline.json"
        data = json.loads(f.read_text())
        for key, val in changes.items():
            if key.startswith("palette."):
                data["palette"][key[8:]] = val
            else:
                data[key] = val
        f.write_text(json.dumps(data))


class NumberHardening(Env):
    def test_R1_huge_or_odd_numbers_raise_valueerror_not_arithmetic_errors(self):
        for bad in ("1e100", "9" * 40, "1_0", "inf", "-Infinity", "1e5", "", " ", "1.2.3", "0x10", "١٢"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                sl.normalize(bad)
        self.assertEqual(sl.normalize(" +2.5 "), "2.500000")
        self.assertEqual(sl.normalize(".5"), "0.500000")
        self.assertEqual(sl.normalize(3), "3.000000")
        self.assertEqual(sl.normalize(Decimal("1.5")), "1.500000")
        self.assertEqual(sl.normalize("999999999999"[:11]), sl.normalize("99999999999"))   # large but legal

    def test_R1_cli_and_terminal_do_not_traceback(self):
        r = self.run_bin("steins-worldline", "set", "1e100")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)
        r = self.run_bin("ibm5100", stdin="set 1e100\nset 9999999999999999999999999999999999\nexit\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count("INVALID NUMBER"), 2)
        self.assertFalse(sl.state_file().exists())


class PackHardening(PackCopy):
    def test_nonfinite_ranges_are_skipped_without_crashing_other_packs(self):
        for value in ("NaN", "sNaN", "Infinity", "-Infinity"):
            for bounds in ([value, 1], [0, value]):
                self.edit("alpha", range=bounds)
                self.assertEqual(len(sl.load_packs()), 5)
                self.assertIn("finite", " ".join(sl.pack_errors()))
                result = self.run_bin("steins-worldline", "list")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_R2_corrupt_and_incomplete_packs_are_skipped_not_fatal(self):
        (self.packs / "zz-broken").mkdir()
        (self.packs / "zz-broken" / "worldline.json").write_text("{not json")
        (self.packs / "zz-partial").mkdir()
        (self.packs / "zz-partial" / "worldline.json").write_text(json.dumps({"id": "zz-partial"}))
        packs = sl.load_packs()
        self.assertEqual(len(packs), 6)
        problems = " ".join(sl.pack_errors())
        self.assertIn("zz-broken", problems)
        self.assertIn("zz-partial", problems)
        self.assertEqual(sl.pick_pack("2.5").id, "hinamizawa")
        r = self.run_bin("steins-worldline", "list")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("skipped pack zz-broken", r.stderr)

    def test_R4_hostile_pack_data_is_rejected(self):
        for field, value in (("id", "../../escape"), ("id", "Upper"), ("id", "a b"), ("id", ""), ("id", "alpha\n"),
                             ("palette.accent", "red; } * { display:none } x {"), ("palette.bg", "#12345"), ("palette.bg", "#123456\n"),
                             ("wallpaper", "../../etc/passwd.svg"), ("wallpaper", "x.png"),
                             ("range", [3, 1]), ("range", [-1, 2]), ("range", [0, 99]), ("range", "abc")):
            shutil.rmtree(self.packs); shutil.copytree(ETC / "worldlines", self.packs)
            self.edit("alpha", **{field: value})
            self.assertNotIn("alpha", [p.id for p in sl.load_packs()], (field, value))
            self.assertEqual(len(sl.load_packs()), 5)

    def test_names_are_sanitised_for_conky_and_terminal(self):
        self.edit("alpha", name="Al${exec rm -rf ~}]] pha\x1b[31m", tagline="x\n$(evil)")
        pack = [p for p in sl.load_packs() if p.id == "alpha"][0]
        for bad in "$[]{}()\x1b\n":
            self.assertNotIn(bad, pack.name + pack.tagline)

    def test_bad_terminal_palette_is_dropped_not_fatal(self):
        self.edit("alpha", terminal_palette=["#fff"] * 3)
        pack = [p for p in sl.load_packs() if p.id == "alpha"][0]
        self.assertEqual(pack.terminal_palette, [])
        self.assertIn("terminal_palette", " ".join(sl.pack_errors()))

    def test_duplicate_ids_and_missing_wallpaper_are_skipped(self):
        shutil.copytree(self.packs / "alpha", self.packs / "alpha-copy")
        (self.packs / "lugunica" / "wallpaper.svg").unlink()
        ids = [p.id for p in sl.load_packs()]
        self.assertEqual(ids.count("alpha"), 1)
        self.assertNotIn("lugunica", ids)

    def test_R9_no_packs_is_a_clean_failure(self):
        shutil.rmtree(self.packs)
        for args in (("apply", "--quiet"), ("list",), ("id",), ("set", "2.5")):
            r = self.run_bin("steins-worldline", *args)
            self.assertEqual(r.returncode, 3, args)
            self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(self.run_bin("steins-worldline", "get").returncode, 0)


class CodeHardening(Env):
    def test_R3_one_bad_code_does_not_disable_the_rest(self):
        etc = self.home / "etc"
        shutil.copytree(ETC, etc)
        data = json.loads((etc / "codes.json").read_text())
        data["codes"]["BROKEN"] = "not-a-number"
        data["codes"]["HUGE"] = "1e99"
        (etc / "codes.json").write_text(json.dumps(data))
        os.environ["STEINS_ETC_DIR"] = str(etc)
        self.assertEqual(sl.lookup_code("cicada"), "2.198306")
        self.assertIsNone(sl.lookup_code("broken"))
        for junk in ('[1, 2]', '"text"', '{"codes": []}', "{oops"):
            (etc / "codes.json").write_text(junk)
            self.assertEqual(sl.load_codes(), {}, junk)


class ApplyHardening(PackCopy):
    def test_R5_a_failing_step_never_aborts_the_rest(self):
        pack = sl.pick_pack("2.5")
        with patch.object(sl, "_write_terminal", side_effect=RuntimeError("boom")):
            result = sl.apply_pack(pack)
        self.assertFalse(result.ok)
        steps = [s[0] for s in result.steps]
        self.assertEqual(steps[-1], "conky")                       # the monitor is always attempted last
        self.assertIn("gtk", steps)
        self.assertTrue((self.home / ".config/steins/conky.conf").is_file())   # later steps still ran
        self.assertTrue(any("ERROR terminal: boom" == n for n in result))

    def test_R5_failed_xfconf_is_reported_with_exit_status(self):
        pack = sl.pick_pack("2.5")
        fail = type("P", (), {"returncode": 1, "stderr": "no daemon", "stdout": ""})()
        with patch.dict(os.environ, {"DISPLAY": ":0"}), patch.object(sl.shutil, "which", return_value="/usr/bin/x"), \
                patch.object(sl.subprocess, "run", return_value=fail), patch.object(sl.subprocess, "Popen"), \
                patch.object(sl, "_png_for", return_value=Path("/tmp/x.png")), patch.object(sl, "_monitor_outputs", return_value=["eDP-1"]):
            result = sl.apply_pack(pack)
        failed = {s[0] for s in result.steps if not s[1]}
        self.assertTrue({"terminal", "wallpaper", "panel"} <= failed, failed)
        self.assertEqual(result.steps[-1][0], "conky")                  # still attempted
        self.assertTrue((self.home / ".config/gtk-3.0/gtk.css").is_file())

    def test_wallpaper_without_monitors_is_an_error_not_a_silent_success(self):
        with patch.dict(os.environ, {"DISPLAY": ":0"}), patch.object(sl.shutil, "which", return_value="/usr/bin/x"), \
                patch.object(sl, "_monitor_outputs", return_value=[]):
            with self.assertRaises(RuntimeError):
                sl._set_wallpaper(Path("/tmp/x.png"), False)

    def test_R9_unwritable_home_is_reported_not_raised(self):
        with patch.object(sl, "atomic_write", side_effect=PermissionError("read-only file system")):
            result = sl.apply_pack(sl.pick_pack("2.5"))
        self.assertFalse(result.ok)
        self.assertGreaterEqual(len(result.errors), 3)

    def test_cli_apply_reports_failures_on_stderr_even_when_quiet(self):
        shutil.copy(ETC / "conky.conf", self.home / "conky.conf")
        r = self.run_bin("steins-worldline", "apply", "--quiet")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def _fake_rsvg(self, body):
        fakebin = self.home / "fakebin"
        fakebin.mkdir(exist_ok=True)
        script = fakebin / "rsvg-convert"
        script.write_text('#!/bin/sh\nwhile [ $# -gt 0 ]; do [ "$1" = "-o" ] && out="$2"; shift; done\n' + body)
        script.chmod(script.stat().st_mode | stat.S_IEXEC)
        os.environ["PATH"] = str(fakebin) + os.pathsep + os.environ["PATH"]

    def test_R6_failed_render_leaves_no_cached_image(self):
        self._fake_rsvg('printf PARTIAL > "$out"\nexit 1\n')
        pack = sl.pick_pack("2.5")
        with self.assertRaises(RuntimeError):
            sl._png_for(pack, self.home, False)
        cache = self.home / ".cache/steins"
        self.assertEqual([p.name for p in cache.glob("*.png")], [])
        self.assertEqual(list(cache.glob(".render-*")), [])         # temp file cleaned up too
        self._fake_rsvg('printf PARTIAL > "$out"\nexit 0\n')         # "succeeds" but writes garbage
        with self.assertRaises(RuntimeError):
            sl._png_for(pack, self.home, False)
        self.assertEqual([p.name for p in cache.glob("*.png")], [])

    def test_R6_cache_is_keyed_by_content_not_timestamp(self):
        counter = self.home / "calls"
        png = PNG.decode("latin-1")
        self._fake_rsvg("echo x >> %s\nprintf '\\211PNG\\r\\n\\032\\n' > \"$out\"\nhead -c 300 /dev/zero >> \"$out\"\nexit 0\n" % counter)
        pack = sl.pick_pack("2.5")
        first = sl._png_for(pack, self.home, False)
        os.utime(pack.wallpaper_path(), (1500000000, 1500000000))     # clock skew / old mtime
        second = sl._png_for(pack, self.home, False)
        self.assertEqual(first, second)
        self.assertEqual(counter.read_text().count("x"), 1)           # rendered once
        pack.wallpaper_path().write_text(pack.wallpaper_path().read_text() + "<!-- changed -->")
        third = sl._png_for(pack, self.home, False)
        self.assertNotEqual(first, third)                             # new content -> new file
        self.assertFalse(first.exists())                              # stale render removed

    def test_R7_state_path_with_spaces_is_quoted_for_conky(self):
        spaced = self.home / "home with space" / "it's"
        os.environ["STEINS_HOME"] = str(spaced)
        os.environ.pop("STEINS_STATE_DIR")
        sl.apply_pack(sl.pick_pack("2.5"))
        line = [l for l in (spaced / ".config/steins/conky.conf").read_text().splitlines() if "execi" in l][0]
        import shlex, re as _re
        command = _re.search(r"\$\{execi 2 (.*?)\}\$\{font", line).group(1)
        self.assertEqual(shlex.split(command), ["cat", str(spaced / ".local/state/steins/divergence")])

    def test_R8_user_gtk_css_is_preserved_and_block_replaced_in_place(self):
        css = self.home / ".config/gtk-3.0/gtk.css"
        css.parent.mkdir(parents=True)
        css.write_text("/* mine */\nbutton { color: pink; }\n")
        sl.apply_pack(sl.pick_pack("2.5"))
        sl.apply_pack(sl.pick_pack("2.5"))                            # idempotent
        text = css.read_text()
        self.assertTrue(text.startswith("/* mine */\nbutton { color: pink; }\n"))
        self.assertEqual(text.count(sl.CSS_BEGIN), 1)
        css.write_text(text + "\n/* added later */\nwindow { border-radius: 0; }\n")
        sl.apply_pack(sl.pick_pack("0.5"))                            # different worldline
        text = css.read_text()
        self.assertIn("steins-worldline:alpha", text)
        self.assertNotIn("steins-worldline:hinamizawa", text)
        self.assertIn("window { border-radius: 0; }", text)           # the later user edit survives
        self.assertEqual(text.count(sl.CSS_BEGIN), 1)
        self.assertFalse(list(css.parent.glob("*.steins-backup")))

    def test_gtk_css_old_format_is_migrated_and_unterminated_block_is_left_alone(self):
        css = self.home / ".config/gtk-3.0/gtk.css"
        css.parent.mkdir(parents=True)
        css.write_text("/* steins-worldline:higurashi -- generated, safe to delete */\nselection { color: red; }\n")
        sl.apply_pack(sl.pick_pack("2.5"))
        self.assertEqual(css.read_text().count(sl.CSS_BEGIN), 1)
        self.assertNotIn("higurashi", css.read_text())
        broken = sl.CSS_BEGIN + " -- steins-worldline:x */\nuser typed here\n"
        css.write_text(broken)
        result = sl.apply_pack(sl.pick_pack("2.5"))
        self.assertEqual(css.read_text(), broken)                     # refused to guess
        self.assertTrue(any(s[0] == "gtk" and not s[1] for s in result.steps))

    def test_terminalrc_with_invalid_encoding_is_left_untouched(self):
        term = self.home / ".config/xfce4/terminal/terminalrc"
        term.parent.mkdir(parents=True)
        term.write_bytes(b"[Configuration]\nFontName=\xff\xfe\n")
        result = sl.apply_pack(sl.pick_pack("2.5"))
        self.assertEqual(term.read_bytes(), b"[Configuration]\nFontName=\xff\xfe\n")
        self.assertTrue(any(s[0] == "terminal" and not s[1] for s in result.steps))

    def test_state_writes_are_atomic_and_leave_no_temp_files(self):
        for value in ("1.5", "2.5", "3.5"):
            sl.set_divergence(value)
        self.assertEqual([p.name for p in sl.state_dir().iterdir()], ["divergence"])
        with patch.object(sl.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                sl.set_divergence("4.5")
        self.assertEqual(sl.get_divergence(), "3.500000")
        self.assertEqual([p.name for p in sl.state_dir().iterdir()], ["divergence"])

    def test_dry_run_still_writes_nothing_with_new_steps(self):
        result = sl.apply_pack(sl.pick_pack("4.5"), dry_run=True)
        self.assertTrue(result.ok)
        stray = [q for q in self.home.rglob("*") if q != self.packs and self.packs not in q.parents]
        self.assertEqual(stray, [])


class TerminalHardening(Env):
    def test_R10_interrupt_during_a_command_returns_to_the_prompt(self):
        module = load_script("ibm5100")
        answers = iter(["divergence", "exit"])
        calls = []

        def fake_handle(line):
            calls.append(line)
            if len(calls) == 1:
                raise KeyboardInterrupt
            return False

        with patch.object(module, "handle", fake_handle), patch("builtins.input", lambda *_: next(answers)):
            module.main()                                              # must not raise
        self.assertEqual(calls, ["divergence", "exit"])

    def test_system_faults_are_reported_not_traceback(self):
        module = load_script("ibm5100")
        with patch.object(module, "handle", side_effect=RuntimeError("no usable worldline packs")), \
                patch("builtins.input", side_effect=["x", EOFError]):
            module.main()

    def test_terminal_shows_friendly_steps_not_paths(self):
        os.environ.pop("STEINS_NO_APPLY", None)
        self.env.pop("STEINS_NO_APPLY", None)
        r = self.run_bin("ibm5100", stdin="cicada\nexit\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("INTERFACE TINT", r.stdout)
        self.assertNotIn("/HOME", r.stdout.upper().replace(str(self.home).upper(), ""))
        self.assertNotIn(str(self.home), r.stdout)

    def test_boot_shows_current_worldline(self):
        sl.set_divergence("5.093001")
        r = self.run_bin("ibm5100", stdin="exit\n")
        self.assertIn("WORLDLINE ............ MITAKIHARA  5.093001", r.stdout)


class MeterLogic(Env):
    def setUp(self):
        super().setUp()
        sys.path.insert(0, str(OVERLAY / "usr/local/lib/steins"))
        import meterlib
        self.m = meterlib

    def test_glyphs(self):
        self.assertEqual(self.m.glyphs("1.048596"), list("1.048596"))
        for bad in ("1.04859", "10.48596", "a.048596", "1,048596", ""):
            with self.assertRaises(ValueError):
                self.m.glyphs(bad)

    def test_flicker_settles_left_to_right_on_the_new_value(self):
        import random
        frames = self.m.flicker_frames("1.048596", "5.093001", frames=15, rng=random.Random(7))
        self.assertEqual(len(frames), 15)
        self.assertEqual(frames[0][0], "1")                           # starts from the old reading
        self.assertEqual(frames[-1], "5.093001")
        self.assertTrue(all(len(f) == 8 and f[1] == "." for f in frames))
        locked = [sum(1 for k in range(8) if f[k] == "5.093001"[k]) for f in frames]
        self.assertEqual(frames[-2][:1], "5")                         # leftmost tube settles first
        self.assertEqual(self.m.flicker_frames("1.048596", "1.048596", frames=2)[-1], "1.048596")

    def test_css_and_accessible_text(self):
        pack = sl.pick_pack("1.048596")
        css = self.m.css_for(pack.palette)
        self.assertIn(pack.palette["accent"], css)
        self.assertEqual(css.count("{"), css.count("}"))
        self.assertEqual(self.m.accessible_text("1.048596", "Steins Gate"), "Divergence 1 point 048596. Worldline: Steins Gate.")
        self.assertIn("unknown", self.m.accessible_text("1.048596", None))


class ArtworkContract(unittest.TestCase):
    def test_wallpapers_have_no_baked_number_and_keep_the_title_top_left(self):
        import re
        for svg in ETC.glob("worldlines/*/wallpaper.svg"):
            text = svg.read_text()
            self.assertIsNone(re.search(r">\d\.\d{6}<", text), svg.parent.name)      # live number lives in conky/meter
            self.assertIn('y="274"', text)                                            # title block y (clear of login box)
            self.assertNotIn("<filter", text)

    def test_base_wallpaper_is_generated_from_the_steins_gate_pack(self):
        sys.path.insert(0, str(ROOT / "build-tools"))
        import generate_worldlines as g
        base = (OVERLAY / "usr/share/backgrounds/steins/worldline.svg").read_text()
        self.assertEqual(base, g.wallpaper(next(w for w in g.WORLDLINES if w["id"] == "steins-gate")))
        for w in g.WORLDLINES:
            self.assertEqual((ETC / "worldlines" / w["id"] / "wallpaper.svg").read_text(), g.wallpaper(w), w["id"])

    def test_generator_manifest_matches_pack_folders(self):
        sys.path.insert(0, str(ROOT / "build-tools"))
        import generate_worldlines as g
        self.assertEqual(sorted(p.name for p in (ETC / "worldlines").iterdir()), sorted(w["id"] for w in g.WORLDLINES))

    def test_panel_default_is_graphite_and_session_has_a_monitor_fallback(self):
        xml = (OVERLAY / "etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml").read_text()
        self.assertIn('name="background-style" type="uint" value="1"', xml)
        self.assertIn("background-rgba", xml)
        session = (BIN / "steins-session").read_text()
        self.assertIn("pgrep", session)
        self.assertNotIn("sleep 6", (OVERLAY / "etc/xdg/autostart/steins-worldline.desktop").read_text())   # no competing startup



if __name__ == "__main__":
    unittest.main(verbosity=2)
