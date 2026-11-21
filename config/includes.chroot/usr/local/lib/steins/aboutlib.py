"""Plain-text content and helpers for steins-about. No GTK import, so tests can run headless."""
import os
import platform
from pathlib import Path

VERSION = "0.1"
CODENAME = "Gate of Steiner"
GUIDE = "/usr/share/doc/steins-os/guide.html"
STATUS = ("Development preview. Not a production-certified release: hardware compatibility, "
          "Secure Boot, suspend and Steins;OS-specific update ownership are untested or not yet provided.")
DISCLAIMER = ("Steins;OS is an independent, community-built Linux distribution. Not affiliated with, or endorsed by, the creators "
              "or rights holders of any work it alludes to. All artwork is original.")
REAL_VS_FICTION = (
    "Decorative: the divergence number, worldline names, D-Mail and codes. They are stored as one local number "
    "and change only colours and wallpaper.\n"
    "Real: the CPU, memory, disk and uptime readings on the desktop widget and in System information.")
DMAIL = ("D-Mail is fictional and local-only. Nothing is sent over a network; the message text is hashed to a "
         "repeatable shift of the number on this computer.")
ACCENT_NOTE = "Already-open GTK applications keep their old accent colours until you reopen them."
PERSISTENCE = ("In the live session, changes vanish at shutdown. After installation the divergence is saved in "
               "your home folder and re-applied at each login.")


def os_pretty_name(path="/etc/os-release"):
    try:
        for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip().strip('"') or None
    except OSError:
        pass
    return None


def system_line():
    return "%s · XFCE · Linux %s" % (os_pretty_name() or "Steins;OS %s (%s)" % (VERSION, CODENAME), platform.release())


def is_live():
    return Path("/run/live/medium").exists()


def worldline_rows(packs):
    """[(name, 'N.x', reference number, tagline)] ordered by divergence, for display."""
    rows = sorted(packs, key=lambda p: (p.low, p.id))
    return [(p.name, "%d.x" % int(p.low), p.divergence, p.tagline) for p in rows]


def current_summary(divergence, pack):
    if pack is None:
        return "Divergence %s · no worldline pack available" % divergence
    return "Divergence %s · worldline %s" % (divergence, pack.name)


def shell_command_hint():
    return "ibm5100   (type HELP; try the code CICADA)"
