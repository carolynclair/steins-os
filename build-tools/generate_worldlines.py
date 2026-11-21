#!/usr/bin/env python3
"""Regenerate the worldline packs (worldline.json + wallpaper.svg), codes.json and default-divergence.

Six time-loop "places", each art-directed. All artwork is original procedural geometry and text:
no screenshots, logos, character art or other third-party imagery. Series names appear only as hidden
codes. No SVG filters are used (they render differently in different viewers); glow is layered shapes.

Layout contract (source canvas 1920x1080; see docs/CLAUDE-CHANGES.md):
  * TITLE block top-left (y 120-330): the LightDM login box sits left-centre (about x 230-720, y 400-680)
    and must never cover it.
  * CONKY ZONE top-right (x >= 1340, y <= 480): the system widget lives here; keep art faint/empty.
  * Art focus lives centre-right/low. No baked-in divergence number (it would not follow the live state);
    a six-band ruler along the bottom shows where this world sits instead.
Set STEINS_DEBUG_ZONES=1 to draw both zones for layout review.

Edit WORLDLINES / SCENES below, then run:  python3 build-tools/generate_worldlines.py
Stale pack folders that are no longer listed are removed.
"""
import json
import math
import os
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "config/includes.chroot/etc/steins"
W, H = 1920, 1080
CONKY_ZONE = (1340, 40, 1920, 480)
GREETER_ZONE = (230, 400, 720, 680)

BASE_ANSI = ["#242c31", "#d97b71", "#93aa86", "#e8b56b", "#86a6b5", "#b196ad", "#89b5a7", "#ddd7c8",
             "#66716e", "#ec998c", "#b5c79e", "#ffd28a", "#acc4d1", "#ccb3c3", "#b0d6c4", "#f4eddf"]

WORLDLINES = [
    dict(id="alpha", name="Alpha", divergence="0.571024", range=[0.0, 0.999999],
         tagline="ORIGIN ATTRACTOR FIELD",
         palette=dict(bg="#171211", bg_alt="#120e0e", fg="#e6dcd6", accent="#c4513a",
                      selection="#8f3a2a", muted="#a08d86")),
    dict(id="steins-gate", name="Steins Gate", divergence="1.048596", range=[1.0, 1.999999],
         tagline="FUTURE GADGET LABORATORY",
         palette=dict(bg="#151b20", bg_alt="#141a1e", fg="#e7e2d6", accent="#e99a45",
                      selection="#a2652a", muted="#9cab9f")),
    dict(id="hinamizawa", name="Hinamizawa", divergence="2.198306", range=[2.0, 2.999999],
         tagline="EVENING / CICADA HOUR",
         palette=dict(bg="#1a1210", bg_alt="#140d0c", fg="#eadbcd", accent="#e0622c",
                      selection="#a8421a", muted="#a89080")),
    dict(id="hitogashima", name="Hitogashima", divergence="3.072100", range=[3.0, 3.999999],
         tagline="ISLAND / TIDE / SHADOW",
         palette=dict(bg="#0f1f2a", bg_alt="#0b1821", fg="#e3eef3", accent="#38a8e0",
                      selection="#1f78a6", muted="#7fa3b8")),
    dict(id="lugunica", name="Lugunica", divergence="4.250801", range=[4.0, 4.999999],
         tagline="SILVER MOON / COLD AIR / RETURN",
         palette=dict(bg="#161824", bg_alt="#11131c", fg="#e6e6f0", accent="#a99cf0",
                      selection="#6e5fc4", muted="#9a9bb8")),
    dict(id="mitakihara", name="Mitakihara", divergence="5.093001", range=[5.0, 5.999999],
         tagline="CITY / CLOCKWORK / AGAIN",
         palette=dict(bg="#1a1426", bg_alt="#140f1e", fg="#f0e6f0", accent="#f08ab8",
                      selection="#a8487a", muted="#b79bc4")),
]

CODES = {
    "_comment": "Codes typed into the ibm5100 terminal. Values are divergence numbers (0 - 6). Add your own.",
    "codes": {
        "EL PSY KONGROO": "1.048596",
        "ATTRACTOR": "0.571024",
        "CICADA": "2.198306",
        "HINAMIZAWA": "2.198306",
        "SHADOW": "3.072100",
        "HITOGASHIMA": "3.072100",
        "RETURN BY DEATH": "4.250801",
        "LUGUNICA": "4.250801",
        "MITAKIHARA": "5.093001",
        "AGAIN": "5.093001",
    },
}


# ----------------------------------------------------------------- helpers
def f(x):
    return f"{x:.1f}"


def stars(rnd, n, x0, x1, y0, y1, colour, rmax=1.8, op=(0.25, 0.9)):
    return "".join(
        f'<circle cx="{f(rnd.uniform(x0, x1))}" cy="{f(rnd.uniform(y0, y1))}" r="{rnd.uniform(0.5, rmax):.1f}" '
        f'fill="{colour}" fill-opacity="{rnd.uniform(*op):.2f}"/>' for _ in range(n))


def ridge(rnd, x0, x1, base, amp, step, fill, op=1.0, seed_waves=3, bottom=H, taper=0, floor=0.0):
    """Filled silhouette. taper>0 eases the left end toward the baseline so there is no hard edge."""
    waves = [(rnd.uniform(0.004, 0.012) * (i + 1), rnd.uniform(0, 6.28), amp / (i + 1)) for i in range(seed_waves)]
    pts = []
    x = x0
    while x <= x1:
        k = 1.0
        if taper:
            t = max(0.0, min(1.0, (x - x0) / taper))
            k = floor + (1 - floor) * t * t * (3 - 2 * t)
        y = base - k * sum(a * (0.5 + 0.5 * math.sin(kk * x + ph)) for kk, ph, a in waves)
        pts.append(f"{f(x)},{f(y)}")
        x += step
    return f'<polygon points="{" ".join(pts)} {x1},{bottom} {x0},{bottom}" fill="{fill}" fill-opacity="{op}"/>'


def glow_disc(cx, cy, r, colour, layers=7, base_op=0.10, grow=1.18):
    return "".join(
        f'<circle cx="{cx}" cy="{cy}" r="{f(r * grow ** (layers - i))}" fill="{colour}" '
        f'fill-opacity="{base_op * (0.55 + i * .12):.3f}"/>' for i in range(layers))


def fade_defs(colour, x_from, x_to, x_out=None, x_end=None):
    """Horizontal gradient: transparent -> opaque (-> transparent again when x_out/x_end are given)."""
    right = ""
    if x_out is not None:
        right = (f'<stop offset="{(x_out - x_from) / (x_end - x_from):.3f}" stop-color="{colour}" stop-opacity="1"/>'
                 f'<stop offset="1" stop-color="{colour}" stop-opacity="0"/>')
        x_to_end = x_end
    else:
        right = f'<stop offset="1" stop-color="{colour}" stop-opacity="1"/>'
        x_to_end = x_to
    span = x_to_end - x_from
    first = (f'<stop stop-color="{colour}" stop-opacity="0"/>'
             f'<stop offset="{(x_to - x_from) / span:.3f}" stop-color="{colour}" stop-opacity="1"/>')
    if x_out is None:
        first = f'<stop stop-color="{colour}" stop-opacity="0"/>'
    return (f'<linearGradient id="fade" gradientUnits="userSpaceOnUse" x1="{x_from}" y1="0" x2="{x_to_end}" y2="0">'
            f'{first}{right}</linearGradient>')


def grid(step=80, op=0.045):
    lines = [f'<path d="M{x} 0V{H}"/>' for x in range(0, W + 1, step)]
    lines += [f'<path d="M0 {y}H{W}"/>' for y in range(0, H + 1, step)]
    return f'<g stroke="#8ea098" stroke-opacity="{op}">{"".join(lines)}</g>'


def ruler(active, palette):
    """Six-band divergence ruler: shows where this world sits in the 0-6 range (static, never stale)."""
    x0, x1, y = 140, 1780, 872
    unit = (x1 - x0) / 6.0
    muted, acc = palette["muted"], palette["accent"]
    s = ""
    for i in range(61):
        x = x0 + i * unit / 10
        major = i % 10 == 0
        s += f'<path d="M{f(x)} {y}v{14 if major else 7}" stroke="{muted}" stroke-opacity="{0.55 if major else 0.28}"/>'
    lo, hi = active["range"]
    s += f'<path d="M{f(x0 + lo * unit)} {y}H{f(x0 + (hi + 0.000001) * unit)}" stroke="{acc}" stroke-width="4"/>'
    for w in WORLDLINES:
        cx = x0 + (w["range"][0] + 0.5) * unit
        on = w["id"] == active["id"]
        s += (f'<text x="{f(cx)}" y="{y + 36}" text-anchor="middle" fill="{acc if on else muted}" '
              f'fill-opacity="{1 if on else 0.55}" font-family="DejaVu Sans Mono" font-size="13" letter-spacing="2">'
              f'{w["name"].upper()}</text>')
    return s


def debug_zones():
    out = ""
    for (x0, y0, x1, y1), colour in ((CONKY_ZONE, "#ff0000"), (GREETER_ZONE, "#00ff00")):
        out += f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{colour}" fill-opacity=".12" stroke="{colour}"/>'
    return out


# ------------------------------------------------------------------ scenes
# Each returns (defs, background_svg, scene_svg).
def scene_alpha(p):
    rnd = random.Random(571024)
    acc = p["accent"]
    defs = ('<radialGradient id="bg" cx=".6" cy=".55" r=".8"><stop stop-color="#2a1b19"/>'
            '<stop offset="1" stop-color="#0d0909"/></radialGradient>') + fade_defs(acc, 680, 1000)
    bg = f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
    cx, cy = 1120, 600
    s = glow_disc(cx, cy, 14, acc, layers=8, base_op=0.06)
    for i in range(20):  # converging field lines
        y0 = 120 + i * 46
        s += f'<path d="M680 {y0}L{cx} {cy}" stroke="url(#fade)" stroke-opacity="{0.12 + i * .010:.3f}" stroke-width="1.6"/>'
    for r in (60, 120, 210, 330):
        s += (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{acc}" stroke-opacity="{0.40 - r / 1100:.2f}" '
              f'stroke-dasharray="{6 + r // 20} {10 + r // 15}"/>')
    s += f'<circle cx="{cx}" cy="{cy}" r="8" fill="{acc}"/>'
    for _ in range(70):  # particles drawn in along the lines
        t = rnd.random() ** 1.6
        y0 = 120 + rnd.randint(0, 19) * 46
        x, y = 680 + (cx - 680) * t, y0 + (cy - y0) * t
        s += f'<circle cx="{f(x)}" cy="{f(y)}" r="{rnd.uniform(1, 2.6):.1f}" fill="{acc}" fill-opacity="{0.25 + 0.55 * t:.2f}"/>'
    for _ in range(9):  # glitch slices: the world failing to hold
        y, h = rnd.randint(500, 820), rnd.choice([4, 6, 10, 16])
        x, w = rnd.randint(720, 1200), rnd.randint(140, 420)
        s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{acc}" fill-opacity="{rnd.uniform(.05, .16):.2f}"/>'
    s += stars(rnd, 70, 700, 1900, 500, 1000, "#e6dcd6", 1.2, (.1, .4))
    return defs, bg, s


def scene_steins(p):
    rnd = random.Random(1048596)
    acc, muted = p["accent"], p["muted"]
    defs = ('<radialGradient id="bg" cx=".58" cy=".55" r=".85"><stop stop-color="#27322f"/>'
            '<stop offset="1" stop-color="#0f1519"/></radialGradient>')
    bg = f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
    gx, gy = 1110, 600
    s = ""
    for r, op, dash in ((300, .30, "2 14"), (250, .22, "40 10"), (190, .35, "none"), (120, .2, "4 8")):
        d = "" if dash == "none" else f' stroke-dasharray="{dash}"'
        s += f'<circle cx="{gx}" cy="{gy}" r="{r}" fill="none" stroke="{acc}" stroke-opacity="{op}"{d}/>'
    for k in range(48):  # gate tick marks
        a = k * math.pi / 24
        r0, r1 = 300, 318 if k % 4 == 0 else 308
        s += (f'<path d="M{f(gx + r0 * math.cos(a))} {f(gy + r0 * math.sin(a))}L{f(gx + r1 * math.cos(a))} '
              f'{f(gy + r1 * math.sin(a))}" stroke="{acc}" stroke-opacity=".5"/>')
    for i in range(7):  # worldline circuit traces, kept clear of the widget zone
        y = 430 + i * 60
        end = 760 + 140 + i * 30 + 90 + 260 - i * 10
        s += (f'<path d="M760 {y}H{900 + i * 30}l90 -90h{260 - i * 10}" fill="none" stroke="{acc}" '
              f'stroke-opacity="{0.12 + i * .065:.3f}" stroke-width="2"/>')
        s += f'<circle cx="{end - 760 + 760}" cy="{y - 90}" r="5" fill="{acc}" opacity=".7"/>'
    s += stars(rnd, 40, 700, 1330, 500, 860, muted, 1.4, (.1, .35))
    return defs, bg, s


def scene_hinamizawa(p):
    rnd = random.Random(2198306)
    acc = p["accent"]
    defs = ('<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#0d0708"/>'
            '<stop offset=".45" stop-color="#341610"/><stop offset=".66" stop-color="#a8421a"/>'
            '<stop offset=".67" stop-color="#1a0d0a"/><stop offset="1" stop-color="#0c0605"/></linearGradient>')
    defs += fade_defs(acc, 600, 800, 1180, 1330)
    bg = f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
    sx, sy = 1080, 712
    s = glow_disc(sx, sy, 150, "#ff8a3d", layers=9, base_op=0.05, grow=1.14)
    s += f'<circle cx="{sx}" cy="{sy}" r="150" fill="#f08a3c"/><circle cx="{sx}" cy="{sy}" r="150" fill="#ffd9a0" fill-opacity=".25"/>'
    for i in range(5):  # cicada sound waves in the sky, fading in and out
        pts = " ".join(f"{x},{400 + i * 36 + 18 * math.sin(x / (45 + i * 7) + i)}" for x in range(600, 1331, 8))
        s += f'<polyline points="{pts}" fill="none" stroke="url(#fade)" stroke-opacity="{0.60 - i * .09:.2f}" stroke-width="2"/>'
    s += ridge(rnd, 0, W, 712, 70, 14, "#2a120d", taper=900, floor=0.18)     # far hills
    s += ridge(rnd, 0, W, 775, 60, 14, "#1d0d0a", taper=900, floor=0.15)
    s += ridge(rnd, 0, W, 885, 50, 14, "#120807", floor=0.5)                   # foreground field
    for x in (860, 1290):                                                       # utility poles and wires
        s += f'<path d="M{x} 580V860M{x - 46} 620H{x + 46}M{x - 34} 660H{x + 34}" stroke="#0a0505" stroke-width="7"/>'
    s += f'<path d="M860 622Q1075 710 1290 622M860 662Q1075 750 1290 662" stroke="#0a0505" stroke-width="2" fill="none"/>'
    for i in range(14):                                                         # rice-field perspective rows
        x = 560 + i * 110
        s += f'<path d="M{x} {H}L1080 790" stroke="{acc}" stroke-opacity=".10"/>'
    for _ in range(46):                                                         # fireflies / embers
        s += (f'<circle cx="{f(rnd.uniform(640, 1330))}" cy="{f(rnd.uniform(580, 960))}" r="{rnd.uniform(1, 2.8):.1f}" '
              f'fill="#ffb066" fill-opacity="{rnd.uniform(.2, .8):.2f}"/>')
    s += stars(rnd, 40, 700, 1900, 20, 380, "#f3d9c4", 1.2, (.1, .4))
    return defs, bg, s


def scene_hitogashima(p):
    rnd = random.Random(3072100)
    acc = p["accent"]
    defs = ('<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#050d14"/>'
            '<stop offset=".5" stop-color="#0f3040"/><stop offset=".62" stop-color="#2b7a93"/>'
            '<stop offset=".625" stop-color="#0c2230"/><stop offset="1" stop-color="#050e15"/></linearGradient>')
    bg = f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
    mx, my = 1120, 270
    s = glow_disc(mx, my, 100, "#bfe9f5", layers=8, base_op=0.045, grow=1.16)
    s += f'<circle cx="{mx}" cy="{my}" r="100" fill="#e6f6fb" fill-opacity=".92"/>'
    s += f'<circle cx="{mx - 30}" cy="{my - 20}" r="22" fill="#b9dbe6" fill-opacity=".5"/>'
    s += '<polygon points="900,0 1060,0 700,1080 520,1080" fill="#000" fill-opacity=".28"/>'     # long shadow
    s += ridge(rnd, 760, W, 672, 105, 12, "#0a1c27", 1, 4, bottom=700, taper=420)                   # island
    for i in range(10):                                                                              # sea in perspective (stops above the ruler)
        y = 680 + i * (i + 4) * 1.4
        amp = 3 + i * 0.9
        pts = " ".join(f"{x},{f(y + amp * math.sin(x / (30 + i * 6) + i))}" for x in range(0, 1921, 8))
        s += (f'<polyline points="{pts}" fill="none" stroke="{acc}" stroke-opacity="{0.14 + i * .03:.2f}" '
              f'stroke-width="{1 + i * .12:.1f}"/>')
    for i in range(10):                                                                              # moon glitter on water
        y = 690 + i * 18
        w = 10 + i * 5
        s += f'<path d="M{mx - w} {y}H{mx + w}" stroke="#e6f6fb" stroke-opacity="{0.55 - i * .025:.2f}" stroke-width="3"/>'
    s += stars(rnd, 90, 700, 1900, 10, 560, "#d5eef7", 1.4, (.15, .6))
    return defs, bg, s


def scene_lugunica(p):
    rnd = random.Random(4250801)
    acc = p["accent"]
    defs = ('<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#0b0c18"/>'
            '<stop offset=".55" stop-color="#23233a"/><stop offset="1" stop-color="#3a3556"/></linearGradient>')
    bg = f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
    mx, my, r = 1130, 290, 140
    s = glow_disc(mx, my, r, "#cfcaf5", layers=9, base_op=0.035, grow=1.15)
    s += f'<path d="M{mx} {my - r}A{r} {r} 0 0 0 {mx} {my + r}A{r * 0.45:.0f} {r} 0 0 1 {mx} {my - r}Z" fill="#dcd8f7"/>'   # crescent
    # spire skyline; right of x=1340 stays below y=480 so the widget zone is clear
    for x, w, h, roof in ((740, 70, 250, 100), (830, 54, 360, 130), (900, 90, 200, 70), (1010, 46, 420, 150),
                          (1080, 110, 260, 90), (1210, 60, 380, 140), (1290, 80, 220, 70), (1390, 52, 250, 110),
                          (1470, 100, 200, 80), (1600, 64, 230, 90), (1690, 90, 150, 50)):
        top = 860 - h
        s += f'<rect x="{x}" y="{top}" width="{w}" height="{h + 220}" fill="#0b0b16"/>'
        s += f'<polygon points="{x - 6},{top} {x + w + 6},{top} {x + w / 2},{top - roof}" fill="#0b0b16"/>'
        for k in range(rnd.randint(1, 3)):
            s += f'<rect x="{x + w / 2 - 3 + rnd.randint(-12, 12)}" y="{top + 30 + k * 46}" width="6" height="16" fill="{acc}" fill-opacity=".55"/>'
    s += ridge(rnd, 0, W, 934, 34, 14, "#07070f", floor=0.3)
    s += f'<path d="M{mx - 40} {my + 150}V560" stroke="#d23a52" stroke-opacity=".7" stroke-width="3"/>'   # crimson thread
    s += f'<circle cx="{mx - 40}" cy="560" r="6" fill="#d23a52"/>'
    for _ in range(26):                                                                                  # ice shards
        x, y = rnd.randint(700, 1330), rnd.randint(60, 700)
        l = rnd.randint(30, 90)
        s += f'<polygon points="{x},{y} {x + 4},{y + l} {x - 4},{y + l * .8:.0f}" fill="{acc}" fill-opacity="{rnd.uniform(.12, .4):.2f}"/>'
    for _ in range(140):                                                                                 # falling snow
        s += (f'<circle cx="{f(rnd.uniform(560, 1900))}" cy="{f(rnd.uniform(0, 1000))}" r="{rnd.uniform(1, 3):.1f}" '
              f'fill="#ffffff" fill-opacity="{rnd.uniform(.15, .55):.2f}"/>')
    return defs, bg, s


def scene_mitakihara(p):
    rnd = random.Random(5093001)
    acc = p["accent"]
    defs = ('<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#0d0a1c"/>'
            '<stop offset=".5" stop-color="#2a1a40"/><stop offset=".82" stop-color="#7a3a68"/>'
            '<stop offset="1" stop-color="#1a1026"/></linearGradient>')
    bg = f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
    cx, cy, R = 1040, 410, 250
    s = glow_disc(cx, cy, R * 0.9, acc, layers=6, base_op=0.025, grow=1.1)
    s += f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{acc}" stroke-opacity=".55" stroke-width="3"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{R + 26}" fill="none" stroke="{acc}" stroke-opacity=".28" stroke-dasharray="14 9" stroke-width="8"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{R - 30}" fill="none" stroke="{acc}" stroke-opacity=".25"/>'
    for k in range(60):
        a = k * math.pi / 30 - math.pi / 2
        r0, r1 = R - 18, R - (40 if k % 5 == 0 else 28)
        s += (f'<path d="M{f(cx + r0 * math.cos(a))} {f(cy + r0 * math.sin(a))}L{f(cx + r1 * math.cos(a))} '
              f'{f(cy + r1 * math.sin(a))}" stroke="{acc}" stroke-opacity=".65" stroke-width="{3 if k % 5 == 0 else 1.5}"/>')
    for ang, ln, wd in ((-35, 160, 6), (200, 200, 4)):                                                  # clock hands, stopped
        a = math.radians(ang)
        s += f'<path d="M{cx} {cy}L{f(cx + ln * math.cos(a))} {f(cy + ln * math.sin(a))}" stroke="#ffd3e6" stroke-width="{wd}" stroke-linecap="round"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="10" fill="#ffd3e6"/>'
    x = 700
    while x < W:                                                                                         # skyline, tops at y >= 520
        w, h = rnd.randint(50, 120), rnd.randint(120, 380)
        s += f'<rect x="{x}" y="{H - 180 - h}" width="{w}" height="{h + 180}" fill="#0c0816"/>'
        if rnd.random() < .35 and h < 330:
            s += f'<path d="M{x + w / 2:.0f} {H - 180 - h}v-{rnd.randint(20, 40)}" stroke="#0c0816" stroke-width="3"/>'
        for wy in range(H - 170 - h, H - 200, 24):
            for wx in range(x + 8, x + w - 8, 18):
                if rnd.random() < .22:
                    s += (f'<rect x="{wx}" y="{wy}" width="6" height="9" fill="{rnd.choice([acc, "#ffe3f0", "#ffb3d4"])}" '
                          f'fill-opacity="{rnd.uniform(.35, .9):.2f}"/>')
        x += w + rnd.randint(4, 22)
    s += stars(rnd, 100, 600, 1900, 10, 520, "#ffe3f0", 1.5, (.15, .7))
    return defs, bg, s


SCENES = {"alpha": scene_alpha, "steins-gate": scene_steins, "hinamizawa": scene_hinamizawa,
          "hitogashima": scene_hitogashima, "lugunica": scene_lugunica, "mitakihara": scene_mitakihara}


def wallpaper(w):
    p = w["palette"]
    acc, muted, fg = p["accent"], p["muted"], p["fg"]
    defs, bg, scene = SCENES[w["id"]](p)
    vignette = ('<radialGradient id="vg" cx=".5" cy=".5" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/>'
                '<stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>')
    zones = debug_zones() if os.environ.get("STEINS_DEBUG_ZONES") else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>{defs}{vignette}</defs>
{bg}{grid()}
{scene}
<rect width="{W}" height="{H}" fill="url(#vg)"/>
<path d="M140 128h70" stroke="{acc}" stroke-width="4"/>
<text x="140" y="182" fill="{muted}" font-family="DejaVu Sans Mono" font-size="16" letter-spacing="4">{w["tagline"]}</text>
<text x="135" y="274" fill="{fg}" font-family="DejaVu Sans" font-size="76" font-weight="bold">Steins;OS</text>
<text x="140" y="320" fill="{acc}" font-family="DejaVu Sans Mono" font-size="18" letter-spacing="3">WORLDLINE / {w["name"].upper()}</text>
{ruler(w, p)}
<path d="M140 935H1780" stroke="#8ea098" stroke-opacity=".2"/>
<text x="140" y="974" fill="{muted}" fill-opacity=".75" font-family="DejaVu Sans Mono" font-size="13" letter-spacing="2">STEINS;OS / WORLDLINE SERIES</text>
{zones}</svg>'''


def ansi(accent, muted):
    a = list(BASE_ANSI)
    a[3], a[8], a[11] = accent, muted, accent
    return a


def main():
    packs_root = OUT / "worldlines"
    keep = {w["id"] for w in WORLDLINES}
    if packs_root.is_dir():
        for old in packs_root.iterdir():
            if old.is_dir() and old.name not in keep:
                shutil.rmtree(old)
                print("removed stale pack:", old.name)
    for w in WORLDLINES:
        d = packs_root / w["id"]
        d.mkdir(parents=True, exist_ok=True)
        data = {k: w[k] for k in ("id", "name", "divergence", "range", "palette", "tagline")}
        data["terminal_palette"] = ansi(w["palette"]["accent"], w["palette"]["muted"])
        data["wallpaper"] = "wallpaper.svg"
        (d / "worldline.json").write_text(json.dumps(data, indent=2) + "\n")
        (d / "wallpaper.svg").write_text(wallpaper(w))
    (OUT / "codes.json").write_text(json.dumps(CODES, indent=2) + "\n")
    (OUT / "default-divergence").write_text("1.048596\n")
    print("Generated %d worldline packs, codes.json, default-divergence." % len(WORLDLINES))


if __name__ == "__main__":
    main()
