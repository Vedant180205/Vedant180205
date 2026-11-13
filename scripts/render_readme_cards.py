#!/usr/bin/env python3
"""Render the animated SVG cards used by README.md.

Reads data/contributions.json and writes:
- hero.svg (Wide 1600x500 banner with monochrome portrait & technical geometry)
- social.svg
- graph.svg
- months.svg
- tile-build.svg
- tile-learn.svg
- tile-hire.svg
- about.svg
- stack.svg
- footer.svg
into cards/.
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

# ---- Palette Specification: Graphic Garden & Tech Navy --------------------
BG_CHARCOAL   = "#323232"
CARD_CREAM    = "#FEE8D0"
ACCENT_ORANGE = "#FC6F20"
SOFT_ORANGE   = "#FFAA70"
BORDER_NEUTRAL= "#D8C3AC"
DARK_TEXT     = "#323232"
MUTED_DARK    = "#685E55"
LIGHT_TEXT    = "#FEE8D0"
MUTED_LIGHT   = "#B8AFA6"
GRID_EMPTY    = "#424242"

# Hero specific colors
HERO_NAVY      = "#102B3F"
HERO_OCEAN     = "#0875D1"
HERO_PALE_BLUE = "#EAF6FE"
HERO_WHITE     = "#FFFFFF"

# Heatmap orange levels: empty + 4 intensities
HEAT_LEVELS = [
    GRID_EMPTY,
    "#7A4526",  # level 1
    "#B5531B",  # level 2
    "#E26118",  # level 3
    ACCENT_ORANGE  # level 4 (#FC6F20)
]

def esc(s):
    return html.escape(str(s), quote=True)

# ---- Font embedding (Anton, Bebas Neue, Manrope, JetBrains Mono) ------------
def font_face(family, filename, weight=400):
    p = ROOT / "fonts" / filename
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    fmt = "woff2" if filename.endswith("woff2") else "woff"
    return (
        f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;font-display:swap;"
        f"src:url('data:font/{fmt};base64,{b64}') format('{fmt}');}}\n"
    )

FONTS = "".join([
    font_face("Anton", "anton.woff2", 400),
    font_face("BebasNeue", "bebasneue.woff2", 400),
    font_face("Manrope", "manrope.woff2", 400),
    font_face("Manrope", "manrope.woff2", 600),
    font_face("Manrope", "manrope.woff2", 700),
    font_face("Manrope", "manrope.woff2", 800),
    font_face("JetBrainsMono", "jetbrainsmono.woff2", 400),
    font_face("JetBrainsMono", "jetbrainsmono.woff2", 500),
    font_face("JetBrainsMono", "jetbrainsmono.woff2", 700),
])

FONT_DISPLAY = "'Anton', 'BebasNeue', Impact, -apple-system, sans-serif"
FONT_SANS = "'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
FONT_MONO = "'JetBrainsMono', monospace"

BASE_CSS = f"""
{FONTS}
* {{ box-sizing: border-box; }}
.title-font {{ font-family: {FONT_DISPLAY}; }}
.sans {{ font-family: {FONT_SANS}; }}
.mono {{ font-family: {FONT_MONO}; }}
.fb {{ transform-box: fill-box; }}
.cs {{ display: none; }}

@keyframes rise {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
@keyframes grow {{ from {{ transform: scaleY(0); }} to {{ transform: scaleY(1); }} }}
@keyframes pop {{ 0% {{ opacity: 0; transform: scale(.4); }} 70% {{ opacity: 1; transform: scale(1.1); }} 100% {{ opacity: 1; transform: scale(1); }} }}
@keyframes nudge {{ 0%, 100% {{ transform: translate(0,0); }} 50% {{ transform: translate(3px, -3px); }} }}
@keyframes sweep {{ 0%, 70% {{ transform: translateX(-120%) skewX(-15deg); }} 100% {{ transform: translateX(360%) skewX(-15deg); }} }}

/* Hero specific animations */
@keyframes heroDiag {{ from {{ opacity: 0; transform: translateX(50px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes heroPortrait {{ from {{ opacity: 0; transform: translateY(30px); }} to {{ opacity: 1; transform: none; }} }}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation: none !important; }}
  .sh, .cf, .shine {{ display: none !important; }}
  .cs {{ display: inline !important; }}
}}
""" + ("\n*, *::before, *::after { animation: none !important; } .sh, .cf, .shine { display: none !important; } .cs { display: inline !important; }" if STATIC else "")

def A(name, dur=0.6, delay=0.0, ease="cubic-bezier(.16,1,.3,1)", extra="both"):
    if STATIC:
        return 'style="transform-box:fill-box;transform-origin:center"'
    return f'style="animation:{name} {dur}s {ease} {delay:.3f}s {extra};transform-box:fill-box;transform-origin:center"'

def svg(w, h, body, title, extra_defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{esc(title)}">\n'
        f'<title>{esc(title)}</title>\n'
        f'<defs>\n<style>\n{BASE_CSS}\n</style>\n{extra_defs}\n</defs>\n'
        f'{body}\n</svg>'
    )

def countup(x, y, n, cls, attrs, begin, dur=0.8):
    if STATIC or n <= 0:
        return f'<text x="{x}" y="{y}" class="{cls}" {attrs}>{n}</text>'
    steps = min(n, 16)
    vals = sorted({round(n * i / steps) for i in range(steps + 1)})
    out = [f'<text x="{x}" y="{y}" class="{cls} cs" {attrs}>{n}</text>']
    for i, v in enumerate(vals):
        t = begin + dur * i / len(vals)
        if i == len(vals) - 1:
            st = f'<set attributeName="visibility" to="visible" begin="{t:.3f}s" fill="freeze"/>'
        else:
            st = f'<set attributeName="visibility" to="visible" begin="{t:.3f}s" dur="{dur/len(vals):.3f}s"/>'
        out.append(f'<text x="{x}" y="{y}" class="{cls} cf" {attrs} visibility="hidden">{v}{st}</text>')
    return "".join(out)

# ---- Contribution Data Parsing ----------------------------------------------
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

# ---- 1. HERO CARD (Wide 1600 x 500) ----------------------------------------
def hero():
    W, H = 1600, 500
    
    # Check portrait image
    portrait_path = ROOT / "cards" / "portrait.png"
    portrait_b64 = ""
    if portrait_path.exists():
        portrait_b64 = base64.b64encode(portrait_path.read_bytes()).decode("ascii")

    # Procedural technical wireframe terrain on right
    wave_paths = []
    for i in range(12):
        y_offset = 120 + i * 26
        d = f"M 1150 {y_offset + 100} Q 1280 {y_offset - 60} 1420 {y_offset + 40} T 1620 {y_offset - 20}"
        opacity = 0.08 + (i / 12.0) * 0.18
        wave_paths.append(f'<path d="{d}" fill="none" stroke="#2585D8" stroke-width="1.2" stroke-opacity="{opacity:.2f}"/>')

    for j in range(14):
        x_offset = 1180 + j * 32
        d = f"M {x_offset} 200 Q {x_offset + 30} 320 {x_offset + 70} 500"
        opacity = 0.06 + (j / 14.0) * 0.14
        wave_paths.append(f'<path d="{d}" fill="none" stroke="#1D6FA8" stroke-width="1.0" stroke-opacity="{opacity:.2f}"/>')

    wireframe_svg = "".join(wave_paths)

    defs = f'''
    <clipPath id="inner-banner-clip">
      <rect x="25" y="22" width="1550" height="456" rx="4"/>
    </clipPath>
    <clipPath id="portrait-clip">
      <rect x="950" y="0" width="650" height="500"/>
    </clipPath>
    '''

    b = [
        # Outer Canvas: Deep Navy #102B3F
        f'<rect width="{W}" height="{H}" fill="{HERO_NAVY}"/>',
        
        # Inner banner container
        f'<g clip-path="url(#inner-banner-clip)">',
        f'  <rect x="25" y="22" width="1550" height="456" fill="{HERO_PALE_BLUE}" {A("fade", 0.7, 0.0)}/>',
        f'  <polygon points="1260,22 1575,22 1575,478 1020,478" fill="{HERO_NAVY}" {A("fade", 0.7, 0.1)}/>',
        f'  <polygon points="1225,22 1360,22 1080,478 945,478" fill="{HERO_OCEAN}" {A("heroDiag", 0.9, 0.2)}/>',
        f'  <g {A("fade", 1.2, 1.2)}>{wireframe_svg}</g>',
        f'</g>',
        
        # Left edge framing strip
        f'<rect x="0" y="0" width="25" height="{H}" fill="{HERO_NAVY}"/>',
        
        # Dominant Title: VEDANT PATIL
        f'<g class="title-font" font-size="142" letter-spacing="1.5">',
        f'  <text x="105" y="235" fill="{HERO_NAVY}" {A("rise", 0.8, 0.4)}>VEDANT</text>',
        f'  <text x="590" y="235" fill="{HERO_OCEAN}" {A("rise", 0.8, 0.55)}>PATIL</text>',
        f'</g>',
        
        # Subtitle with slim ocean-blue accent line
        f'<g transform="translate(105, 276)">',
        f'  <rect x="0" y="6" width="4.5" height="52" fill="{HERO_OCEAN}" rx="2" {A("grow", 0.6, 1.0)}/>',
        f'  <text class="sans" x="24" y="28" font-size="25" font-weight="600" fill="{HERO_NAVY}" letter-spacing="-0.2" {A("rise", 0.7, 1.15)}>',
        f'    <tspan x="24" dy="0">Building intelligent systems at the intersection of</tspan>',
        f'    <tspan x="24" dy="32">hardware, data and algorithms.</tspan>',
        f'  </text>',
        f'</g>',
        
        # Location: Mumbai, India
        f'<g transform="translate(105, 388)" {A("rise", 0.6, 1.5)}>',
        f'  <g transform="translate(0, 2) scale(1.15)">',
        f'    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" fill="{HERO_OCEAN}"/>',
        f'  </g>',
        f'  <text class="sans" x="30" y="20" font-size="22" font-weight="700" fill="{HERO_NAVY}">Mumbai, India</text>',
        f'</g>'
    ]

    # Right section: Cutout portrait
    if portrait_b64:
        b.append(
            f'<g clip-path="url(#portrait-clip)" {A("heroPortrait", 1.1, 0.75)}>'
            f'  <image href="data:image/png;base64,{portrait_b64}" x="1070" y="16" width="370" height="656" preserveAspectRatio="xMidYMid meet"/>'
            f'</g>'
        )

    return svg(W, H, "".join(b), "Vedant Patil — Hero Banner", defs)

# ---- 2. SOCIAL LINKS BAR ----------------------------------------------------
def social():
    W, H = 1000, 52
    items = [
        ("GitHub", "M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z", LIGHT_TEXT, "https://github.com/Vedant180205"),
        ("LinkedIn", "M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z", LIGHT_TEXT, "https://www.linkedin.com/in/vedant-patil-933190330/"),
        ("Instagram", "M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z", ACCENT_ORANGE, "https://instagram.com/vedantonmic"),
        ("Email", "M0 3v10l5-5-5-5zm1 0l7 4.5L15 3H1zm14 0l-5 5 5 5V3zm-6 6.5l-2 1.5-2-1.5L0 14h16l-6-4.5z", ACCENT_ORANGE, "mailto:vedbhumi123@gmail.com"),
        ("Portfolio", "M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z", ACCENT_ORANGE, "https://github.com/Vedant180205"),
    ]
    b = [f'<rect width="{W}" height="{H}" fill="none"/>']
    
    center_x = W / 2
    total_w = 780
    start_x = center_x - total_w / 2
    pitch = total_w / len(items)
    
    for i, (name, icon_d, col, link) in enumerate(items):
        cx = start_x + i * pitch + pitch / 2
        b.append(
            f'<g class="fb" {A("fade", 0.5, 0.1 + i*0.08)}>'
            f'<g transform="translate({cx - 48}, 16) scale(1.1)">'
            f'<path d="{icon_d}" fill="{col}"/>'
            f'</g>'
            f'<text x="{cx - 20}" y="32" class="sans" font-size="15" font-weight="600" fill="{LIGHT_TEXT}">{name}</text>'
            f'</g>'
        )
        if i < len(items) - 1:
            sep_x = start_x + (i + 1) * pitch
            b.append(f'<line x1="{sep_x}" y1="18" x2="{sep_x}" y2="34" stroke="{BORDER_NEUTRAL}" stroke-opacity="0.4" stroke-width="1.5"/>')
            
    return svg(W, H, "".join(b), "Social Links")

# ---- 3. CONTRIBUTION GRAPH --------------------------------------------------
def graph():
    W, H = 1000, 240
    b = [
        f'<rect width="{W}" height="{H}" rx="20" fill="{BG_CHARCOAL}" stroke="{BORDER_NEUTRAL}" stroke-width="1.5" stroke-opacity="0.25"/>'
    ]
    
    b.append(
        f'<g {A("fade", 0.5, 0.1)}>'
        f'<rect x="42" y="44" width="5" height="18" rx="2.5" fill="{ACCENT_ORANGE}"/>'
        f'<rect x="52" y="38" width="5" height="24" rx="2.5" fill="{ACCENT_ORANGE}"/>'
        f'<rect x="62" y="48" width="5" height="14" rx="2.5" fill="{ACCENT_ORANGE}"/>'
        f'<text x="82" y="58" class="sans" font-size="24" font-weight="700" fill="{LIGHT_TEXT}">Contribution graph</text>'
        f'<text x="955" y="56" class="mono" font-size="14" text-anchor="end" fill="{MUTED_LIGHT}">'
        f'{TOTAL:,} contributions in the last year</text>'
        f'</g>'
    )
    
    start = END - dt.timedelta(days=370)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)
    pitch, x0, y0, cell = 17.2, 42, 102, 13.5
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
        st = f'style="animation:pop .4s cubic-bezier(.16,1,.3,1) {0.15 + wk * 0.015:.3f}s both;transform-origin:center"' if not STATIC else ""
        cells.append(f'<rect class="fb" x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="3.5" fill="{HEAT_LEVELS[lv]}" {st}/>')
        if row == 0 and d.month != last_m and wk < 52:
            labels.append(f'<text x="{x:.1f}" y="92" class="mono" font-size="11" font-weight="500" fill="{MUTED_LIGHT}">{calendar.month_abbr[d.month]}</text>')
            last_m = d.month
        d += dt.timedelta(days=1)
        
    b += labels + cells
    return svg(W, H, "".join(b), f"GitHub contribution graph: {TOTAL} contributions")

# ---- 4. MONTHLY CONTRIBUTION CHART ------------------------------------------
def months():
    W, H = 1000, 320
    b = [
        f'<rect width="{W}" height="{H}" rx="20" fill="{CARD_CREAM}"/>'
    ]
    data = months_series()
    mtotal = sum(v for _, v in data)
    best = max(range(12), key=lambda i: data[i][1])
    mx = max(1, max(v for _, v in data))
    
    b.append(
        f'<g {A("fade", 0.5, 0.1)}>'
        f'<rect x="42" y="44" width="5" height="18" rx="2.5" fill="{ACCENT_ORANGE}"/>'
        f'<rect x="52" y="38" width="5" height="24" rx="2.5" fill="{ACCENT_ORANGE}"/>'
        f'<rect x="62" y="48" width="5" height="14" rx="2.5" fill="{ACCENT_ORANGE}"/>'
        f'<text x="82" y="58" class="sans" font-size="24" font-weight="700" fill="{DARK_TEXT}">Contributions by month</text>'
        f'<text x="580" y="56" class="mono" font-size="14" text-anchor="end" fill="{MUTED_DARK}">{mtotal} in 12 months</text>'
        f'</g>'
    )
    
    b.append(f'<line x1="605" y1="36" x2="605" y2="284" stroke="{BORDER_NEUTRAL}" stroke-width="1.5" stroke-opacity="0.6"/>')
    
    base, top = 246, 110
    pitch = 540 / 12
    for i, (m, v) in enumerate(data):
        h = max(4, (base - top) * v / mx)
        x = 42 + i * pitch + (pitch - 32) / 2
        col = ACCENT_ORANGE if i == best else SOFT_ORANGE
        dl = 0.2 + i * 0.04
        st_bar = f'style="transform-origin:bottom;animation:grow .5s cubic-bezier(.16,1,.3,1) {dl:.2f}s both"' if not STATIC else ""
        b.append(f'<rect class="fb" x="{x:.1f}" y="{base-h:.1f}" width="32" height="{h:.1f}" rx="4" fill="{col}" {st_bar}/>')
        b.append(f'<text x="{x+16:.1f}" y="{base+22}" class="mono" text-anchor="middle" font-size="11" font-weight="500" fill="{MUTED_DARK}">{m}</text>')
        if i == best:
            st_text = f'style="transform-origin:center;animation:pop .4s ease {dl+.3:.2f}s both"' if not STATIC else ""
            b.append(
                f'<text class="fb sans" x="{x+16:.1f}" y="{base-h-10:.1f}" text-anchor="middle" font-size="18" font-weight="800" '
                f'fill="{ACCENT_ORANGE}" {st_text}>{v}</text>'
            )
            
    b.append(f'<line x1="620" y1="160" x2="970" y2="160" stroke="{BORDER_NEUTRAL}" stroke-width="1.2" stroke-opacity="0.5"/>')
    b.append(f'<line x1="795" y1="46" x2="795" y2="274" stroke="{BORDER_NEUTRAL}" stroke-width="1.2" stroke-opacity="0.5"/>')
    
    stats_data = [
        (f"{CUR}", "day" if CUR == 1 else "days", "current streak", 
         "M11 21l-1-7H4l10-14-1 9h6l-8 12z", 630, 80),
        (f"{LONGEST}", "days", "longest streak", 
         "M12 23c-4.97 0-9-4.03-9-9 0-4.12 3.8-9.74 8.27-13.54.43-.37 1.03-.37 1.46 0C17.2 4.26 21 9.88 21 14c0 4.97-4.03 9-9 9zm0-15.5C9.5 10.5 7 13 7 15c0 2.76 2.24 5 5 5s5-2.24 5-5c0-2-2.5-4.5-5-7.5z", 820, 80),
        (f"{ACTIVE}", "days", "active in the year", 
         "M12 2L1 7l11 5 11-5-11-5zm0 8L3.5 6.5 12 3l8.5 3.5L12 10zm-11 5l11 5 11-5-2-1-9 4-9-4-2 1zm0 4l11 5 11-5-2-1-9 4-9-4-2 1z", 630, 196),
        (BUSIEST[0].strftime("%b %d") if BUSIEST[1] else "—", "", "busiest day", 
         "M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zm0-12H5V6h14v2z", 820, 196),
    ]
    
    for i, (val, unit, label, icon_d, sx, sy) in enumerate(stats_data):
        b.append(
            f'<g {A("fade", 0.5, 0.3 + i*0.1)}>'
            f'<g transform="translate({sx}, {sy}) scale(1.1)">'
            f'<path d="{icon_d}" fill="{ACCENT_ORANGE}"/>'
            f'</g>'
            f'<text x="{sx + 40}" y="{sy + 18}" class="sans" font-size="22" font-weight="800" fill="{DARK_TEXT}">'
            f'{val} <tspan font-size="14" font-weight="600" fill="{MUTED_DARK}">{unit}</tspan></text>'
            f'<text x="{sx + 40}" y="{sy + 38}" class="mono" font-size="12" font-weight="500" fill="{MUTED_DARK}">{label}</text>'
            f'</g>'
        )
        
    return svg(W, H, "".join(b), "Contributions by month and activity stats")

# ---- 5. THREE ACHIEVEMENT CARDS ---------------------------------------------
def tile(slot, label, number, caption, tags, bg, fg, border_col, is_orange=False, is_charcoal=False):
    W, H = 320, 260
    defs = f'''
    <clipPath id="tile-clip-{slot}">
      <rect width="{W}" height="{H}" rx="20"/>
    </clipPath>
    '''
    b = [
        f'<rect width="{W}" height="{H}" rx="20" fill="{bg}" stroke="{border_col}" stroke-width="1.5"/>'
    ]
    
    if is_orange:
        b.append(f'<g clip-path="url(#tile-clip-{slot})"><circle cx="{W + 20}" cy="{H + 20}" r="110" fill="{SOFT_ORANGE}"/></g>')
    elif is_charcoal:
        b.append(f'<g clip-path="url(#tile-clip-{slot})"><circle cx="{W + 20}" cy="{H + 20}" r="110" fill="{ACCENT_ORANGE}"/></g>')
    else:
        b.append(f'<g clip-path="url(#tile-clip-{slot})"><circle cx="{W + 20}" cy="{H + 20}" r="90" fill="{SOFT_ORANGE}" fill-opacity="0.3"/></g>')
        
    b.append(
        f'<g {A("fade", 0.5, 0.1)}>'
        f'<text x="24" y="38" class="mono" font-size="12" font-weight="700" letter-spacing="1.5" fill="{fg}">'
        f'{slot} &#160;·&#160; {label}</text>'
        f'<text x="{W - 24}" y="38" class="sans" font-size="20" font-weight="700" text-anchor="end" fill="{fg}">'
        f'↗</text>'
        f'</g>'
    )
    
    b.append(countup(24, 132, number, "sans", f'font-size="88" font-weight="800" letter-spacing="-2" fill="{fg}"', 0.2, 0.6))
    
    b.append(
        f'<text x="24" y="168" class="sans" font-size="18" font-weight="700" fill="{fg}" {A("rise", 0.5, 0.3)}>'
        f'{caption}</text>'
    )
    
    tag_list = [t.strip() for t in tags.split("·")]
    tx = 24
    ty = 194
    pills = []
    for t in tag_list:
        tw = len(t) * 7.5 + 24
        if is_orange:
            pfill, ptxt, pborder = SOFT_ORANGE, LIGHT_TEXT, SOFT_ORANGE
        elif is_charcoal:
            pfill, ptxt, pborder = "#424242", LIGHT_TEXT, BORDER_NEUTRAL
        else:
            pfill, ptxt, pborder = "none", DARK_TEXT, BORDER_NEUTRAL
            
        pills.append(
            f'<rect x="{tx}" y="{ty}" width="{tw}" height="26" rx="13" fill="{pfill}" stroke="{pborder}" stroke-width="1" stroke-opacity="0.8"/>'
            f'<text x="{tx + tw/2}" y="{ty + 17}" class="mono" font-size="11" font-weight="500" text-anchor="middle" fill="{ptxt}">{t}</text>'
        )
        tx += tw + 8
        
    b.append(f'<g {A("fade", 0.5, 0.4)}>' + "".join(pills) + '</g>')
    return svg(W, H, "".join(b), f"{slot} {label}: {number} {caption}", defs)

# ---- 6. ABOUT & CURRENT FOCUS CARD ------------------------------------------
def about():
    W, H = 1000, 240
    b = [f'<rect width="{W}" height="{H}" fill="none"/>']
    
    b.append(f'<line x1="30" y1="20" x2="30" y2="210" stroke="{ACCENT_ORANGE}" stroke-width="3" rx="1.5" {A("grow", 0.6, 0.1)}/>')
    
    bio_lines = [
        "I build engineering systems that work across the full",
        "spectrum — IoT, machine learning, backend, and data-driven",
        "applications. Not demos. Systems. Things that actually run",
        "end-to-end.",
        "",
        "My work spans hardware and software, sensor input and",
        "model output, raw data and production-ready endpoints.",
        "That's not accidental — that's how I think."
    ]
    b_text = []
    y_pos = 42
    for line in bio_lines:
        if line == "":
            y_pos += 12
            continue
        b_text.append(f'<tspan x="54" y="{y_pos}">{esc(line)}</tspan>')
        y_pos += 21
    b.append(f'<text class="sans" font-size="14.5" font-weight="500" fill="{LIGHT_TEXT}" line-height="1.5" {A("fade", 0.6, 0.2)}>{"".join(b_text)}</text>')
    
    b.append(f'<line x1="510" y1="20" x2="510" y2="210" stroke="{BORDER_NEUTRAL}" stroke-width="1.2" stroke-opacity="0.3"/>')
    
    rows = [
        ("M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm0-14c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z",
         "Currently focusing on",
         "Data structures &amp; algorithms · Embedded systems · Low-level programming"),
        ("M12 2L1 7l11 5 11-5-11-5zm0 8L3.5 6.5 12 3l8.5 3.5L12 10zm-11 5l11 5 11-5-2-1-9 4-9-4-2 1zm0 4l11 5 11-5-2-1-9 4-9-4-2 1z",
         "Seeking internships in",
         "ML · Quant Finance · Systems Engineering · Web Development"),
        ("M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z",
         "Engineering philosophy",
         "Correctness before optimization. Explicit assumptions, always.")
    ]
    
    ry = 36
    for i, (icon_d, title, desc) in enumerate(rows):
        is_italic = (i == 2)
        desc_style = 'font-style="italic"' if is_italic else ""
        b.append(
            f'<g {A("fade", 0.5, 0.25 + i*0.12)}>'
            f'<g transform="translate(540, {ry - 12}) scale(1.1)">'
            f'<path d="{icon_d}" fill="{ACCENT_ORANGE}"/>'
            f'</g>'
            f'<text x="578" y="{ry + 2}" class="sans" font-size="15" font-weight="700" fill="{LIGHT_TEXT}">{title}</text>'
            f'<text x="578" y="{ry + 24}" class="sans" font-size="13" font-weight="500" fill="{MUTED_LIGHT}" {desc_style}>{desc}</text>'
            f'</g>'
        )
        ry += 66
        
    return svg(W, H, "".join(b), "About and Current Focus")

# ---- 7. TECH ARSENAL CARD ---------------------------------------------------
def stack():
    W, H = 1000, 240
    clean_json_path = ROOT / "scripts" / "icons_clean.json"
    icons_dict = json.loads(clean_json_path.read_text(encoding="utf-8")) if clean_json_path.exists() else {}
    
    b = [
        f'<rect width="{W}" height="{H}" rx="20" fill="{CARD_CREAM}"/>'
    ]
    
    b.append(
        f'<g {A("fade", 0.5, 0.1)}>'
        f'<g transform="translate(42, 40) scale(1.2)">'
        f'<path d="M12 2L1 7l11 5 11-5-11-5zm0 8L3.5 6.5 12 3l8.5 3.5L12 10zm-11 5l11 5 11-5-2-1-9 4-9-4-2 1zm0 4l11 5 11-5-2-1-9 4-9-4-2 1z" fill="{ACCENT_ORANGE}"/>'
        f'</g>'
        f'<text x="82" y="58" class="sans" font-size="24" font-weight="800" fill="{DARK_TEXT}">Tech arsenal</text>'
        f'</g>'
    )
    
    categories = [
        ("LANGUAGES", False),
        ("ML / AI / DATA", False),
        ("DATABASES", False),
        ("WEB &amp; CLOUD", False),
        ("EMBEDDED", True),
        ("TOOLS", False)
    ]
    cat_x = 370
    for cname, is_active in categories:
        w_text = len(cname) * 7.2
        if is_active:
            b.append(
                f'<text x="{cat_x}" y="56" class="mono" font-size="11.5" font-weight="700" fill="{DARK_TEXT}">{cname}</text>'
                f'<line x1="{cat_x}" y1="62" x2="{cat_x + w_text}" y2="62" stroke="{DARK_TEXT}" stroke-width="2"/>'
            )
        else:
            b.append(f'<text x="{cat_x}" y="56" class="mono" font-size="11.5" font-weight="600" fill="{MUTED_DARK}">{cname}</text>')
        cat_x += w_text + 22
        
    ordered_techs = [
        "c", "cplusplus", "java", "python", "javascript", "typescript",
        "tensorflow", "pytorch", "scikitlearn", "opencv",
        "postgresql", "mongodb",
        "react", "nextjs", "nodejs", "firebase",
        "arduino", "git", "github", "vscode"
    ]
    
    tile_w, tile_h = 39.5, 48
    gap = 7.0
    start_x = 42
    tile_y = 118
    
    for i, tech in enumerate(ordered_techs):
        tx = start_x + i * (tile_w + gap)
        icon_info = icons_dict.get(tech)
        
        b.append(
            f'<g class="fb" {A("pop", 0.4, 0.15 + i*0.02)}>'
            f'<rect x="{tx:.1f}" y="{tile_y}" width="{tile_w}" height="{tile_h}" rx="10" fill="#FFFFFF" stroke="{BORDER_NEUTRAL}" stroke-width="1.2"/>'
        )
        
        if icon_info:
            vb = icon_info["viewBox"]
            content = icon_info["content"]
            b.append(
                f'<svg x="{tx + 7.7:.1f}" y="{tile_y + 12}" width="24" height="24" viewBox="{vb}">'
                f'{content}'
                f'</svg>'
            )
        b.append('</g>')
        
    return svg(W, H, "".join(b), "Tech Arsenal")

# ---- 8. FOOTER CARD ---------------------------------------------------------
def footer():
    W, H = 1000, 240
    defs = f'''
    <clipPath id="footer-clip">
      <rect width="{W}" height="{H}" rx="20"/>
    </clipPath>
    '''
    b = [
        f'<rect width="{W}" height="{H}" rx="20" fill="{BG_CHARCOAL}" stroke="{BORDER_NEUTRAL}" stroke-width="1.5" stroke-opacity="0.3"/>'
    ]
    
    shapes = f'''
    <g clip-path="url(#footer-clip)">
      <circle cx="950" cy="270" r="160" fill="{ACCENT_ORANGE}"/>
      <circle cx="870" cy="290" r="130" fill="{CARD_CREAM}" fill-opacity="0.95"/>
    </g>
    '''
    b.append(shapes)
    
    b.append(
        f'<g {A("rise", 0.6, 0.15)}>'
        f'<text x="60" y="106" class="sans" font-size="44" font-weight="800" fill="{LIGHT_TEXT}">Let’s build something</text>'
        f'<text x="60" y="162" class="sans" font-size="44" font-weight="800" fill="{LIGHT_TEXT}">'
        f'that <tspan fill="{ACCENT_ORANGE}" font-style="italic">actually</tspan> works.</text>'
        f'</g>'
    )
    
    b.append(f'<line x1="510" y1="94" x2="510" y2="156" stroke="{BORDER_NEUTRAL}" stroke-width="1.5" stroke-opacity="0.4" {A("fade", 0.6, 0.25)}/>')
    
    b.append(
        f'<g {A("rise", 0.6, 0.3)}>'
        f'<text x="540" y="112" class="mono" font-size="13" font-weight="700" letter-spacing="2" fill="{LIGHT_TEXT}">OPEN TO INTERNSHIPS</text>'
        f'<text x="540" y="142" class="mono" font-size="11.5" font-weight="500" letter-spacing="1.5" fill="{MUTED_LIGHT}">ML &#160;·&#160; QUANT &#160;·&#160; SYSTEMS &#160;·&#160; EMBEDDED</text>'
        f'</g>'
    )
    
    return svg(W, H, "".join(b), "Let's build something that actually works", defs)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cards = {
        "hero.svg": hero(),
        "social.svg": social(),
        "graph.svg": graph(),
        "months.svg": months(),
        "tile-build.svg": tile("01", "BUILD", 4, "hackathons won", "ML · IoT · Quant · Backend", ACCENT_ORANGE, LIGHT_TEXT, ACCENT_ORANGE, is_orange=True),
        "tile-learn.svg": tile("02", "LEARN", 3, "deep dives right now", "DSA · Embedded · Low-level", CARD_CREAM, DARK_TEXT, CARD_CREAM),
        "tile-hire.svg": tile("03", "OPEN TO", 4, "internship tracks", "ML · Quant · Systems · Web", BG_CHARCOAL, LIGHT_TEXT, BORDER_NEUTRAL, is_charcoal=True),
        "about.svg": about(),
        "stack.svg": stack(),
        "footer.svg": footer(),
    }
    for name, content in cards.items():
        out_file = OUT / name
        out_file.write_text(content, encoding="utf-8")
        print(f"Wrote {out_file} ({len(content)/1024:.1f} KB)")
    print(f"Done! {len(cards)} SVG cards generated successfully.")

if __name__ == "__main__":
    main()
