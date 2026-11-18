"""Display-independent logic for the steins-meter divergence meter (testable without GTK)."""
import random
import json
from pathlib import Path

TUBES = 8                    # "d.dddddd"
DIGITS = "0123456789"


def motion_profile(preferences_path, default="full"):
    """Read the shared preference without maintaining another state file.

    Legacy sessions may keep their existing Full behaviour when no preference file
    exists. Plasma passes Reduced as its default. Corrupt/unreadable preferences
    always choose Reduced so a damaged file cannot force digit scrambling.
    """
    try:
        preferences = json.loads(Path(preferences_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default if default in ("off", "reduced", "full") else "reduced"
    except (OSError, ValueError):
        return "reduced"
    if not isinstance(preferences, dict):
        return "reduced"
    value = preferences.get("motion", default)
    return value if value in ("off", "reduced", "full") else "reduced"


def glyphs(number):
    """Split a normalized divergence ('1.048596') into the 8 tube characters."""
    text = str(number)
    if len(text) != TUBES or text[1] != "." or not (text[0] + text[2:]).isdigit():
        raise ValueError("expected a divergence like 1.048596, got %r" % (number,))
    return list(text)


def flicker_frames(old, new, frames=15, rng=None):
    """Frames that scramble the tubes and settle them left to right on `new`.

    Each frame is an 8-character string. The last frame is always exactly `new`; the first
    frames start from `old`. Tube k locks onto its final glyph from frame lock[k] onward.
    """
    rng = rng or random.Random()
    a, b = glyphs(old), glyphs(new)
    frames = max(2, int(frames))
    lock = [max(1, int(round((k + 1) * (frames - 1) / TUBES))) for k in range(TUBES)]
    out = []
    for i in range(frames - 1):
        row = []
        for k in range(TUBES):
            if b[k] == ".":
                row.append(".")
            elif i >= lock[k]:
                row.append(b[k])
            elif i == 0 and a[k] != b[k]:
                row.append(a[k])                      # start from the old reading
            else:
                row.append(rng.choice(DIGITS))
        out.append("".join(row))
    out.append("".join(b))
    return out


def accessible_text(number, worldline_name):
    spoken = " point ".join(str(number).split("."))
    return "Divergence %s. Worldline: %s." % (spoken, worldline_name or "unknown")


def _rgba(hex_colour, alpha):
    h = hex_colour.lstrip("#")
    return "rgba(%d,%d,%d,%.2f)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def css_for(palette):
    """GTK3 CSS for the meter, from a worldline palette (all values validated #rrggbb)."""
    bg, bg2, fg, acc, muted = palette["bg"], palette["bg_alt"], palette["fg"], palette["accent"], palette["muted"]
    return "\n".join([
        ".steins-meter { background-color: %s; }" % bg2,
        ".steins-meter-body { padding: 14px 18px; }",
        ".tube { font-family: 'DejaVu Sans Mono', monospace; font-size: 40px; font-weight: bold; color: %s;"
        " background-image: linear-gradient(to bottom, rgba(255,255,255,0.07), rgba(0,0,0,0.40));"
        " border: 1px solid %s; border-radius: 10px; padding: 6px 4px; min-width: 34px;"
        " text-shadow: 0 0 6px %s, 0 0 18px %s; }" % (acc, _rgba(muted, 0.45), _rgba(acc, 0.9), _rgba(acc, 0.45)),
        ".tube.dot { min-width: 14px; padding: 6px 2px; }",
        ".tube.scramble { color: %s; text-shadow: 0 0 4px %s; }" % (fg, _rgba(fg, 0.5)),
        ".meter-title { color: %s; font-size: 11px; letter-spacing: 2px; }" % muted,
        ".meter-world { color: %s; font-size: 13px; font-weight: bold; letter-spacing: 3px; }" % acc,
        ".meter-hint { color: %s; font-size: 10px; }" % _rgba(muted, 0.8),
        "button.meter-button { background-image: none; background-color: transparent; border: 1px solid transparent;"
        " border-radius: 12px; padding: 4px; box-shadow: none; }",
        "button.meter-button:focus { border-color: %s; }" % acc,
        "button.meter-button:hover { background-color: %s; }" % _rgba(acc, 0.08),
    ])
