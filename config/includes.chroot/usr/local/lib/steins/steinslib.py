"""Shared logic for the Steins;OS worldline system.

One divergence number (the state) selects one worldline pack (the theme).
Used by steins-worldline, ibm5100, dmail and steins-meter.

Design rules (see docs/CLAUDE-CHANGES.md):
  * Never raise out of apply_pack(): every step is isolated and reported, so one failing
    step cannot leave the session without its monitor or abort the rest of the theme.
  * Every file we write is written atomically (temp file + rename).
  * Pack data is untrusted input: ids, colours and names are validated before use.
  * The user's own gtk.css is preserved; we only manage a marked block inside it.

Test overrides (environment variables):
  STEINS_WORLDLINES_DIR  packs directory      (default /etc/steins/worldlines)
  STEINS_ETC_DIR         /etc/steins stand-in (default /etc/steins)
  STEINS_STATE_DIR       state directory      (default ~/.local/state/steins)
  STEINS_HOME            home stand-in        (default ~)
"""
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

DIVERGENCE_MIN = Decimal("0.000001")
DIVERGENCE_SPAN = Decimal("6")          # divergence lives in [0, 6): one integer band per worldline
MAX_INPUT = Decimal(10) ** 12           # larger inputs are rejected instead of wrapped
DEFAULT_DIVERGENCE = "1.048596"
MARKER = "steins-worldline"
CSS_BEGIN = "/* >>> steins-worldline BEGIN"
CSS_END = "/* <<< steins-worldline END"

_NUMBER_RE = re.compile(r"^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)$")   # ASCII digits only (\d also matches Arabic-Indic etc.)
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def etc_dir():
    return Path(os.environ.get("STEINS_ETC_DIR", "/etc/steins"))


def packs_dir():
    return Path(os.environ.get("STEINS_WORLDLINES_DIR", str(etc_dir() / "worldlines")))


def home_dir():
    return Path(os.environ.get("STEINS_HOME", str(Path.home())))


def state_dir():
    default = home_dir() / ".local" / "state" / "steins"
    return Path(os.environ.get("STEINS_STATE_DIR", str(default)))


def state_file():
    return state_dir() / "divergence"


# ------------------------------------------------------------ atomic files
def _default_mode():
    mask = os.umask(0)
    os.umask(mask)
    return 0o666 & ~mask


def atomic_write(path, text):
    """Write text to path atomically. An existing file keeps its permissions."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        mode = path.stat().st_mode & 0o777
    except OSError:
        mode = _default_mode()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix="." + path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _run(cmd, timeout=10):
    """Run a helper command. Returns (ok, message); never raises."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "timed out"
    except OSError as e:
        return False, str(e)
    rc = getattr(proc, "returncode", 0)
    if isinstance(rc, int) and rc != 0:
        err = proc.stderr if isinstance(proc.stderr, str) else ""
        return False, err.strip()[:100] or "exit status %d" % rc
    return True, ""


# ---------------------------------------------------------------- numbers
def normalize(value):
    """Return a divergence as a 6-decimal string like '1.048596', wrapped into [0, 6).

    Accepts plain decimal numbers only. Exponent notation, underscores, NaN/Infinity and
    absurdly large numbers are rejected with ValueError, never with an arithmetic error.
    """
    if isinstance(value, str):
        text = value.strip()
    else:
        try:
            text = format(Decimal(str(value)), "f")
        except Exception:
            raise ValueError("not a number: %r" % (value,))
    if not _NUMBER_RE.match(text):
        raise ValueError("not a number: %r" % (value,))
    d = Decimal(text)
    if abs(d) >= MAX_INPUT:
        raise ValueError("number out of range: %r" % (value,))
    d = d % DIVERGENCE_SPAN             # wrap into [0, 6)
    if d < 0:                           # Decimal % keeps the dividend's sign
        d += DIVERGENCE_SPAN
    d = d.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    if d >= DIVERGENCE_SPAN:
        d = Decimal("0.000000")
    if d == 0:
        d = DIVERGENCE_MIN
    return format(d, "f")


# ------------------------------------------------------------------ packs
REQUIRED_PALETTE = ("bg", "bg_alt", "fg", "accent", "selection", "muted")
_pack_errors = []


def _clean_text(value, fallback, limit=40):
    """Printable, shell/Lua/CSS-inert text for names and taglines."""
    text = re.sub(r"[^A-Za-z0-9 .'/\-]", "", str(value))[:limit].strip()
    return text or fallback


class Pack:
    def __init__(self, path, data):
        if not isinstance(data, dict):
            raise ValueError("worldline.json must contain an object")
        self.path = Path(path)
        pid = data.get("id")
        if not isinstance(pid, str) or not _ID_RE.fullmatch(pid) or len(pid) > 40:
            raise ValueError("invalid id %r (use lowercase letters, digits and single dashes)" % (pid,))
        self.id = pid
        self.name = _clean_text(data.get("name", pid), pid)
        if "divergence" not in data:
            raise ValueError("missing divergence")
        self.divergence = normalize(data["divergence"])
        try:
            lo, hi = data["range"]
            self.low, self.high = Decimal(str(lo)), Decimal(str(hi))
        except Exception:
            raise ValueError("range must be [low, high]")
        if not (self.low.is_finite() and self.high.is_finite()):
            raise ValueError("range bounds must be finite numbers")
        if not (0 <= self.low <= self.high <= DIVERGENCE_SPAN):
            raise ValueError("range %s-%s is outside 0-%s" % (self.low, self.high, DIVERGENCE_SPAN))
        palette = data.get("palette")
        if not isinstance(palette, dict):
            raise ValueError("missing palette")
        missing = [k for k in REQUIRED_PALETTE if k not in palette]
        if missing:
            raise ValueError("palette missing %s" % ", ".join(missing))
        for key in REQUIRED_PALETTE:
            if not isinstance(palette[key], str) or not _HEX_RE.fullmatch(palette[key]):
                raise ValueError("palette.%s must be #rrggbb, got %r" % (key, palette[key]))
        self.palette = {k: palette[k].lower() for k in REQUIRED_PALETTE}
        tp = data.get("terminal_palette", [])
        if tp and not (isinstance(tp, list) and len(tp) == 16 and all(isinstance(c, str) and _HEX_RE.fullmatch(c) for c in tp)):
            _pack_errors.append("%s: terminal_palette ignored (needs 16 #rrggbb colours)" % pid)
            tp = []
        self.terminal_palette = [c.lower() for c in tp]
        wp = data.get("wallpaper", "wallpaper.svg")
        if not isinstance(wp, str) or wp != os.path.basename(wp) or wp.startswith(".") or not wp.lower().endswith(".svg"):
            raise ValueError("wallpaper must be a plain .svg file name in the pack folder")
        self.wallpaper = wp
        self.tagline = _clean_text(data.get("tagline", ""), "")

    def contains(self, divergence):
        d = Decimal(divergence)
        return self.low <= d <= self.high

    def distance(self, divergence):
        d = Decimal(divergence)
        if self.contains(divergence):
            return Decimal(0)
        return min(abs(d - self.low), abs(d - self.high))

    def wallpaper_path(self):
        return self.path / self.wallpaper


def pack_errors():
    """Problems found by the most recent load_packs() call (invalid packs are skipped)."""
    return list(_pack_errors)


def load_packs():
    del _pack_errors[:]
    packs, seen = [], set()
    root = packs_dir()
    if not root.is_dir():
        return packs
    try:
        entries = sorted(root.iterdir())
    except OSError as e:
        _pack_errors.append("%s: %s" % (root, e))
        return packs
    for sub in entries:
        f = sub / "worldline.json"
        if not f.is_file():
            continue
        try:
            pack = Pack(sub, json.loads(f.read_text(encoding="utf-8")))
            if pack.id in seen:
                raise ValueError("duplicate id %r" % pack.id)
            if not pack.wallpaper_path().is_file():
                raise ValueError("wallpaper %s not found" % pack.wallpaper)
        except (OSError, ValueError) as e:       # JSONDecodeError and UnicodeDecodeError are ValueErrors
            _pack_errors.append("%s: %s" % (sub.name, e))
            continue
        seen.add(pack.id)
        packs.append(pack)
    return packs


def pick_pack(divergence, packs=None):
    packs = load_packs() if packs is None else packs
    if not packs:
        raise RuntimeError("no usable worldline packs in %s" % packs_dir())
    d = normalize(divergence)
    return min(packs, key=lambda p: (p.distance(d), p.id))


# ------------------------------------------------------------------ state
def default_divergence():
    try:
        return normalize((etc_dir() / "default-divergence").read_text())
    except (OSError, ValueError):
        return DEFAULT_DIVERGENCE


def get_divergence():
    try:
        return normalize(state_file().read_text())
    except (OSError, ValueError):
        return default_divergence()


def set_divergence(value):
    d = normalize(value)
    atomic_write(state_file(), d + "\n")
    return d


def current():
    """(divergence, Pack or None) for display code that must never crash."""
    d = get_divergence()
    try:
        return d, pick_pack(d)
    except RuntimeError:
        return d, None


# ---------------------------------------------------------------- D-mail
def dmail_delta(text):
    """Deterministic divergence shift derived from a message (-2.0 .. +2.0)."""
    digest = hashlib.sha256(text.strip().lower().encode("utf-8", "replace")).hexdigest()
    n = int(digest[:8], 16) % 4000001
    return Decimal(n) / Decimal(1000000) - Decimal(2)


def send_dmail(text, current_value=None):
    base = get_divergence() if current_value is None else current_value
    return normalize(Decimal(normalize(base)) + dmail_delta(text))


# ------------------------------------------------------------------ codes
def load_codes():
    """Codes from codes.json. A bad entry is skipped; it never disables the others."""
    try:
        raw = json.loads((etc_dir() / "codes.json").read_text(encoding="utf-8"))
        entries = raw.get("codes", {}) if isinstance(raw, dict) else {}
        entries = entries if isinstance(entries, dict) else {}
    except (OSError, ValueError):
        return {}
    codes = {}
    for key, val in entries.items():
        try:
            codes[re.sub(r"\s+", " ", str(key).strip().upper())] = normalize(val)
        except ValueError:
            continue
    return codes


def lookup_code(text):
    return load_codes().get(re.sub(r"\s+", " ", text.strip().upper()))


# ----------------------------------------------------------------- apply
class ApplyResult(list):
    """List of human-readable notes (compatible with the old return type) plus structured steps."""

    def __init__(self):
        super().__init__()
        self.steps = []                          # (step, ok, detail)

    def add(self, step, ok, detail):
        self.steps.append((step, ok, detail))
        self.append(detail if ok else "ERROR %s: %s" % (step, detail))

    @property
    def errors(self):
        return [s for s in self.steps if not s[1]]

    @property
    def ok(self):
        return not self.errors


def gtk_css(pack):
    p = pack.palette
    sel, fg, bg, bg2, acc = p["selection"], "#ffffff", p["bg"], p["bg_alt"], p["accent"]
    return "\n".join([
        "%s -- steins-worldline:%s (generated; replaced on every switch, edit outside this block) */" % (CSS_BEGIN, pack.id),
        "@define-color theme_selected_bg_color %s;" % sel,
        "@define-color theme_selected_fg_color %s;" % fg,
        "@define-color selected_bg_color %s;" % sel,
        "@define-color selected_fg_color %s;" % fg,
        "selection { background-color: %s; color: %s; }" % (sel, fg),
        ".view:selected, row:selected { background-color: %s; color: %s; }" % (sel, fg),
        "button.suggested-action { background-image: none; background-color: %s; color: %s; }" % (sel, fg),
        ".xfce4-panel, .xfce4-panel.panel { background-image: none; background-color: %s; color: %s; }" % (bg2, p["fg"]),
        "entry:focus { border-color: %s; }" % acc,
        "progressbar progress, scale highlight { background-color: %s; }" % acc,
        "vte-terminal { padding: 10px 16px 8px 16px; }",
        "#xfce4-terminal-notebook > header.top > tabs > tab:checked { background-color: %s; border-bottom-color: %s; }" % (bg2, acc),
        "#xfce4-terminal-notebook scrollbar, #xfce4-terminal-notebook scrollbar trough { background-color: %s; }" % bg2,
        "#xfce4-terminal-notebook scrollbar slider:active { background-color: %s; }" % acc,
        "%s */" % CSS_END,
        "",
    ])


def merge_css(existing, block):
    """Put our block into a user's gtk.css without touching anything else."""
    if existing is None or not existing.strip():
        return block
    b = existing.find(CSS_BEGIN)
    e = existing.find(CSS_END)
    if b != -1 and e > b:
        line_end = existing.find("\n", e)
        tail = existing[line_end + 1:] if line_end != -1 else ""
        return existing[:b] + block + tail
    if b != -1:
        raise ValueError("gtk.css has an unterminated steins-worldline block; fix or delete it")
    if existing.lstrip().startswith("/* %s:" % MARKER):   # file written by the first release: wholly generated
        return block
    return existing + ("" if existing.endswith("\n") else "\n") + "\n" + block


def _write_gtk_css(pack, home, dry):
    target = home / ".config" / "gtk-3.0" / "gtk.css"
    if dry:
        return "gtk.css -> %s" % target
    try:
        existing = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        existing = None
    except UnicodeDecodeError:
        raise ValueError("%s is not valid UTF-8; left untouched" % target)
    atomic_write(target, merge_css(existing, gtk_css(pack)))
    return "gtk.css -> %s" % target


# terminalrc key -> xfce4-terminal xfconf property (XFCE 4.20 reads the channel).
_TERMINAL_PROPERTIES = {
    "ColorForeground": "color-foreground", "ColorBackground": "color-background",
    "ColorCursor": "color-cursor", "ColorPalette": "color-palette",
    "ColorCursorForeground": "color-cursor-foreground", "ColorCursorUseDefault": "color-cursor-use-default",
    "ColorSelection": "color-selection", "ColorSelectionBackground": "color-selection-background",
    "ColorSelectionUseDefault": "color-selection-use-default", "TabActivityColor": "tab-activity-color",
}


def _write_terminal(pack, home, dry):
    target = home / ".config" / "xfce4" / "terminal" / "terminalrc"
    p = pack.palette
    # Only colours follow the worldline. Font, cursor shape, scrollback and the
    # other profile choices come from the skeleton profile and stay the user's.
    wanted = {"ColorForeground": p["fg"], "ColorBackground": p["bg_alt"], "ColorCursor": p["accent"],
              "ColorCursorForeground": p["bg_alt"], "ColorCursorUseDefault": "FALSE",
              "ColorSelection": "#ffffff", "ColorSelectionBackground": p["selection"],
              "ColorSelectionUseDefault": "FALSE", "TabActivityColor": p["accent"]}
    if pack.terminal_palette:
        wanted["ColorPalette"] = ";".join(pack.terminal_palette)
    if dry:
        return "terminalrc -> %s" % target
    try:
        lines = target.read_text(encoding="utf-8").splitlines() if target.exists() else ["[Configuration]"]
    except UnicodeDecodeError:
        raise ValueError("%s is not valid UTF-8; left untouched" % target)
    seen, out = set(), []
    for line in lines:
        key = line.split("=", 1)[0]
        if key in wanted and "=" in line:
            out.append("%s=%s" % (key, wanted[key]))
            seen.add(key)
        else:
            out.append(line)
    for key, val in wanted.items():
        if key not in seen:
            out.append("%s=%s" % (key, val))
    atomic_write(target, "\n".join(out) + "\n")
    # XFCE 4.20 migrates terminalrc once, then reads the xfconf channel.
    if os.environ.get("DISPLAY") and shutil.which("xfconf-query"):
        failed = []
        for key, val in wanted.items():
            prop = _TERMINAL_PROPERTIES[key]
            kind, val = ("bool", val.lower()) if val in ("TRUE", "FALSE") else ("string", val)
            ok, msg = _run(["xfconf-query", "-c", "xfce4-terminal", "-p", "/" + prop,
                            "--create", "-t", kind, "-s", val])
            if not ok:
                failed.append(msg)
        if failed:
            raise RuntimeError("terminalrc saved, but %d of %d xfconf updates failed (%s)" % (len(failed), len(wanted), failed[0]))
    return "terminalrc -> %s" % target


def _write_conky(pack, home, dry):
    src = etc_dir() / "conky.conf"
    target = home / ".config" / "steins" / "conky.conf"
    if dry:
        return "conky.conf -> %s" % target
    if not src.is_file():
        return "conky: %s not found, skipped" % src
    text = src.read_text(encoding="utf-8")
    strip = lambda c: c.lstrip("#").upper()
    p = pack.palette
    text = re.sub(r"default_color = '[0-9A-Fa-f]{6}'", "default_color = '%s'" % strip(p["muted"]), text)
    text = re.sub(r"color1 = '[0-9A-Fa-f]{6}'", "color1 = '%s'" % strip(p["accent"]), text)
    text = re.sub(r"color2 = '[0-9A-Fa-f]{6}'", "color2 = '%s'" % strip(p["fg"]), text)
    # shlex.quote keeps a HOME with spaces or quotes working inside conky's shell call
    text = text.replace("1.048596", "${execi 2 cat %s}" % shlex.quote(str(state_file())))
    text = text.replace("REFERENCE DIVERGENCE · FICTIONAL", pack.name.upper() + " · FICTIONAL")
    atomic_write(target, text)
    return "conky.conf -> %s" % target


def _png_for(pack, home, dry):
    """Wallpaper PNG for a pack, cached by content hash. Returns a Path or None.

    The cache key is the SVG's content, not its timestamp, so upgrades and clock skew
    cannot leave a stale image. A failed render never leaves a half-written file behind.
    """
    cache = home / ".cache" / "steins"
    svg = pack.wallpaper_path()
    try:
        digest = hashlib.sha256(svg.read_bytes()).hexdigest()[:12]
    except OSError:
        if dry:
            return cache / (pack.id + ".png")
        raise RuntimeError("wallpaper %s is unreadable" % svg)
    png = cache / ("%s-%s.png" % (pack.id, digest))
    if dry:
        return png
    try:
        if png.stat().st_size > 200 and png.read_bytes()[:8] == _PNG_MAGIC:
            return png
    except OSError:
        pass
    if shutil.which("rsvg-convert") is None:
        return None
    cache.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(cache), prefix=".render-", suffix=".png")
    os.close(fd)
    try:
        ok, msg = _run(["rsvg-convert", "-f", "png", "-o", tmp, str(svg)], timeout=30)
        if not ok:
            raise RuntimeError("rsvg-convert failed: %s" % msg)
        with open(tmp, "rb") as fh:
            if fh.read(8) != _PNG_MAGIC or os.path.getsize(tmp) <= 200:
                raise RuntimeError("rsvg-convert produced an invalid image")
        os.chmod(tmp, _default_mode())
        os.replace(tmp, png)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    for old in cache.glob(pack.id + "-*.png"):       # drop stale renders of this pack
        if old != png:
            try:
                old.unlink()
            except OSError:
                pass
    return png


def _monitor_outputs():
    if not shutil.which("xrandr"):
        return []
    try:
        q = subprocess.run(["xrandr", "--query"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [l.split()[0] for l in q.splitlines() if len(l.split()) > 1 and l.split()[1] == "connected"]


def _set_wallpaper(png, dry):
    if png is None:
        return "wallpaper: no image, skipped"
    if dry:
        return "wallpaper -> %s" % png
    if shutil.which("xfconf-query") is None or not os.environ.get("DISPLAY"):
        return "wallpaper: no desktop session, skipped"
    outputs = _monitor_outputs()
    if not outputs:
        raise RuntimeError("no connected monitors reported by xrandr; wallpaper not changed")
    failed = 0
    for out in outputs:
        for ws in range(4):
            base = "/backdrop/screen0/monitor%s/workspace%d" % (out, ws)
            for prop, typ, val in (("last-image", "string", str(png)), ("image-style", "int", "5")):
                ok, _ = _run(["xfconf-query", "-c", "xfce4-desktop", "-p", base + "/" + prop,
                              "--create", "-t", typ, "-s", val])
                failed += 0 if ok else 1
    if failed:
        raise RuntimeError("%d xfconf wallpaper updates failed" % failed)
    return "wallpaper -> %s" % png


def _set_panel(pack, dry):
    """Colour the top panel through xfconf (the reliable route; GTK CSS alone did not take effect)."""
    if dry:
        return "panel -> %s" % pack.palette["bg_alt"]
    if shutil.which("xfconf-query") is None or not os.environ.get("DISPLAY"):
        return "panel: no desktop session, skipped"
    rgb = [int(pack.palette["bg_alt"][i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    base = "/panels/panel-1/"
    ok1, m1 = _run(["xfconf-query", "-c", "xfce4-panel", "-p", base + "background-style", "--create", "-t", "uint", "-s", "1"])
    cmd = ["xfconf-query", "-c", "xfce4-panel", "-p", base + "background-rgba", "--create"]
    for v in rgb + [0.96]:
        cmd += ["-t", "double", "-s", "%.4f" % v]
    ok2, m2 = _run(cmd)
    if not (ok1 and ok2):
        raise RuntimeError("panel colour not updated (%s)" % (m1 or m2))
    return "panel -> %s" % pack.palette["bg_alt"]


def _ere_escape(text):
    return re.sub(r"([.\[\]{}()*+?^$|\\])", r"\\\1", text)


def _restart_conky(home, dry):
    conf = home / ".config" / "steins" / "conky.conf"
    if dry or shutil.which("conky") is None or not conf.is_file() or not os.environ.get("DISPLAY"):
        return "conky: not restarted"
    # Only stop the conky instances this project started, never the user's other widgets.
    for pattern in ("conky -c " + _ere_escape(str(conf)), "conky -c /etc/steins/conky.conf"):
        _run(["pkill", "-u", str(os.getuid()), "-f", "--", pattern])
    try:
        subprocess.Popen(["conky", "-c", str(conf)], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError as e:
        raise RuntimeError("could not start conky: %s" % e)
    return "conky restarted"


def session_request(method, value=None):
    """Use the explicitly selected Plasma session's authoritative state service.

    Callers decide when this applies; low-level file functions remain available
    for headless/XFCE use and for the service itself. A failed session request
    must never fall back to an independent write/apply operation.
    """
    if method not in ('SetDivergence', 'ShiftMessage', 'ApplyCurrent'):
        raise ValueError('Unsupported worldline request')
    try:
        import dbus
        service = dbus.Interface(dbus.SessionBus().get_object(
            'org.steinsos.Worldline1', '/org/steinsos/Worldline'), 'org.steinsos.Worldline1')
        fn = getattr(service, method)
        result = json.loads(str(fn(str(value), timeout=65) if value is not None else fn(timeout=65)))
        if (not isinstance(result, dict) or result.get('interface') != 1 or
                not isinstance(result.get('divergence'), str) or
                type(result.get('applied')) is not bool or not isinstance(result.get('errors'), list) or
                any(not isinstance(e, dict) or not isinstance(e.get('step'), str) or
                    not isinstance(e.get('message'), str) for e in result.get('errors', []))):
            raise ValueError('Malformed session result')
        if 'previous_divergence' in result and (not isinstance(result['previous_divergence'], str) or
                normalize(result['previous_divergence']) != result['previous_divergence']):
            raise ValueError('Malformed previous divergence')
        return result
    except Exception as error:
        raise RuntimeError('Worldline session request failed: %s' % error) from error


def session_result(state):
    """Adapt a service reply to the existing CLI's per-step reporting contract."""
    result = ApplyResult()
    if state['applied']:
        result.add('session', True, 'Worldline applied by the session service')
    else:
        for error in state['errors']:
            result.add(str(error.get('step', 'session')), False, str(error.get('message', 'Apply failed')))
        if not result.steps:
            result.add('session', False, 'Appearance was not fully applied')
    return result


def apply_pack(pack, dry_run=False):
    """Apply a worldline to the current user's session. Never raises.

    Each step is isolated. The wallpaper is rendered first (the most failure-prone step) but a
    failure there only skips the wallpaper. The monitor (conky) is always attempted last, so a
    failing step can no longer leave the desktop without it. Check result.ok / result.errors.
    """
    # Explicit opt-in: the reference XFCE image never selects experimental code.
    if os.environ.get("STEINS_DESKTOP_BACKEND") == "plasma":
        try:
            import steinsplasma
            return steinsplasma.apply_pack(pack, dry_run)
        except Exception as e:
            result = ApplyResult()
            result.add("plasma", False, str(e))
            return result
    home = home_dir()
    result = ApplyResult()
    png = [None]

    def step(name, fn):
        try:
            result.add(name, True, fn())
        except Exception as e:                       # noqa: BLE001 - reported, never propagated
            result.add(name, False, str(e) or type(e).__name__)

    def render():
        png[0] = _png_for(pack, home, dry_run)
        return "wallpaper image ready" if png[0] else "wallpaper image: renderer unavailable, skipped"

    if not dry_run:
        step("state", lambda: (set_divergence(get_divergence()), "state file ready")[1])   # first login needs it
    step("render", render)
    step("gtk", lambda: _write_gtk_css(pack, home, dry_run))
    step("terminal", lambda: _write_terminal(pack, home, dry_run))
    step("conky-config", lambda: _write_conky(pack, home, dry_run))
    step("wallpaper", lambda: _set_wallpaper(png[0], dry_run))
    step("panel", lambda: _set_panel(pack, dry_run))
    step("conky", lambda: _restart_conky(home, dry_run))
    return result
