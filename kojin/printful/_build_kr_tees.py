#!/usr/bin/env python3
"""Build Printful-ready front print files for the three Drop-01 tees that had no
Printful product yet (KR-01 Team Wordmark, KR-02 Night Session, KR-03 Garage Crew).

Source art: concept mockups /workspace/kojin-drop02/ref-kr-0{1,2,3}.jpg (identical
to the live Shopify product images). Geometry is measured in mockup pixel space
(1100x1320 mockup) and rebuilt as clean vectors, then baked into a 4500x5400
(15x18 in @ 300 DPI) Printful front canvas. All text is converted to outlines
(fontTools), all strokes are outlined to filled polygons (shapely) — the SVGs
contain only <path> fills, like the earlier set.

Fonts: Nimbus Sans Narrow Bold Oblique (URW Helvetica-Narrow clone; wordmarks,
per-line horizontal fit to the mockup widths), DejaVu Sans Mono Bold (small text).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from shapely.geometry import Polygon, LineString, Point, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

OUT = Path("/workspace/kojin/printful")
PREV = OUT / "previews"
REF = Path("/workspace/kojin-drop02")
WORD_FONT = "/usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-BoldOblique.otf"
MONO_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

W, H = 4500, 5400          # Printful front, 15x18 in @ 300 DPI
SCALE = 11.0               # print px per mockup px (art ~14 in wide)
TOP = 150                  # art top margin in print px (0.5 in)

# Colors (sampled from flat interior areas of the mockups)
CREAM = "#F2EAD7"          # (242,234,215)
ORANGE = "#FF5637"         # (255,86,55)
INK = "#191919"            # (25,25,25) near-black ink used on sand
TEE_BLACK = (36, 36, 38)   # mockup black tee  #242426
TEE_SAND = (219, 204, 175) # mockup sand tee   #DBCCAF

_fonts = {}
def font(p):
    if p not in _fonts:
        f = TTFont(p); _fonts[p] = (f, f.getGlyphSet(), f.getBestCmap())
    return _fonts[p]


class Xf:
    """mockup-space -> output-space affine (uniform scale + translate)."""
    def __init__(self, s, tx, ty):
        self.s, self.tx, self.ty = s, tx, ty
    def pt(self, x, y):
        return x * self.s + self.tx, y * self.s + self.ty
    def geom(self, g):
        return affinity.affine_transform(g, [self.s, 0, 0, self.s, self.tx, self.ty])


def text_path(fontfile, text, bbox, xf, tracking=0.0, uniform=False):
    """Outline `text`; map its ink bbox onto `bbox`=(x0,y0,x1,y1) in mockup px."""
    f, gs, cmap = font(fontfile)
    hmtx = f["hmtx"]
    if tracking == "auto":  # letter-spacing that makes the fit uniform (sx == sy)
        _, (sx0, sy0) = text_path(fontfile, text, bbox, xf, 0.0)
        bw = (bbox[2] - bbox[0]) / sx0  # natural ink width at tracking 0
        tracking = ((bbox[2] - bbox[0]) / sy0 - bw) / (f["head"].unitsPerEm * (len(text) - 1))
    x = 0.0; placed = []
    for ch in text:
        gn = cmap[ord(ch)]
        placed.append((gn, x))
        x += hmtx[gn][0] + tracking * f["head"].unitsPerEm
    bx0 = by0 = 1e9; bx1 = by1 = -1e9
    for gn, ox in placed:
        bp = BoundsPen(gs); gs[gn].draw(bp)
        if bp.bounds:
            a, b, c, d = bp.bounds
            bx0 = min(bx0, a + ox); bx1 = max(bx1, c + ox)
            by0 = min(by0, b); by1 = max(by1, d)
    x0, y0, x1, y1 = bbox
    sy = (y1 - y0) / (by1 - by0)
    sx = sy if uniform else (x1 - x0) / (bx1 - bx0)
    if uniform:  # centre horizontally in bbox
        x0 = (x0 + x1) / 2 - (bx1 - bx0) * sx / 2
    ds = []
    for gn, ox in placed:
        sp = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        # glyph (gx,gy) -> mock X = x0 + (gx+ox-bx0)*sx ; Y = y0 + (by1-gy)*sy -> output
        s, tx, ty = xf.s, xf.tx, xf.ty
        a = sx * s; d = -sy * s
        e = (x0 + (ox - bx0) * sx) * s + tx
        fy = (y0 + by1 * sy) * s + ty
        tp = TransformPen(sp, (a, 0, 0, d, e, fy))
        gs[gn].draw(tp)
        if sp.getCommands():
            ds.append(sp.getCommands())
    return " ".join(ds), (sx, sy)


def poly_d(g):
    """shapely (Multi)Polygon -> SVG path d (evenodd-safe, rings closed)."""
    if g.is_empty:
        return ""
    polys = list(g.geoms) if hasattr(g, "geoms") else [g]
    parts = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            c = list(ring.coords)[:-1]
            parts.append("M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in c) + " Z")
    return " ".join(parts)


def rrect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=64)


def rrect_ring(x0, y0, x1, y1, r, w):
    """stroke of width w centred on rounded rect (x0..x1, centreline radius r)."""
    h = w / 2
    outer = rrect(x0 - h, y0 - h, x1 + h, y1 + h, r + h)
    inner = rrect(x0 + h, y0 + h, x1 - h, y1 - h, r - h)
    return outer.difference(inner)


def circle(cx, cy, r):
    return Point(cx, cy).buffer(r, quad_segs=128)


def stroke(pts, w):
    return LineString(pts).buffer(w / 2, cap_style="flat", join_style="mitre", mitre_limit=6)


def parallelogram(xbl, ybot, ytop, width, skew):
    return Polygon([(xbl, ybot), (xbl + width, ybot), (xbl + width + skew, ytop), (xbl + skew, ytop)])


# ---------------------------------------------------------------- designs ---
# Each design returns list of (fill, kind, payload) in mockup space; kind is
# "geom" (shapely) or "text" (fontfile, text, bbox).

def kr01():
    L = []
    stripes = unary_union([parallelogram(359.4 + i * 39.6, 382.5, 352.0, 34.0, 17.6) for i in range(3)])
    L.append((ORANGE, "geom", stripes))
    L.append((CREAM, "text", (WORD_FONT, "KOJIN", (384.6, 396.6, 732.6, 480.6), 0.0)))
    L.append((CREAM, "text", (WORD_FONT, "RACERS", (376.6, 496.6, 739.6, 580.6), -0.005)))
    L.append((ORANGE, "geom", box(374.6, 606.4, 740.4, 609.6)))
    L.append((CREAM, "text", (MONO_FONT, "PACIFIC NORTHWEST / 01", (378.6, 625.6, 723.6, 643.6), 0.03)))
    return L


def car_parts():
    sw = 3.8
    body_front = [(456.0, 552.5), (390.0, 562.0), (379.0, 579.0), (384.0, 589.0), (424.0, 597.5)]
    sill = [(468.6, 597.5), (645.6, 597.5)]
    body_rear = [(690.4, 598.0), (728.0, 590.0), (727.0, 569.0), (707.0, 551.0), (633.5, 544.5)]
    cabin = [(454.0, 552.0), (497.0, 519.5), (581.0, 514.5), (633.0, 543.0)]
    roof_inner = [(480.0, 537.5), (505.0, 524.0), (578.0, 521.0), (620.0, 546.5)]
    lines = unary_union([stroke(p, sw) for p in (body_front, sill, body_rear, cabin)] + [stroke(roof_inner, 3.2)])
    wheels = []
    hubs = []
    for cx in (446.0, 668.0):
        wheels.append(circle(cx, 592.4, 23.0).difference(circle(cx, 592.4, 19.0)))
        hubs.append(circle(cx, 592.4, 9.0))
    # silhouette (everything inside the outline) -> knocks the sun out
    sil = Polygon([(456.0, 552.5), (390.0, 562.0), (379.0, 579.0), (384.0, 589.0), (424.0, 597.5),
                   (690.4, 598.0), (728.0, 590.0), (727.0, 569.0), (707.0, 551.0), (633.5, 544.5),
                   (581.0, 514.5), (497.0, 519.5)]).buffer(sw / 2, join_style="mitre")
    sil = unary_union([sil, *[circle(c, 592.4, 23.0) for c in (446.0, 668.0)]])
    return unary_union([lines, *wheels]), unary_union(hubs), sil


def kr02():
    L = []
    L.append((CREAM, "text", (WORD_FONT, "NIGHT SESSION", (360.6, 351.6, 740.6, 403.6), 0.005)))
    sun = circle(550.0, 515.0, 87.3)
    bands = unary_union([box(400, 400, 700, 518.2), box(400, 523.6, 700, 531.8),
                         box(400, 537.4, 700, 544.2), box(400, 551.0, 700, 556.0)])
    car_lines, hubs, sil = car_parts()
    L.append((ORANGE, "geom", sun.intersection(bands).difference(sil)))
    L.append((CREAM, "geom", car_lines))
    L.append((ORANGE, "geom", hubs))
    L.append((ORANGE, "geom", box(367.6, 625.9, 729.4, 628.9)))
    L.append((CREAM, "text", (MONO_FONT, "KOJIN RACERS / DRIFT CLUB", (377.6, 645.6, 720.6, 664.6), 0.04)))
    return L


def kr03():
    L = []
    L.append((INK, "geom", rrect_ring(361.9, 354.9, 738.1, 697.1, 50.5, 5.8)))
    L.append((ORANGE, "geom", rrect_ring(373.6, 366.4, 726.4, 685.6, 38.8, 3.2)))
    L.append((INK, "text", (WORD_FONT, "KOJIN RACERS", (401.6, 396.6, 700.6, 442.6), 0.0)))
    s = (688.6 - 409.6) / 12.0
    sq = []
    for r in range(3):
        for c in range(12):
            if (r + c) % 2 == 0:
                sq.append(box(409.6 + c * s, 469.6 + r * 23.3, 409.6 + (c + 1) * s, 469.6 + (r + 1) * 23.3))
    L.append((INK, "geom", unary_union(sq)))
    L.append((INK, "text", (WORD_FONT, "GARAGE CREW", (398.6, 566.6, 703.6, 612.6), 0.015)))
    L.append((INK, "text", (MONO_FONT, "PACIFIC NORTHWEST", (434.6, 635.6, 664.6, 650.6), 0.04)))
    return L


DESIGNS = {
    "team-wordmark": dict(fn=kr01, ref="ref-kr-01.jpg", tee=TEE_BLACK, code="KR-01"),
    "night-session": dict(fn=kr02, ref="ref-kr-02.jpg", tee=TEE_BLACK, code="KR-02"),
    "garage-crew-badge": dict(fn=kr03, ref="ref-kr-03.jpg", tee=TEE_SAND, code="KR-03"),
}


def layers_bounds(layers):
    gs = []
    for fill, kind, p in layers:
        if kind == "geom":
            gs.append(p)
        else:
            gs.append(box(*p[2]))
    return unary_union(gs).bounds


def render_svg(layers, xf, w, h, title):
    out = [f'<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           f'<title>{title}</title>']
    for fill, kind, p in layers:
        if kind == "geom":
            d = poly_d(xf.geom(p))
        else:
            d, _ = text_path(p[0], p[1], p[2], xf, tracking=p[3])
        out.append(f'<path fill="{fill}" fill-rule="evenodd" d="{d}"/>')
    out.append("</svg>\n")
    return "\n".join(out)


def svg2png(svg_text, w, h):
    import cairosvg, io
    b = cairosvg.svg2png(bytestring=svg_text.encode(), output_width=w, output_height=h, background_color="transparent")
    return Image.open(io.BytesIO(b)).convert("RGBA")


def compose(im, rgb):
    bg = Image.new("RGBA", im.size, rgb + (255,))
    return Image.alpha_composite(bg, im).convert("RGB")


def main():
    PREV.mkdir(parents=True, exist_ok=True)
    qa = Path("/tmp/kr/qa"); qa.mkdir(parents=True, exist_ok=True)
    from PIL import ImageDraw
    for name, cfg in DESIGNS.items():
        layers = cfg["fn"]()
        bx0, by0, bx1, by1 = layers_bounds(layers)
        cx = (bx0 + bx1) / 2
        xf = Xf(SCALE, W / 2 - cx * SCALE, TOP - by0 * SCALE)
        svg = render_svg(layers, xf, W, H, f"Kojin Racers {cfg['code']} {name} front 15x18in @300dpi")
        (OUT / f"{name}.svg").write_text(svg)
        png = svg2png(svg, W, H)
        png.save(OUT / f"{name}.png", dpi=(300, 300), optimize=True)
        a = np.array(png)[:, :, 3]
        ys, xs = np.nonzero(a)
        print(f"{name}: art bbox x {xs.min()}-{xs.max()} y {ys.min()}-{ys.max()} "
              f"({(xs.max()-xs.min()+1)/300:.2f}x{(ys.max()-ys.min()+1)/300:.2f} in)")
        # preview on tee colour, 800px wide like the earlier previews
        pv = compose(png.resize((800, 960), Image.LANCZOS), cfg["tee"])
        pv.save(PREV / f"{name}.png", optimize=True)
        # QA: mockup-space render overlaid at native mockup resolution
        mxf = Xf(1.0, 0.0, 0.0)
        msvg = render_svg(layers, mxf, 1100, 1320, name)
        m = svg2png(msvg.replace('width="1100" height="1320"', 'width="1100" height="1320"'), 1100, 1320)
        ref = Image.open(REF / cfg["ref"]).convert("RGB")
        pad = 20
        crop = (int(bx0) - pad, int(by0) - pad, int(bx1) + pad, int(by1) + pad)
        rc = ref.crop(crop)
        mine = compose(m.crop(crop), cfg["tee"])
        # difference heat
        diff = np.abs(np.asarray(rc, float) - np.asarray(mine, float)).mean(2)
        print(f"   mean abs diff vs mockup (crop): {diff.mean():.2f}")
        Image.fromarray(np.clip(diff * 3, 0, 255).astype(np.uint8)).resize((rc.width * 2, rc.height * 2)).save(qa / f"{name}-diff.png")
        # overlay blink-style: mockup left, mine right at 2x
        k = 2
        both = Image.new("RGB", (rc.width * 2 * k + 10, rc.height * k), (0, 0, 0))
        both.paste(rc.resize((rc.width * k, rc.height * k), Image.LANCZOS), (0, 0))
        both.paste(mine.resize((rc.width * k, rc.height * k), Image.LANCZOS), (rc.width * k + 10, 0))
        both.save(qa / f"{name}-qa.png")
        # side-by-side compare: full mockup | mockup cropped to the same 15x18in
        # framing as the print file | print file composited on tee colour
        hh = 960
        refr = ref.resize((round(ref.width * hh / ref.height), hh), Image.LANCZOS)
        fx0 = (0 - xf.tx) / xf.s; fy0 = (0 - xf.ty) / xf.s
        fx1 = (W - xf.tx) / xf.s; fy1 = (H - xf.ty) / xf.s
        frame = ref.crop((round(fx0), round(fy0), round(fx1), round(fy1))).resize((800, 960), Image.LANCZOS)
        gap = 24
        cmp_ = Image.new("RGB", (refr.width + 800 * 2 + gap * 2, hh + 40), (17, 17, 17))
        cmp_.paste(refr, (0, 40)); cmp_.paste(frame, (refr.width + gap, 40))
        cmp_.paste(pv, (refr.width + 800 + gap * 2, 40))
        d = ImageDraw.Draw(cmp_)
        d.text((8, 12), f"{cfg['code']} concept mockup ({cfg['ref']})", fill=(220, 220, 220))
        d.text((refr.width + gap + 8, 12), "mockup, same 15x18in framing as print file", fill=(220, 220, 220))
        d.text((refr.width + 800 + gap * 2 + 8, 12), f"{name}.png (vector) on tee colour", fill=(220, 220, 220))
        cmp_.save(PREV / f"{name}-compare.png", optimize=True)

if __name__ == "__main__":
    main()
