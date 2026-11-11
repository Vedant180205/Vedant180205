#!/usr/bin/env python3
"""Render the animated SVG cards used by README.md.

Reads data/contributions.json (refreshed daily by the GitHub Action) and
writes hero / graph / months / tiles / stack / footer SVGs into cards/.

Usage:
    python scripts/render_readme_cards.py            # animated
    STATIC=1 python scripts/render_readme_cards.py   # static final frame (e.g. for previews/fallbacks)

Env:
    DATA=path/to/contributions.json (optional)
    OUT=path/to/cards (optional)
    STATIC=1 (optional)
"""
import base64
import calendar
import datetime as dt
import html
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DATA", ROOT / "data" / "contributions.json"))
OUT = Path(os.environ.get("OUT", ROOT / "cards"))
STATIC = os.environ.get("STATIC") == "1"

# ---- Profile configuration --------------------------------------------------
NAME = ("Vedant", "Patil")
USER = "Vedant180205"
TAGLINES = [
    "ECS engineer  ·  systems thinker",
    "ML + quant finance + IoT builder",
    "Arduino → ML pipelines → backend logic",
    "Correctness before optimization",
    "End-to-end systems, not demos",
]
META = "B.Tech Electronics & Computer Science  ·  Mumbai"
URL_GH = f"https://github.com/{USER}"

STACK = [
    ("Languages", ["C", "C++", "Java", "Python", "JavaScript", "TypeScript", "Dart"]),
    ("ML / AI / Data", ["TensorFlow", "PyTorch", "scikit-learn", "OpenCV", "NumPy", "Pandas", "Matplotlib"]),
    ("Databases", ["MySQL", "SQLite", "PostgreSQL", "Supabase", "MongoDB", "Firebase"]),
    ("Web & Cloud", ["HTML5", "CSS3", "React", "Next.js", "Node.js", "FastAPI", "Google Cloud", "Vercel", "Render"]),
    ("Embedded & Hardware", ["Arduino", "ESP32"]),
    ("Dev Tools", ["Git", "GitHub", "VS Code", "PowerShell", "Antigravity"]),
]

# ---- Palette: Warm Paper & Editorial Ink ------------------------------------
PAPER, PAPER2, INK, INK2 = "#f6f1e7", "#ece5d6", "#14110f", "#3b362f"
BLUE, RED, YELLOW = "#2547d0", "#d9382b", "#f2b705"
LEVELS = ["#e6dfcf", "#c5cef4", "#8da0ec", "#5372de", BLUE]

SERIF = "'CardSerif','Instrument Serif',Georgia,'Times New Roman',serif"
SANS = "'CardSans','Geist',-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'CardMono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def esc(s):
    return html.escape(str(s), quote=True)


# ---- Fonts embedded as base64 WOFF data URIs --------------------------------
def font_face(family, filename, weight=400):
    p = ROOT / "fonts" / filename
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    return (
        f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;font-display:swap;"
        f"src:url('data:font/woff;base64,{b64}') format('woff');}}\n"
    )


FONTS = "".join([
    font_face("CardSerif", "serif.woff", 400),
    font_face("CardSans", "sans.woff", 400),
    font_face("CardSans", "sans-bold.woff", 700),
    font_face("CardMono", "mono.woff", 400),
])

BASE_CSS = f"""
{FONTS}
.serif {{ font-family: {SERIF}; }}
.sans {{ font-family: {SANS}; }}
.mono {{ font-family: {MONO}; }}
.fb {{ transform-box: fill-box; }}
.cs {{ display: none; }}

@keyframes rise {{ from {{ opacity: 0; transform: translateY(24px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes grow {{ from {{ transform: scaleY(0); }} to {{ transform: scaleY(1); }} }}
@keyframes pop {{ 0% {{ opacity: 0; transform: scale(.2); }} 65% {{ opacity: 1; transform: scale(1.2); }} 100% {{ opacity: 1; transform: scale(1); }} }}
@keyframes swing {{ 0% {{ opacity: 0; transform: translateY(60px) rotate(-6deg); }} 60% {{ opacity: 1; transform: translateY(-8px) rotate(1.4deg); }} 80% {{ transform: translateY(2px) rotate(-.3deg); }} 100% {{ opacity: 1; transform: none; }} }}
@keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-8px); }} }}
@keyframes nudge {{ 0%, 100% {{ transform: translate(0,0); }} 50% {{ transform: translate(4px, -4px); }} }}
@keyframes beat {{ 0%, 100% {{ opacity: 1; transform: scale(1); }} 50% {{ opacity: .35; transform: scale(1.6); }} }}
@keyframes ring {{ 0% {{ opacity: .7; transform: scale(.3); }} 100% {{ opacity: 0; transform: scale(2.4); }} }}
@keyframes sweep {{ 0%, 70% {{ transform: translateX(-140%) skewX(-18deg); }} 100% {{ transform: translateX(420%) skewX(-18deg); }} }}
@keyframes cycle {{ 0% {{ opacity: 0; transform: translateY(10px); }} 4%, 18% {{ opacity: 1; transform: none; }} 23%, 100% {{ opacity: 0; transform: translateY(-6px); }} }}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; }}
  .sh, .cf, .ring, .shine {{ display: none !important; }}
  .cs {{ display: inline !important; }}
  .cy + .cy {{ display: none !important; }}
}}
""" + ("\n*, *::before, *::after { animation: none !important; } .sh, .cf, .ring, .shine { display: none !important; } .cs { display: inline !important; } .cy + .cy { display: none !important; }" if STATIC else "")


def A(name, dur=0.7, delay=0.0, ease="cubic-bezier(.2,.8,.2,1)", extra="both"):
    """Inline CSS animation shorthand."""
    if STATIC:
        return 'style="transform-box:fill-box;transform-origin:center"'
    return (
        f'style="animation:{name} {dur}s {ease} {delay:.3f}s {extra};'
        f'transform-box:fill-box;transform-origin:center"'
    )


def svg(w, h, body, title, extra_defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{esc(title)}">\n'
        f'<title>{esc(title)}</title>\n'
        f'<defs>\n<style>\n{BASE_CSS}\n</style>\n{extra_defs}\n</defs>\n'
        f'{body}\n</svg>'
    )


def card_bg(w, h, fill=PAPER, stroke=INK):
    return f'<rect x="1.5" y="1.5" width="{w-3}" height="{h-3}" rx="20" fill="{fill}" stroke="{stroke}" stroke-width="3"/>'


def countup(x, y, n, cls, attrs, begin, dur=1.0):
    """Number that counts up from 0 using SMIL <set> frames for animated rendering."""
    if STATIC or n <= 0:
        return f'<text x="{x}" y="{y}" class="{cls}" {attrs}>{n}</text>'
    steps = min(n, 18)
    vals = sorted({round(n * i / steps) for i in range(steps + 1)})
    # .cs = static final number for prefers-reduced-motion
    out = [f'<text x="{x}" y="{y}" class="{cls} cs" {attrs}>{n}</text>']
    for i, v in enumerate(vals):
        t = begin + dur * i / len(vals)
        if i == len(vals) - 1:
            st = f'<set attributeName="visibility" to="visible" begin="{t:.3f}s" fill="freeze"/>'
        else:
            st = f'<set attributeName="visibility" to="visible" begin="{t:.3f}s" dur="{dur/len(vals):.3f}s"/>'
        out.append(f'<text x="{x}" y="{y}" class="{cls} cf" {attrs} visibility="hidden">{v}{st}</text>')
    return "".join(out)


# ---- Contribution data parsing ----------------------------------------------
def load_days():
    if not DATA.exists():
        return []
    try:
        raw = json.loads(DATA.read_text(encoding="utf-8"))
        days = raw["days"] if isinstance(raw, dict) else raw
        out = [(dt.date.fromisoformat(d["date"]), int(d["count"])) for d in days]
        out.sort(key=lambda x: x[0])
        return out
    except Exception as e:
        print(f"Warning: Failed to parse contribution data: {e}", file=sys.stderr)
        return []


DAYS = load_days()
END = DAYS[-1][0] if DAYS else dt.date.today()
YEAR = [(d, c) for d, c in DAYS if d > END - dt.timedelta(days=371)]
BY_DATE = dict(YEAR)


def streaks():
    counts = [c for _, c in YEAR]
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    cur = 0
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0:
        i -= 1
    while i >= 0 and counts[i] > 0:
        cur += 1
        i -= 1
    return cur, longest


TOTAL = sum(c for _, c in YEAR)
ACTIVE = sum(1 for _, c in YEAR if c > 0)
CUR, LONGEST = streaks()
BUSIEST = max(YEAR, key=lambda x: x[1]) if YEAR else (END, 0)


def months_series():
    ym = []
    y, m = END.year, END.month
    for _ in range(12):
        ym.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    ym.reverse()
    sums = {k: 0 for k in ym}
    for d, c in DAYS:
        if (d.year, d.month) in sums:
            sums[(d.year, d.month)] += c
    return [(calendar.month_abbr[m], sums[(y, m)]) for y, m in ym]


# ---- Card 1: Hero -----------------------------------------------------------
def hero():
    W, H = 1000, 400
    b = [card_bg(W, H)]
    # Status line
    b.append(
        f'<g {A("fade", .6, .1)}><circle cx="52" cy="62" r="6" fill="{BLUE}" class="fb" '
        f'style="animation:beat 2s ease-in-out infinite;transform-origin:center"/>'
        f'<text x="70" y="67" class="mono" font-size="15" fill="{INK2}" xml:space="preserve">{esc(META)}</text></g>'
    )
    # Name typography
    grad = (
        f'<linearGradient id="shine" gradientUnits="objectBoundingBox" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset=".3" stop-color="{BLUE}" stop-opacity="0"/><stop offset=".5" stop-color="{BLUE}" stop-opacity="1"/>'
        f'<stop offset=".7" stop-color="{BLUE}" stop-opacity="0"/>'
        + ('' if STATIC else '<animateTransform attributeName="gradientTransform" type="translate" '
           'values="-1 0;1 0;1 0" keyTimes="0;.35;1" dur="5.5s" begin="1.6s" repeatCount="indefinite"/>')
        + '</linearGradient>'
    )
    b.append(f'<text x="44" y="205" class="serif" font-size="136" fill="{INK}" {A("rise", .9, .25)}>{esc(NAME[0])}</text>')
    b.append(
        f'<g {A("rise", .9, .55)}>'
        f'<text x="44" y="336" class="serif" font-size="136" fill="{INK}">{esc(NAME[1])}</text>'
        f'<text x="44" y="336" class="serif sh" font-size="136" fill="url(#shine)">{esc(NAME[1])}</text></g>'
    )
    # Geometric accent shapes
    shapes = (
        f'<g {A("pop", .8, 1.0)}><g class="fb" style="animation:float 5s ease-in-out infinite"><circle cx="790" cy="140" r="64" fill="{BLUE}" stroke="{INK}" stroke-width="3"/></g></g>'
        f'<g {A("pop", .8, 1.2)}><g class="fb" style="animation:float 6s ease-in-out -2s infinite"><rect x="850" y="150" width="96" height="96" rx="10" fill="{RED}" stroke="{INK}" stroke-width="3" transform="rotate(12 898 198)"/></g></g>'
        f'<g {A("pop", .8, 1.4)}><g class="fb" style="animation:float 5.5s ease-in-out -1s infinite"><path d="M690 250 L760 130 L830 250 Z" fill="{YELLOW}" stroke="{INK}" stroke-width="3" stroke-linejoin="round" transform="translate(-10 0)"/></g></g>'
    )
    b.append(shapes)
    # Rotating tagline
    n = len(TAGLINES)
    per = 2.8
    lines = []
    for i, t in enumerate(TAGLINES):
        st = f'style="animation:cycle {n*per}s ease-in-out {1.4 + i*per:.2f}s infinite both"' if not STATIC else ""
        lines.append(
            f'<text x="500" y="336" class="sans cy" font-size="25" font-weight="500" fill="{INK}" '
            f'{st} xml:space="preserve">{esc(t)}</text>'
        )
    b.append(f'<line x1="500" y1="290" x2="956" y2="290" stroke="{INK}" stroke-width="2" {A("fade", .6, 1.3)}/>')
    b.append("<g>" + "".join(lines) + "</g>")
    return svg(W, H, "".join(b), "Vedant Patil — ECS engineer and systems thinker", grad)


# ---- Card 2: Contribution Graph ---------------------------------------------
def graph():
    W, H = 1000, 250
    b = [card_bg(W, H)]
    b.append(f'<text x="40" y="58" class="serif" font-size="38" fill="{INK}" {A("rise", .7, 0)}>Contribution graph</text>')
    b.append(
        f'<text x="960" y="56" class="mono" text-anchor="end" font-size="14" fill="{INK2}" {A("fade", .6, .2)}>'
        f'{TOTAL:,} contributions in the last year</text>'
    )
    start = END - dt.timedelta(days=370)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # align back to Sunday
    pitch, x0, y0, cell = 17.6, 40, 100, 14.6
    nz = sorted(c for _, c in YEAR if c > 0)
    qs = [nz[int(len(nz) * p)] for p in (0.25, 0.5, 0.75)] if nz else [1, 2, 3]

    def level(c):
        if c <= 0:
            return 0
        return 1 + sum(c > q for q in qs) if c > qs[0] else 1

    cells, labels, last_m = [], [], None
    d = start
    while d <= END:
        wk = (d - start).days // 7
        row = (d.weekday() + 1) % 7
        c = BY_DATE.get(d, 0)
        lv = min(level(c), 4)
        x, y = x0 + wk * pitch, y0 + row * pitch
        st = f'style="animation:pop .5s cubic-bezier(.2,.8,.2,1) {0.2 + wk * 0.028:.3f}s both;transform-origin:center"' if not STATIC else ""
        cells.append(f'<rect class="fb" x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="3" fill="{LEVELS[lv]}" {st}/>')
        if row == 0 and d.month != last_m:
            labels.append(f'<text x="{x:.1f}" y="92" class="mono" font-size="12" fill="{INK2}">{calendar.month_abbr[d.month]}</text>')
            last_m = d.month
        d += dt.timedelta(days=1)
    b += labels + cells
    # Legend
    lx = 960 - 5 * 20 - 70
    b.append(f'<text x="{lx}" y="232" class="mono" font-size="12" text-anchor="end" fill="{INK2}">less</text>')
    for i, col_ in enumerate(LEVELS):
        b.append(f'<rect x="{lx + 10 + i*20}" y="221" width="14" height="14" rx="3" fill="{col_}"/>')
    b.append(f'<text x="{lx + 118}" y="232" class="mono" font-size="12" fill="{INK2}">more</text>')
    return svg(W, H, "".join(b), f"GitHub contribution graph: {TOTAL} contributions in the last year")


# ---- Card 3: Monthly Chart --------------------------------------------------
def months():
    W, H = 1000, 430
    b = [card_bg(W, H)]
    data = months_series()
    mtotal = sum(v for _, v in data)
    best = max(range(12), key=lambda i: data[i][1])
    mx = max(1, max(v for _, v in data))
    b.append(f'<text x="40" y="58" class="serif" font-size="38" fill="{INK}" {A("rise", .7, 0.2)}>Contributions by month</text>')
    b.append(
        f'<text x="960" y="56" class="mono" text-anchor="end" font-size="14" fill="{INK2}" {A("fade", .6, 0.4)}>'
        f'{mtotal:,} in 12 months</text>'
    )
    base, top = 290, 120
    pitch = 920 / 12
    for i, (m, v) in enumerate(data):
        h = max(3, (base - top) * v / mx)
        x = 40 + i * pitch + (pitch - 54) / 2
        col = BLUE if i == best else INK2
        dl = 0.5 + i * 0.07
        st_bar = f'style="transform-origin:bottom;animation:grow .7s cubic-bezier(.2,.8,.2,1) {dl:.2f}s both"' if not STATIC else ""
        b.append(f'<rect class="fb" x="{x:.1f}" y="{base-h:.1f}" width="54" height="{h:.1f}" rx="6" fill="{col}" {st_bar}/>')
        b.append(f'<text x="{x+27:.1f}" y="{base+24}" class="mono" text-anchor="middle" font-size="13" fill="{INK2}">{m}</text>')
        if i == best:
            st_text = f'style="transform-origin:center;animation:pop .6s ease {dl+.5:.2f}s both"' if not STATIC else ""
            b.append(
                f'<text class="fb sans" x="{x+27:.1f}" y="{base-h-12:.1f}" text-anchor="middle" font-size="24" font-weight="700" '
                f'fill="{BLUE}" {st_text}>{v}</text>'
            )
    b.append(f'<line x1="40" y1="{base}" x2="960" y2="{base}" stroke="{INK}" stroke-width="2"/>')
    # Streak & Busiest stats
    b.append(f'<line x1="40" y1="332" x2="960" y2="332" stroke="{INK}" stroke-opacity=".25" stroke-width="1.5"/>')
    stats = [
        (f"{CUR}", "days", "current streak", BLUE),
        (f"{LONGEST}", "days", "longest streak", RED),
        (f"{ACTIVE}", "days", "active in the year", YELLOW),
        (f"{BUSIEST[1]}", BUSIEST[0].strftime("%b %d") if BUSIEST[1] else "—", "busiest day", INK),
    ]
    for i, (num, unit, label, colr) in enumerate(stats):
        x = 40 + i * 230
        dl = 1.4 + i * 0.12
        b.append(
            f'<g {A("rise", .6, dl)}><circle cx="{x+6}" cy="364" r="6" fill="{colr}" stroke="{INK}" stroke-width="2"/>'
            f'<text x="{x+22}" y="374" class="serif" font-size="42" fill="{INK}">{esc(num)}</text>'
            f'<text x="{x+22+len(num)*22+8}" y="374" class="mono" font-size="14" fill="{INK2}">{esc(unit)}</text>'
            f'<text x="{x}" y="406" class="mono" font-size="13" fill="{INK2}">{esc(label)}</text></g>'
        )
    return svg(W, H, "".join(b), f"Contributions per month; best month {data[best][0]} with {data[best][1]}; current streak {CUR} days")


# ---- Card 4: Three Feature Tiles --------------------------------------------
def tile(slot, label, number, caption, sub, fill, fg, delay):
    W, H = 400, 330
    cid = f"clip{slot}"
    defs = f'<clipPath id="{cid}"><rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="20"/></clipPath>'
    st_group = f'class="fb" style="transform-origin:50% 100%;animation:swing 1.0s cubic-bezier(.2,.8,.2,1) {delay:.2f}s both"' if not STATIC else ""
    b = [f'<g {st_group}>']
    b.append(card_bg(W, H, fill, INK))
    b.append(
        f'<g clip-path="url(#{cid})">'
        f'<circle class="ring fb" cx="352" cy="52" r="26" fill="none" stroke="{fg}" stroke-width="3" '
        f'style="transform-origin:center;animation:ring 2.6s ease-out {delay+0.8:.2f}s infinite both"/>'
        f'<rect class="shine" x="0" y="0" width="70" height="{H}" fill="#fff" fill-opacity=".22" '
        f'style="animation:sweep 5.5s ease-in-out {delay+1.2:.2f}s infinite"/></g>'
    )
    b.append(f'<text x="34" y="62" class="mono" font-size="16" font-weight="400" fill="{fg}" letter-spacing="2">{esc(slot)} · {esc(label)}</text>')
    b.append(
        f'<text x="352" y="62" class="sans fb" font-size="34" font-weight="700" text-anchor="middle" fill="{fg}" '
        f'style="transform-origin:center;animation:nudge 2.4s ease-in-out {delay+0.8:.2f}s infinite">↗</text>'
    )
    b.append(countup(30, 218, number, "serif", f'font-size="150" fill="{fg}"', delay + 0.4, 0.8))
    b.append(f'<text x="36" y="262" class="sans" font-size="22" font-weight="700" fill="{fg}">{esc(caption)}</text>')
    b.append(f'<text x="36" y="298" class="mono" font-size="14" fill="{fg}" fill-opacity=".85">{esc(sub)}</text>')
    b.append("</g>")
    return svg(W, H, "".join(b), f"{label}: {number} {caption}", defs)


# ---- Card 5: Tech Arsenal ---------------------------------------------------
def stack():
    W = 1000
    chip_h, gap, x_start, x_max = 36, 12, 270, 960
    y = 120
    items, groups = [], []
    colors = [BLUE, RED, YELLOW]
    order = 0
    for gi, (name, tools) in enumerate(STACK):
        col = colors[gi % 3]
        x, gy = x_start, y
        groups.append((name, y, col))
        for t in tools:
            w = len(t) * 9.6 + 46
            if x + w > x_max:
                x, gy = x_start, gy + chip_h + gap
            items.append((t, x, gy, w, col, order))
            order += 1
            x += w + gap
        y = gy + chip_h + 30
    H = y + 10
    b = [card_bg(W, H)]
    b.append(f'<text x="40" y="66" class="serif" font-size="42" fill="{INK}" {A("rise", .7, 0.2)}>Tech arsenal</text>')
    b.append(
        f'<text x="960" y="64" class="mono" text-anchor="end" font-size="14" fill="{INK2}" {A("fade", .6, 0.4)}>'
        f'{sum(len(t) for _, t in STACK)} tools across {len(STACK)} layers</text>'
    )
    for name, gy, col in groups:
        b.append(
            f'<g {A("fade", .6, 0.5)}><rect x="40" y="{gy+13}" width="10" height="10" fill="{col}" stroke="{INK}" stroke-width="2"/>'
            f'<text x="62" y="{gy+24}" class="mono" font-size="14" fill="{INK}" letter-spacing="1">{esc(name.upper())}</text></g>'
        )
    for t, x, gy, w, col, o in items:
        dl = 0.6 + o * 0.03
        b.append(
            f'<g class="fb" style="transform-origin:center;animation:pop .45s cubic-bezier(.2,.8,.2,1) {dl:.3f}s both">'
            f'<rect x="{x:.1f}" y="{gy}" width="{w:.1f}" height="{chip_h}" rx="18" fill="{PAPER2}" stroke="{INK}" stroke-width="2"/>'
            f'<circle cx="{x+20:.1f}" cy="{gy+18}" r="5" fill="{col}"/>'
            f'<text x="{x+34:.1f}" y="{gy+23.5}" class="sans" font-size="15" font-weight="500" fill="{INK}">{esc(t)}</text></g>'
        )
    return svg(W, H, "".join(b), "Tech stack: " + "; ".join(f"{n}: {', '.join(t)}" for n, t in STACK))


# ---- Card 6: Footer ---------------------------------------------------------
def footer():
    W, H = 1000, 300
    b = [f'<rect x="1.5" y="1.5" width="{W-3}" height="{H-3}" rx="20" fill="{INK}"/>']
    b.append(f'<text x="44" y="120" class="serif" font-size="68" fill="{PAPER}" {A("rise", .9, 0.2)}>Let’s build something</text>')
    b.append(f'<text x="44" y="200" class="serif" font-size="68" fill="{PAPER}" {A("rise", .9, 0.45)}>that actually works.</text>')
    b.append(
        f'<text x="46" y="258" class="mono" font-size="15" fill="{PAPER}" fill-opacity=".8" {A("fade", .8, 0.8)} xml:space="preserve">'
        f'Open to internships  ·  ML  ·  Quant  ·  Systems  ·  Embedded</text>'
    )
    b.append(f'<g {A("pop", .7, 0.6)}><g class="fb" style="animation:float 5s ease-in-out infinite"><circle cx="840" cy="90" r="34" fill="{BLUE}"/></g></g>')
    b.append(f'<g {A("pop", .7, 0.75)}><g class="fb" style="animation:float 6s ease-in-out -2s infinite"><rect x="880" y="130" width="62" height="62" rx="8" fill="{RED}" transform="rotate(12 911 161)"/></g></g>')
    b.append(f'<g {A("pop", .7, 0.9)}><g class="fb" style="animation:float 5.5s ease-in-out -1s infinite"><path d="M760 200 L805 126 L850 200 Z" fill="{YELLOW}" stroke-linejoin="round"/></g></g>')
    return svg(W, H, "".join(b), "Let's build something that actually works")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cards = {
        "hero.svg": hero(),
        "graph.svg": graph(),
        "months.svg": months(),
        "tile-build.svg": tile("01", "BUILD", 4, "hackathons won", "ML · IoT · quant · backend", BLUE, PAPER, 0.2),
        "tile-learn.svg": tile("02", "LEARN", 3, "deep dives right now", "DSA · embedded · low-level", YELLOW, INK, 0.35),
        "tile-hire.svg": tile("03", "OPEN TO", 4, "internship tracks", "ML · quant · systems · web", RED, PAPER, 0.5),
        "stack.svg": stack(),
        "footer.svg": footer(),
    }
    for name, content in cards.items():
        out_file = OUT / name
        out_file.write_text(content, encoding="utf-8")
        print(f"Wrote {out_file} ({len(content)/1024:.1f} KB)")
    print(f"Data summary: {len(DAYS)} days, total {TOTAL}, streak {CUR}/{LONGEST}, active {ACTIVE}")


if __name__ == "__main__":
    main()
