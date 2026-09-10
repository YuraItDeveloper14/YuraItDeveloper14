# -*- coding: utf-8 -*-
"""Термінальна картка: ASCII-мапа України, Київщина помаранчева, місто Київ — червоне.

Межі країни й областей — OSM (25 областей, EugeneBorshch/ukraine_geojson); межа міста —
OSM relation 421866 (Nominatim). Усі кільця областей малюються як суша: у Херсонській,
Миколаївській та Одеській OSM кладе острови й материк окремими кільцями одного полігона.
Кожна клітинка несе чесну частку покриття (BOX): область чи місто позначаються там,
де займають щонайменше половину клітинки.

    python scripts/card.py                                   # SVG із data/map_layers.json
    python scripts/card.py --oblasts UA.geojson --city kyiv.geojson   # перерахувати шари (Pillow)
"""
import argparse, io, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
LAYERS = ROOT / "data" / "map_layers.json"

KYIV_OBLAST = "UA-32"

W = 1000
COLS = 112
SUPER = 8
FS = 7.8                # кегль ASCII-мапи
CW = FS * 0.55          # виміряно в браузері: моноширинний символ = 0.55em
LH = FS                 # рядки впритул
MAP_X = 40
PAD = 30
HALF = 128              # клітинка «належить», коли покрита щонайменше наполовину

RAMP = [(150, "@"), (95, "#"), (45, "+"), (15, ":")]
REGION_CH, CITY_CH = "@", "@"
FLAG_SPLIT = 0.44       # частка висоти мапи, де синій переходить у жовтий

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
    "dark":  dict(bg="#0d1117", panel="#161b22", border="#30363d",
                  fg="#e6edf3", dim="#8b949e", accent="#a78bfa",
                  blue="#0057B7", yellow="#FFD700", orange="#ff9f1c", red="#ff3131",
                  weight="", pulse=True),
    # на білому: глибше золото, насиченіші помаранчевий і червоний, жирніші гліфи
    "light": dict(bg="#ffffff", panel="#f6f8fa", border="#d0d7de",
                  fg="#1f2328", dim="#59636e", accent="#7c3aed",
                  blue="#0050A8", yellow="#E0A100", orange="#e07b00", red="#c40012",
                  weight=' font-weight="700"', pulse=False),
}

ROWS = [
    ("Name",     "Yurii Dmytrenko"),
    ("Age",      "15"),
    ("Location", "Kyiv, Ukraine"),
    ("Role",     "Full-stack developer"),
]

SWATCHES = ["#f87171", "#fb923c", "#fbbf24", "#4ade80",
            "#22d3ee", "#60a5fa", "#a78bfa", "#f472b6"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def polygons(geom):
    return [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]


def ring_area(r):
    return abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))) / 2


def rasterize(oblasts_path, city_path):
    from PIL import Image, ImageDraw   # потрібен лише для перерахунку шарів

    d = json.load(io.open(oblasts_path, encoding="utf-8"))
    land, oblast = [], []
    for f in d["features"]:
        rings = [ring for poly in polygons(f["geometry"]) for ring in poly]
        land.extend(rings)
        if f["properties"].get("iso3166-2") == KYIV_OBLAST:
            oblast.extend(rings)

    city = json.load(io.open(city_path, encoding="utf-8"))["features"][0]["geometry"]
    # у полігоні міста найбільше кільце — межа, решта — анклави області всередині міста
    city_outer, city_holes = [], []
    for poly in polygons(city):
        rings = sorted(poly, key=ring_area, reverse=True)
        city_outer.append(rings[0])
        city_holes.extend(rings[1:])

    pts = [p for r in land for p in r]
    lon0, lon1 = min(p[0] for p in pts), max(p[0] for p in pts)
    lat0, lat1 = min(p[1] for p in pts), max(p[1] for p in pts)
    k = math.cos(math.radians((lat0 + lat1) / 2))
    rows = max(1, int(round(COLS * (CW / LH) * (lat1 - lat0) / ((lon1 - lon0) * k))))
    IW, IH = COLS * SUPER, rows * SUPER

    def project(ring):
        return [((p[0] - lon0) / (lon1 - lon0) * (IW - 1),
                 (lat1 - p[1]) / (lat1 - lat0) * (IH - 1)) for p in ring]

    def draw(rings, holes=()):
        img = Image.new("L", (IW, IH), 0)
        dr = ImageDraw.Draw(img)
        for r in rings:
            dr.polygon(project(r), fill=255)
        for h in holes:
            dr.polygon(project(h), fill=0)
        return img.resize((COLS, rows), Image.BOX).load()   # BOX = чесна частка покриття

    land_px, obl_px, city_px = draw(land), draw(oblast), draw(city_outer, city_holes)
    in_obl = [[obl_px[x, y] >= HALF for x in range(COLS)] for y in range(rows)]
    in_city = [[city_px[x, y] >= HALF for x in range(COLS)] for y in range(rows)]

    def on_contour(x, y):
        return in_obl[y][x] and any(
            not (0 <= y + dy < rows and 0 <= x + dx < COLS and in_obl[y + dy][x + dx])
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))

    base, region, town = [], [], []
    n_obl = n_contour = 0
    city_cells = []
    for y in range(rows):
        b, c, t = [], [], []
        for x in range(COLS):
            n_obl += in_obl[y][x]
            if in_city[y][x]:
                city_cells.append((x, y))
                b.append(" "); c.append(" "); t.append(CITY_CH)
                continue
            if in_obl[y][x]:              # уся площа області, не лише межа
                n_contour += on_contour(x, y)
                b.append(" "); c.append(REGION_CH); t.append(" ")
                continue
            v = land_px[x, y]
            b.append(next((g for thr, g in RAMP if v >= thr), " "))
            c.append(" "); t.append(" ")
        base.append("".join(b)); region.append("".join(c)); town.append("".join(t))

    info = dict(rows=rows, oblast=n_obl, contour=n_contour, city_cells=city_cells,
                city_loose=sum(city_px[x, y] >= 90 for y in range(rows) for x in range(COLS)))
    return base, region, town, info


def text_layer(lines, x, y, fill, weight="", animate=""):
    out = [f'<g fill="{fill}" font-size="{FS}"{weight}>{animate}']
    for i, line in enumerate(lines):
        if line.strip():
            out.append(f'<text x="{x}" y="{y + i*LH:.2f}" xml:space="preserve">'
                       f'{esc(line.rstrip())}</text>')
    out.append('</g>')
    return "\n  ".join(out)


def build(theme, base, region, town):
    t = THEMES[theme]
    rows = len(base)
    map_h = rows * LH
    H = int(40 + PAD + map_h + PAD)
    top = 40 + PAD
    my = top + FS * 0.8
    bottom = top + map_h

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="Yurii Dmytrenko, 15, full-stack developer from Kyiv, Ukraine">',
         f'<style>text{{font-family:{MONO};}}</style>',
         f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" '
         f'fill="{t["bg"]}" stroke="{t["border"]}"/>',
         f'<path d="M1 13a12 12 0 0 1 12-12h{W-26}a12 12 0 0 1 12 12v27H1z" fill="{t["panel"]}"/>',
         f'<line x1="1" y1="40" x2="{W-1}" y2="40" stroke="{t["border"]}"/>']
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        s.append(f'<circle cx="{24 + i*20}" cy="20" r="6" fill="{c}"/>')
    s.append(f'<text x="{W/2}" y="25" text-anchor="middle" font-size="12.5" '
             f'fill="{t["dim"]}">~/about</text>')

    s.append(f'<linearGradient id="flag{theme}" gradientUnits="userSpaceOnUse" '
             f'x1="0" y1="{top:.1f}" x2="0" y2="{bottom:.1f}">'
             f'<stop offset="0" stop-color="{t["blue"]}"/>'
             f'<stop offset="{FLAG_SPLIT}" stop-color="{t["blue"]}"/>'
             f'<stop offset="{FLAG_SPLIT}" stop-color="{t["yellow"]}"/>'
             f'<stop offset="1" stop-color="{t["yellow"]}"/></linearGradient>')

    s.append(text_layer(base, MAP_X, my, f"url(#flag{theme})", t["weight"]))
    s.append(text_layer(region, MAP_X, my, t["orange"], t["weight"]))
    # on white a fading red turns pink, so only the dark card breathes
    pulse = ('<animate attributeName="opacity" values="1;0.72;1" dur="2.4s" '
             'repeatCount="indefinite"/>') if t["pulse"] else ""
    s.append(text_layer(town, MAP_X, my, t["red"], ' font-weight="700"', pulse))

    x_label = int(MAP_X + COLS * CW + 56)
    x_value = x_label + 160
    span = bottom - top
    y_prompt = top + 16
    y_title = top + span * 0.20 + 10
    y_row0 = top + span * 0.38 + 10
    step = span * 0.135
    pal = 26

    s.append(f'<text x="{x_label}" y="{y_prompt:.1f}" font-size="15" fill="{t["dim"]}">'
             f'<tspan fill="{t["accent"]}">~</tspan> $ whoami</text>')
    s.append(f'<text x="{x_label}" y="{y_title:.1f}" font-size="20" font-weight="700" '
             f'fill="{t["accent"]}">MY INFO</text>')
    s.append(f'<line x1="{x_label}" y1="{y_title + 12:.1f}" x2="{W-40}" y2="{y_title + 12:.1f}" '
             f'stroke="{t["border"]}"/>')
    for i, (label, value) in enumerate(ROWS):
        y = y_row0 + i * step
        s.append(f'<text x="{x_label}" y="{y:.1f}" font-size="16" font-weight="600" '
                 f'fill="{t["accent"]}">{label}</text>')
        s.append(f'<text x="{x_value}" y="{y:.1f}" font-size="16" fill="{t["fg"]}">{esc(value)}</text>')

    y_pal = bottom - pal
    for i, c in enumerate(SWATCHES):
        s.append(f'<rect x="{x_label + i*32}" y="{y_pal:.1f}" width="{pal}" height="{pal}" '
                 f'rx="5" fill="{c}"/>')
    s.append(f'<rect x="{x_label + len(SWATCHES)*32 + 10}" y="{y_pal + 3:.1f}" width="11" '
             f'height="{pal - 6}" fill="{t["fg"]}"><animate attributeName="opacity" '
             f'values="1;1;0;0" dur="1.1s" repeatCount="indefinite"/></rect>')
    s.append('</svg>')
    return "\n".join(s), H


def main():
    ap = argparse.ArgumentParser(description="Render the profile card SVGs.")
    ap.add_argument("--oblasts", help="GeoJSON of Ukraine's oblasts; rebuilds data/map_layers.json")
    ap.add_argument("--city", help="GeoJSON of the Kyiv city boundary (OSM relation 421866)")
    args = ap.parse_args()
    if args.oblasts and args.city:
        base, region, town, info = rasterize(args.oblasts, args.city)
        LAYERS.parent.mkdir(exist_ok=True)
        LAYERS.write_text(json.dumps({"base": base, "region": region, "city": town}, indent=0),
                          encoding="utf-8")
        print("layers: %d x %d, oblast %d cells, city %d" % (COLS, info["rows"], info["oblast"],
                                                             len(info["city_cells"])))
    layers = json.loads(LAYERS.read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    for name in THEMES:
        svg, _ = build(name, layers["base"], layers["region"], layers["city"])
        (OUT / f"card-{name}.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
