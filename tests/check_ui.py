#!/usr/bin/env python3
"""UI-contract tests: field guide, About content, installer theme, palette contrast, ibm5100 LIST order.
Static/headless except the optional About construction test, which needs python3-gi and a display (xvfb-run)."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "config/includes.chroot"
ETC = OVERLAY / "etc/steins"
BIN = OVERLAY / "usr/local/bin"
sys.path.insert(0, str(OVERLAY / "usr/local/lib/steins"))
os.environ.setdefault("STEINS_ETC_DIR", str(ETC))
import aboutlib  # noqa: E402
import steinslib as sl  # noqa: E402

GUIDE = (OVERLAY / "usr/share/doc/steins-os/guide.html").read_text(encoding="utf-8")
HOOK = (ROOT / "config/hooks/live/0900-steins.hook.chroot").read_text()
CONFIGURE = (ROOT / "packaging/configure-system").read_text()
THEME_CSS = (ROOT / "packaging/theme-overrides.css").read_text()
QSS = (OVERLAY / "usr/share/steins/calamares/stylesheet.qss").read_text()
QML = (OVERLAY / "usr/share/steins/calamares/show.qml").read_text()
PACKS = [json.loads(p.read_text()) for p in sorted((ETC / "worldlines").glob("*/worldline.json"))]


def luminance(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


class Guide(unittest.TestCase):
    def test_lists_every_world_with_its_reference_number_and_accent(self):
        self.assertEqual(len(PACKS), 6)
        for p in PACKS:
            self.assertIn(p["name"], GUIDE)
            self.assertIn(p["divergence"], GUIDE)
            self.assertIn(p["palette"]["accent"], GUIDE, "swatch for %s is stale" % p["id"])

    def test_no_stale_three_wallpaper_text(self):
        self.assertNotIn("one of three", GUIDE.lower())

    def test_covers_the_required_topics(self):
        low = GUIDE.lower()
        for needle in ("ibm5100", "cicada", "d-mail", "local", "divergence meter", "reopen", "live usb",
                       "development preview", "decorative", "real"):
            self.assertTrue(needle in low, "guide is missing: " + needle)

    def test_has_no_invented_support_links_and_works_offline(self):
        self.assertNotIn("http://", GUIDE)
        self.assertNotIn("https://", GUIDE)
        self.assertNotRegex(GUIDE, r"(?i)<(script|link|img)\b[^>]*(src|href)=[\"']?https?:")

    def test_accessibility_basics(self):
        self.assertIn('lang="en"', GUIDE)
        self.assertIn("width=device-width", GUIDE)
        self.assertIn(":focus-visible", GUIDE)
        self.assertIn("skip", GUIDE)
        self.assertIn("prefers-color-scheme", GUIDE)
        self.assertEqual(len(re.findall(r"<h1", GUIDE)), 1)


class About(unittest.TestCase):
    def test_rows_are_ordered_by_divergence_and_cover_all_packs(self):
        packs = sl.load_packs()
        rows = aboutlib.worldline_rows(packs)
        self.assertEqual([r[1] for r in rows], ["0.x", "1.x", "2.x", "3.x", "4.x", "5.x"])
        self.assertEqual({r[0] for r in rows}, {p.name for p in packs})

    def test_os_release_parsing_and_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "os-release"
            f.write_text('NAME="X"\nPRETTY_NAME="Steins;OS 0.1 (Gate of Steiner)"\n')
            self.assertEqual(aboutlib.os_pretty_name(f), "Steins;OS 0.1 (Gate of Steiner)")
            self.assertIsNone(aboutlib.os_pretty_name(Path(d) / "missing"))

    def test_text_keeps_the_honesty_claims(self):
        self.assertIn("fictional", aboutlib.DMAIL)
        self.assertIn("local", aboutlib.DMAIL)
        self.assertIn("Not a production", aboutlib.STATUS)
        self.assertNotRegex(aboutlib.STATUS + aboutlib.DISCLAIMER, r"https?://")

    def test_summary_survives_no_pack(self):
        self.assertIn("no worldline pack", aboutlib.current_summary("1.048596", None))

    @unittest.skipUnless(shutil.which("xvfb-run"), "needs xvfb-run")
    def test_window_builds_and_closes_with_escape(self):
        code = ("import sys;sys.dont_write_bytecode=True\nimport importlib.machinery as m,importlib.util as u\n"
                "import gi;gi.require_version('Gtk','3.0');from gi.repository import Gtk,Gdk\n"
                "l=m.SourceFileLoader('a',%r);s=u.spec_from_loader('a',l);mod=u.module_from_spec(s);l.exec_module(mod)\n"
                "w=mod.About();w.show_all()\n"
                "assert w.get_focus().__class__.__name__=='Notebook',w.get_focus()\n"
                "e=Gdk.Event.new(Gdk.EventType.KEY_PRESS);e.keyval=Gdk.KEY_Escape\n"
                "assert w.on_key(w,e) is True\n"
                "w2=mod.About();w2.launch('x',['/nonexistent/binary']);assert 'Could not open' in w2.status.get_text()\n"
                "print('ok')\n") % str(BIN / "steins-about")
        try:
            import gi  # noqa: F401
        except ImportError:
            self.skipTest("python3-gi not installed")
        r = subprocess.run(["xvfb-run", "-a", sys.executable, "-c", code], capture_output=True, text=True, timeout=60,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ok", r.stdout)


class InstallerTheme(unittest.TestCase):
    def test_progress_text_remains_readable_over_the_fill(self):
        def rule(selector):
            return re.search(re.escape(selector) + r"\s*\{([^}]+)\}", QSS).group(1)
        bar, chunk = rule("QProgressBar"), rule("QProgressBar::chunk")
        fg = re.search(r"(?<![-\w])color:\s*(#[0-9a-f]{6})", bar).group(1)
        for body in (bar, chunk):
            bg = re.search(r"background-color:\s*(#[0-9a-f]{6})", body).group(1)
            self.assertGreaterEqual(contrast(fg, bg), 4.5, "percentage text on progress fill")

    def test_stylesheet_indicator_assets_are_shipped(self):
        for path in re.findall(r"url\((/[^)]+)\)", QSS):
            self.assertTrue((OVERLAY / path.lstrip("/")).is_file(), path)

    def test_stylesheet_is_balanced_and_covers_states(self):
        self.assertEqual(QSS.count("{"), QSS.count("}"))
        self.assertEqual(QSS.count("/*"), QSS.count("*/"))
        for state in ("QPushButton:disabled", "QPushButton:focus", "QPushButton:default", "QLineEdit:focus",
                      "QLineEdit:disabled", "QComboBox:disabled", "selection-background-color", "QListView::item:selected",
                      "QProgressBar::chunk", "QCheckBox:disabled"):
            self.assertIn(state, QSS, state)

    def test_stylesheet_text_pairs_meet_contrast(self):
        pairs = [("#e7e2d6", "#1b232a", 7), ("#151b20", "#e99a45", 7), ("#a9b3ad", "#1b232a", 4.5),
                 ("#98a39d", "#232d34", 4.5), ("#e7e2d6", "#11171b", 7), ("#e7e2d6", "#2a353d", 7)]
        for fg, bg, need in pairs:
            self.assertGreaterEqual(contrast(fg, bg), need, (fg, bg))
            self.assertIn(fg, QSS)
            self.assertIn(bg, QSS)

    def test_slideshow_is_original_honest_and_self_contained(self):
        self.assertIn("Presentation", QML)
        self.assertGreaterEqual(QML.count("Slide {"), 4)
        self.assertNotRegex(QML, r"https?://")
        self.assertNotIn("Debian GNU/Linux", QML)
        self.assertIn("development preview", QML.lower())
        self.assertEqual(QML.count("{"), QML.count("}"))

    def test_hook_wires_branding_without_inventing_links_or_changing_disk_modules(self):
        self.assertIn("supportUrl='', knownIssuesUrl='', releaseNotesUrl=''", CONFIGURE)
        self.assertIn("/usr/share/steins/calamares", CONFIGURE)
        self.assertIn("prompt-install", CONFIGURE)                # final confirmation preserved
        self.assertIn("calamares-install-debian", (BIN / "install-steins-os").read_text())
        for forbidden in ("partition.conf", "bootloader.conf", "sudoers"):
            self.assertNotIn(forbidden, CONFIGURE)

    def test_hook_selection_colours_are_readable(self):
        m = re.search(r"theme_selected_bg_color (#[0-9a-f]{6});\n@define-color theme_selected_fg_color (#[0-9a-f]{6});", THEME_CSS)
        self.assertTrue(m)
        self.assertGreaterEqual(contrast(m.group(1), m.group(2)), 4.5)
        self.assertIn("outline-width: 2px", THEME_CSS)             # visible keyboard focus
        self.assertIn("outline-color: #e99a45", THEME_CSS)
        self.assertIn("gtk-dark.css", CONFIGURE)                  # prefer-dark uses a separate stylesheet


class PaletteContrast(unittest.TestCase):
    def test_every_world_is_readable(self):
        for p in PACKS:
            c = p["palette"]
            self.assertGreaterEqual(contrast(c["fg"], c["bg"]), 7, p["id"])
            self.assertGreaterEqual(contrast(c["muted"], c["bg"]), 4.5, p["id"])
            self.assertGreaterEqual(contrast(c["accent"], c["bg"]), 3, p["id"])      # UI components/large text
            self.assertGreaterEqual(contrast("#ffffff", c["selection"]), 4.5, "%s selected text" % p["id"])


class Ibm5100List(unittest.TestCase):
    def test_list_is_ordered_by_divergence_not_folder_name(self):
        env = dict(os.environ, STEINS_FAST="1", STEINS_NO_APPLY="1", STEINS_ETC_DIR=str(ETC),
                   PYTHONDONTWRITEBYTECODE="1")
        with tempfile.TemporaryDirectory() as d:
            env.update(STEINS_HOME=d, STEINS_STATE_DIR=d + "/s")
            r = subprocess.run([sys.executable, str(BIN / "ibm5100")], input="LIST\nEXIT\n", capture_output=True,
                               text=True, env=env, timeout=30)
        names = [n for n in ("ALPHA", "STEINS GATE", "HINAMIZAWA", "HITOGASHIMA", "LUGUNICA", "MITAKIHARA")]
        listing = r.stdout.split("TYPE HELP FOR COMMANDS.")[-1]      # the boot banner also names the current world
        positions = [listing.find(n + " ") for n in names]
        self.assertTrue(all(p >= 0 for p in positions), listing)
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main(verbosity=2)
