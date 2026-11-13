#!/usr/bin/env python3
"""Build Printful-ready SVG + transparent PNG print files for four Kojin Racers tees."""

from __future__ import annotations

import os
import re
import shutil
from collections import deque
from pathlib import Path

import numpy as np
import vtracer
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path("/workspace/kojin")
SRC = ROOT / "designs"
OUT = ROOT / "printful"
WORK = Path("/tmp/pfwork")
PREV = OUT / "previews"

# Interior-sampled brand colors (not AA-contaminated k-means centers).
# Orange-red is close to #EB3102; cream varies slightly by design.
DESIGNS = {
    "chassis-fb": {
        "src": SRC / "design-01-chassis-fb.png",
        "palette": [
            # name, RGB — darker / structural first for stacking
            ("black", (0, 0, 0)),
            ("glass", (127, 124, 119)),
            ("shadow", (198, 180, 160)),
            ("cream_mid", (225, 205, 183)),
            ("orange", (204, 61, 9)),  # stripes + wordmarks (artwork rust-orange)
            ("cream", (250, 238, 223)),
        ],
        "out_long": 5120,
        "mode": "spline",
        "corner": 40,
        "filter_speckle": 8,
        "length_threshold": 6.0,
        "has_glass": True,
        "min_cc": 3,
        "cream_ids": ("shadow", "cream_mid", "cream"),
    },
    "save-the-manuals": {
        "src": SRC / "design-03-save-the-manuals.png",
        "palette": [
            ("black", (0, 0, 0)),
            ("orange", (246, 52, 3)),
            ("cream", (254, 241, 224)),
        ],
        "out_long": 5120,
        "mode": "polygon",
        "corner": 30,
        "filter_speckle": 8,
        "length_threshold": 6.0,
        "has_glass": False,
        "min_cc": 3,
        "cream_ids": (),
    },
    "garage-crew-back": {
        "src": SRC / "design-04-garage-crew-back.png",
        "palette": [
            ("black", (0, 0, 0)),
            ("orange", (235, 49, 2)),  # #EB3102
            ("cream", (248, 232, 204)),
        ],
        "out_long": 4608,
        "mode": "polygon",
        "corner": 30,
        "filter_speckle": 8,
        "length_threshold": 6.0,
        "has_glass": False,
        "min_cc": 3,
        "cream_ids": (),
    },
    "night-run-club": {
        "src": SRC / "design-05-night-run-club.png",
        "palette": [
            ("black", (0, 0, 0)),
            ("teal", (112, 191, 172)),
            ("orange", (229, 49, 4)),
            ("cream", (252, 236, 208)),
        ],
        "out_long": 5120,
        "mode": "spline",
        "corner": 32,
        "filter_speckle": 4,  # protect thin rings and 速
        "length_threshold": 6.0,
        "has_glass": False,
        "min_cc": 3,
        "cream_ids": (),
    },
}

DARK_RGB = 28
FRINGE_PX = 2


def dilate(mask: np.ndarray, r: int = 1) -> np.ndarray:
    if r <= 0:
        return mask.copy()
    return ndi.binary_dilation(mask, iterations=r)


def erode(mask: np.ndarray, r: int = 1) -> np.ndarray:
    if r <= 0:
        return mask.copy()
    return ndi.binary_erosion(mask, iterations=r)


def count_neighbors(mask: np.ndarray) -> np.ndarray:
    """Count 8-connected True neighbors for every pixel."""
    k = np.ones((3, 3), dtype=np.uint8)
    k[1, 1] = 0
    return ndi.convolve(mask.astype(np.uint8), k, mode="constant", cval=0)


def flood_background(arr: np.ndarray, dark: int = DARK_RGB, fringe_px: int = FRINGE_PX):
    """Flood exterior transparency; only absorb thin near-black fringe, not tires / badge fills."""
    h, w = arr.shape[:2]
    rgb_max = arr[:, :, :3].max(axis=2)
    alpha = arr[:, :, 3]
    is_trans = alpha <= 16
    is_dark_op = (rgb_max <= dark) & (alpha > 16)

    bg = np.zeros((h, w), dtype=bool)
    q = deque()

    def seed(y, x):
        if not bg[y, x] and is_trans[y, x]:
            bg[y, x] = True
            q.append((y, x))

    for x in range(w):
        seed(0, x)
        seed(h - 1, x)
    for y in range(h):
        seed(y, 0)
        seed(y, w - 1)

    while q:
        y, x = q.popleft()
        if y > 0:
            seed(y - 1, x)
        if y + 1 < h:
            seed(y + 1, x)
        if x > 0:
            seed(y, x - 1)
        if x + 1 < w:
            seed(y, x + 1)

    # Absorb thin dark fringe only: dark pixels touching background that do not
    # belong to a thick dark object (tires, trim, badge fills).
    dark_left = is_dark_op & ~bg
    for _ in range(fringe_px + 1):
        n_bg = count_neighbors(bg)
        n_dark = count_neighbors(dark_left)
        # At least two background neighbors, and not buried in a dark mass.
        add = dark_left & (n_bg >= 2) & (n_dark <= 4)
        if not add.any():
            break
        bg |= add
        dark_left &= ~add

    out = arr.copy()
    out[bg] = (0, 0, 0, 0)
    return out, bg


def posterize(arr: np.ndarray, bg: np.ndarray, palette, has_glass: bool, min_cc: int):
    """Snap remaining pixels to the design palette. Recover black-matted AA edges."""
    h, w = arr.shape[:2]
    names = [n for n, _ in palette]
    pal = np.array([c for _, c in palette], dtype=np.float64)
    k = len(pal)
    black_i = names.index("black") if "black" in names else None
    glass_i = names.index("glass") if "glass" in names else None

    rgb = arr[:, :, :3].astype(np.float64)
    alpha = arr[:, :, 3]
    active = (~bg) & (alpha > 0)

    # Direct RGB distance to each palette color.
    dist = np.sqrt(((rgb[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(3))

    # Blend-with-black model for non-black palette colors (recovers matted AA).
    residual = np.full((h, w, k), 1e9, dtype=np.float64)
    coverage = np.zeros((h, w, k), dtype=np.float64)
    for i, c in enumerate(pal):
        if c.max() < 20:
            residual[:, :, i] = dist[:, :, i]
            coverage[:, :, i] = 1.0  # black is itself
            continue
        cc = float(np.dot(c, c))
        t = np.clip((rgb @ c) / cc, 0.0, 1.3)
        recon = t[:, :, None] * c
        residual[:, :, i] = np.sqrt(((rgb - recon) ** 2).sum(2))
        coverage[:, :, i] = t

    labels = np.full((h, w), -1, dtype=np.int16)

    # Confident direct matches.
    nearest = dist.argmin(2)
    mind = dist.min(2)
    confident = active & (mind <= 28)
    labels[confident] = nearest[confident]

    # Blend-model assignment for remaining active pixels.
    rest = active & (labels < 0)
    if rest.any():
        best_i = residual.argmin(2)
        best_r = residual.min(2)
        best_t = np.take_along_axis(coverage, best_i[:, :, None], 2)[:, :, 0]

        # Solid-ish coverage of a palette color (including mid-gray glass).
        snap = rest & (best_r <= 22) & (best_t >= 0.50)
        labels[snap] = best_i[snap]

        # Light coverage on the exterior: drop to transparent (don't leave a dark halo).
        rest = active & (labels < 0)
        near_bg = dilate(bg | (alpha == 0), 1)
        drop = rest & near_bg & (best_r <= 24) & (best_t < 0.50)
        # leave labels at -1 (transparent)
        # mark so we don't later force them to black
        dropped = drop

        rest = active & (labels < 0) & ~dropped
        # Remaining dark pixels are artwork blacks (enclosed or structural).
        luma = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
        if black_i is not None:
            labels[rest & (luma <= 40)] = black_i
            rest = active & (labels < 0) & ~dropped
        # Anything else: nearest palette color (force — preserves mid-grays, rust, etc.)
        labels[rest] = nearest[rest]
    else:
        dropped = np.zeros((h, w), dtype=bool)

    # Glass vs cream-black AA disambiguation: keep gray only in sizable blobs.
    if has_glass and glass_i is not None:
        glass = labels == glass_i
        labeled, nlab = ndi.label(glass, structure=np.ones((3, 3)))
        sizes = ndi.sum(glass, labeled, index=range(1, nlab + 1)) if nlab else []
        keep = np.zeros(nlab + 1, dtype=bool)
        for i, s in enumerate(sizes, start=1):
            if s >= 40:  # windows are thousands of px; AA halos are tiny
                keep[i] = True
        glass_keep = keep[labeled]
        glass_reject = glass & ~glass_keep
        # Reassign rejected "glass" via cream/black blend coverage.
        if glass_reject.any() and "cream" in names:
            cream_i = names.index("cream")
            t_cream = coverage[:, :, cream_i]
            r_cream = residual[:, :, cream_i]
            to_cream = glass_reject & (r_cream <= 28) & (t_cream >= 0.50)
            to_trans = glass_reject & ~to_cream & dilate(bg | (labels < 0) | dropped, 1)
            to_black = glass_reject & ~to_cream & ~to_trans
            labels[to_cream] = cream_i
            labels[to_trans] = -1
            if black_i is not None:
                labels[to_black] = black_i

    # Remove tiny speckles per class (not thin long lines).
    for i in range(k):
        m = labels == i
        if not m.any():
            continue
        lab, nlab = ndi.label(m, structure=np.ones((3, 3)))
        if nlab == 0:
            continue
        sizes = ndi.sum(m, lab, index=range(1, nlab + 1))
        keep = np.zeros(nlab + 1, dtype=bool)
        for j, s in enumerate(sizes, start=1):
            if s >= min_cc:
                keep[j] = True
        labels[m] = np.where(keep[lab[m]], i, -1)

    # Rebuild RGBA posterized image.
    out = np.zeros((h, w, 4), dtype=np.uint8)
    for i, (_, c) in enumerate(palette):
        m = labels == i
        out[m, 0] = c[0]
        out[m, 1] = c[1]
        out[m, 2] = c[2]
        out[m, 3] = 255
    return out, labels



def labels_to_rgba(labels, palette):
    h, w = labels.shape
    out = np.zeros((h, w, 4), dtype=np.uint8)
    for i, (_, c) in enumerate(palette):
        m = labels == i
        out[m, 0] = c[0]
        out[m, 1] = c[1]
        out[m, 2] = c[2]
        out[m, 3] = 255
    return out


def majority_smooth_creams(labels, palette, cream_names, iterations=2):
    """Reduce salt-and-pepper banding between cream shade levels without touching lines."""
    if not cream_names:
        return labels
    names = [n for n, _ in palette]
    cream_ids = [names.index(n) for n in cream_names if n in names]
    if not cream_ids:
        return labels
    out = labels.copy()
    kernel = np.ones((3, 3), dtype=np.uint8)
    for _ in range(iterations):
        cur = out
        is_cream = np.isin(cur, cream_ids)
        counts = [ndi.convolve((cur == cid).astype(np.uint8), kernel, mode="nearest") for cid in cream_ids]
        counts = np.stack(counts, 0)
        winner = np.array(cream_ids, dtype=np.int16)[counts.argmax(0)]
        cream_count = counts.sum(0)
        upd = is_cream & (cream_count >= 3)
        out = cur.copy()
        out[upd] = winner[upd]
    return out



def compactness(mask: np.ndarray) -> float:
    per = int((ndi.binary_dilation(mask) & ~mask).sum())
    area = int(mask.sum())
    if per == 0 or area == 0:
        return 0.0
    return float(4.0 * np.pi * area / (per * per))


def punch_letter_counters(labels, palette, min_area=16, max_area=2000, min_compact=0.30):
    """Turn leftover opaque-black typographic counters (A/R/O/6/kanji holes) transparent.

    Keeps complex marks such as 速 (low compactness), large fills (H-gate, badges),
    and holes inside shapes that have 3+ openings (shifter slots, wheel spokes).
    """
    names = [n for n, _ in palette]
    if "black" not in names:
        return labels
    black_i = names.index("black")
    stroke_ids = [
        names.index(n)
        for n in names
        if n in ("cream", "orange", "orange_text", "teal") or n.startswith("cream")
    ]
    out = labels.copy()
    black = labels == black_i

    # Parent cream/orange CCs with 3+ holes are graphics (H-gate, wheel), not letters.
    protected = np.zeros(black.shape, dtype=bool)
    for sid in stroke_ids:
        ink = labels == sid
        if not ink.any():
            continue
        slab, ns = ndi.label(ink, structure=np.ones((3, 3)))
        # invert ink to find holes, but only those not connected to the border
        holes = ~ink
        # flood holes from the border so only enclosed holes remain
        border = np.zeros_like(holes)
        border[0, :] = True
        border[-1, :] = True
        border[:, 0] = True
        border[:, -1] = True
        exterior = ndi.binary_propagation(border & holes, mask=holes)
        enclosed = holes & ~exterior
        hlab, nh = ndi.label(enclosed, structure=np.ones((3, 3)))
        # count holes per parent stroke CC (by looking at a 1px ring around each hole)
        from collections import Counter
        hole_counts = Counter()
        hole_parent = {}
        for hi in range(1, nh + 1):
            hm = hlab == hi
            ring = ndi.binary_dilation(hm) & ~hm
            parents = slab[ring]
            parents = parents[parents > 0]
            if parents.size == 0:
                continue
            pid = int(np.bincount(parents).argmax())
            hole_counts[pid] += 1
            hole_parent[hi] = pid
        # Measure parent bbox so we only protect large graphics (H-gate, wheel),
        # not a single kanji that happens to have 3 small counters.
        multi = set()
        for pid, c in hole_counts.items():
            if c < 3:
                continue
            ys, xs = np.where(slab == pid)
            if ys.size == 0:
                continue
            if max(int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)) >= 150:
                multi.add(pid)
        for hi, pid in hole_parent.items():
            if pid in multi:
                protected |= hlab == hi

    lab, nlab = ndi.label(black, structure=np.ones((3, 3)))
    kernel = np.ones((3, 3), dtype=bool)
    punched = 0
    dust = 0
    kept_protected = 0
    for i in range(1, nlab + 1):
        m = lab == i
        area = int(m.sum())
        if area < min_area:
            out[m] = -1
            dust += 1
            continue
        if protected[m].any():
            kept_protected += 1
            continue
        if area > max_area:
            continue
        C = compactness(m)
        if C < min_compact:
            continue
        ring = ndi.binary_dilation(m, structure=kernel) & ~m
        neigh = labels[ring]
        if neigh.size == 0:
            continue
        non_black = neigh[neigh != black_i]
        if non_black.size == 0:
            continue
        stroke = np.isin(non_black, stroke_ids).mean()
        if stroke >= 0.75:
            out[m] = -1
            punched += 1
    print(f"  counters punched={punched}, black dust dropped={dust}, protected graphic holes={kept_protected}")
    return out


def drop_small_components(labels, min_area=8):
    """Remove tiny islands of any ink color (AA crumbs) without touching thin long lines."""
    k = int(labels.max()) + 1 if labels.size and labels.max() >= 0 else 0
    out = labels.copy()
    dropped = 0
    for i in range(k):
        m = labels == i
        if not m.any():
            continue
        lab, nlab = ndi.label(m, structure=np.ones((3, 3)))
        if nlab == 0:
            continue
        sizes = ndi.sum(m, lab, index=range(1, nlab + 1))
        keep = np.zeros(nlab + 1, dtype=bool)
        for j, s in enumerate(sizes, start=1):
            if s >= min_area:
                keep[j] = True
            else:
                dropped += 1
        out[m] = np.where(keep[lab[m]], i, -1)
    if dropped:
        print(f"  dropped {dropped} small ink speckles (min_area={min_area})")
    return out


def unmatte_png(arr: np.ndarray, palette) -> np.ndarray:
    """Give semi-transparent fringe pixels a straight palette color (no black matte)."""
    out = arr.copy()
    a = out[:, :, 3]
    semi = (a > 0) & (a < 255)
    if not semi.any():
        # still force trans pixels to zero rgb
        out[a == 0] = (0, 0, 0, 0)
        return out
    pal = np.array([c for _, c in palette], dtype=np.float64)
    rgb = out[:, :, :3].astype(np.float64)
    # Decontaminate assuming blend over black: recover fg = rgb / alpha
    alpha = a[semi].astype(np.float64) / 255.0
    rec = np.clip(rgb[semi] / np.maximum(alpha[:, None], 1e-6), 0, 255)
    d = np.sqrt(((rec[:, None, :] - pal[None, :, :]) ** 2).sum(2))
    nearest = pal[d.argmin(1)]
    out[semi, :3] = np.round(nearest).astype(np.uint8)
    out[a == 0] = (0, 0, 0, 0)
    return out


def smooth_up_mask(mask: np.ndarray, factor: int = 2, sigma: float = 0.45) -> np.ndarray:
    """2x bilinear + light blur + re-threshold so vtracer fits smooth contours, not pixel stairs."""
    if factor == 1 and not sigma:
        return mask
    up = ndi.zoom(mask.astype(np.float32), factor, order=1)
    if sigma:
        up = ndi.gaussian_filter(up, sigma)
    return up >= 0.5


def extract_paths(svg_text: str, fill: str) -> str:
    """Return path elements from a vtracer SVG, with fill replaced."""
    parts = []
    # paths may be multiline
    for m in re.finditer(r"<path\b[^>]*/>", svg_text, flags=re.DOTALL):
        tag = m.group(0)
        if re.search(r'fill="[^"]*"', tag):
            tag = re.sub(r'fill="[^"]*"', f'fill="{fill}"', tag)
        else:
            tag = tag[:-2] + f' fill="{fill}"/>'
        # fill-rule evenodd helps cutout holes
        if "fill-rule" not in tag:
            tag = tag[:-2] + ' fill-rule="evenodd"/>'
        parts.append(tag)
    return "\n".join(parts)


def hex_of(rgb) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def trace_layers(labels: np.ndarray, palette, mode: str, corner: int, filter_speckle: int,
                 length_threshold: float, work: Path, name: str, factor: int = 2, sigma: float = 0.45):
    path_bits = []
    uw = uh = None
    # Paint dark / structural colors first, lightest last (palette is already ordered).
    for i, (cname, rgb) in enumerate(palette):
        mask = labels == i
        if not mask.any():
            print(f"    skip empty layer {cname}")
            continue
        mask_u = smooth_up_mask(mask, factor=factor, sigma=sigma)
        uh, uw = mask_u.shape
        img = np.full((uh, uw, 3), 255, dtype=np.uint8)
        img[mask_u] = (0, 0, 0)
        layer_png = work / f"{name}_{cname}.png"
        Image.fromarray(img).save(layer_png)
        layer_svg = work / f"{name}_{cname}.svg"
        vtracer.convert_image_to_svg_py(
            str(layer_png),
            str(layer_svg),
            colormode="binary",
            hierarchical="cutout",
            mode=mode,
            filter_speckle=filter_speckle,
            corner_threshold=corner,
            length_threshold=length_threshold,
            max_iterations=10,
            splice_threshold=45,
            path_precision=2,
        )
        text = layer_svg.read_text()
        paths = extract_paths(text, hex_of(rgb))
        n_paths = paths.count("<path")
        print(f"    layer {cname} {hex_of(rgb)}: {int(mask.mean()*1000)/10}% src px, {n_paths} paths, {layer_svg.stat().st_size} bytes, {uw}x{uh}")
        if paths:
            path_bits.append(paths)

    if uw is None:
        uh, uw = labels.shape[0] * factor, labels.shape[1] * factor
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
        f'width="{uw}" height="{uh}" viewBox="0 0 {uw} {uh}">\n'
        + "\n".join(path_bits)
        + "\n</svg>\n"
    )
    return svg, uw, uh


def rasterize_svg(svg_path: Path, png_path: Path, width: int, height: int):
    import cairosvg

    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=width,
        output_height=height,
        background_color="transparent",
    )


def make_preview(src: Image.Image, dest: Path, width: int = 800, bg=(17, 17, 17)):
    w, h = src.size
    nh = max(1, round(h * (width / w)))
    im = src.resize((width, nh), Image.Resampling.LANCZOS)
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    canvas = Image.new("RGBA", im.size, bg + (255,))
    out = Image.alpha_composite(canvas, im)
    out.convert("RGB").save(dest, optimize=True)
    return dest


def compose_on(im: Image.Image, bg_rgb):
    canvas = Image.new("RGBA", im.size, bg_rgb + (255,))
    return Image.alpha_composite(canvas, im.convert("RGBA"))


def report_image(path: Path):
    im = Image.open(path)
    arr = np.array(im.convert("RGBA"))
    a = arr[:, :, 3]
    return {
        "size": im.size,
        "mode": im.mode,
        "bytes": path.stat().st_size,
        "opaque": int((a == 255).sum()),
        "trans": int((a == 0).sum()),
        "semi": int(((a > 0) & (a < 255)).sum()),
    }


def process(name: str, cfg: dict):
    print(f"\n========== {name} ==========")
    work = WORK / name
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    im = Image.open(cfg["src"]).convert("RGBA")
    arr = np.array(im)
    print(f"  source {cfg['src'].name} {im.size} {im.mode}")

    cleaned, bg = flood_background(arr)
    n_bg = int(bg.sum())
    n_new = int(((arr[:, :, 3] > 16) & bg).sum())
    print(f"  background flood: {n_bg} px marked bg (newly absorbed opaque/dark: {n_new})")
    Image.fromarray(cleaned).save(work / "01_cleaned.png")

    poster, labels = posterize(cleaned, bg, cfg["palette"], cfg["has_glass"], cfg["min_cc"])
    labels = majority_smooth_creams(labels, cfg["palette"], cfg.get("cream_ids") or ())
    labels = punch_letter_counters(labels, cfg["palette"])
    labels = drop_small_components(labels, min_area=8)
    poster = labels_to_rgba(labels, cfg["palette"])
    # stats
    total = labels.size
    for i, (cname, rgb) in enumerate(cfg["palette"]):
        n = int((labels == i).sum())
        print(f"  posterize {cname} {hex_of(rgb)}: {n} px ({100*n/total:.2f}%)")
    n_tr = int((labels < 0).sum())
    print(f"  posterize transparent: {n_tr} px ({100*n_tr/total:.2f}%)")
    Image.fromarray(poster).save(work / "02_posterized.png")
    make_preview(Image.fromarray(poster), work / "02_posterized_preview.png", 800)

    svg_text, uw, uh = trace_layers(
        labels,
        cfg["palette"],
        mode=cfg["mode"],
        corner=cfg["corner"],
        filter_speckle=cfg["filter_speckle"],
        length_threshold=cfg.get("length_threshold", 4.0),
        work=work,
        name=name,
        factor=2,
        sigma=0.55,
    )
    svg_path = OUT / f"{name}.svg"
    svg_path.write_text(svg_text)
    print(f"  wrote {svg_path} {svg_path.stat().st_size} bytes, svg canvas {uw}x{uh}")

    # Rasterize the vector at Printful DTG size (longest side >= 4500).
    src_w, src_h = im.size
    out_long = cfg["out_long"]
    if src_w >= src_h:
        rw, rh = out_long, max(1, round(out_long * src_h / src_w))
    else:
        rh, rw = out_long, max(1, round(out_long * src_w / src_h))
    png_path = OUT / f"{name}.png"
    rasterize_svg(svg_path, png_path, rw, rh)
    # Verify / flatten to true 8-bit RGBA, no stray matte
    out_im = Image.open(png_path).convert("RGBA")
    out_arr = unmatte_png(np.array(out_im), cfg["palette"])
    out_im = Image.fromarray(out_arr, "RGBA")
    # Save optimized PNG
    out_im.save(png_path, format="PNG", optimize=True, compress_level=9)
    info = report_image(png_path)
    print(f"  wrote {png_path} {info['size']} {info['mode']} {info['bytes']/1e6:.2f}MB "
          f"opaque={info['opaque']} semi={info['semi']} trans={info['trans']}")
    if info["bytes"] >= 50 * 1000 * 1000:
        print("  WARNING: file exceeds 50MB")
    if max(info["size"]) < 4500:
        print("  WARNING: longest side < 4500")

    prev = PREV / f"{name}.png"
    make_preview(out_im, prev, 800, bg=(17, 17, 17))
    print(f"  preview {prev} {Image.open(prev).size}")

    # Also save a side-by-side QA (source vs poster vs trace) on #111
    qa_compare(arr, poster, out_im, work / "03_qa_compare.png", name)
    return {"svg": svg_path, "png": png_path, "preview": prev, "info": info, "canvas": (uw, uh)}


def qa_compare(src_arr, poster, traced_im, dest, name):
    """Source (composited), posterized, and traced SVG raster, all on #111, same 800px width."""
    w = 800
    frames = []
    for im in (
        Image.fromarray(src_arr, "RGBA"),
        Image.fromarray(poster, "RGBA"),
        traced_im,
    ):
        frames.append(make_frame(im, w))
    gap = 8
    H = max(f.height for f in frames)
    canvas = Image.new("RGB", (w * 3 + gap * 2, H + 28), (17, 17, 17))
    x = 0
    for f in frames:
        canvas.paste(f, (x, 28))
        x += w + gap
    # labels
    from PIL import ImageDraw
    d = ImageDraw.Draw(canvas)
    for i, lab in enumerate(("source", "posterized", "traced SVG")):
        d.text((i * (w + gap) + 8, 6), f"{name}  {lab}", fill=(200, 200, 200))
    canvas.save(dest)
    print(f"  QA {dest}")


def make_frame(im: Image.Image, width: int) -> Image.Image:
    w, h = im.size
    nh = max(1, round(h * (width / w)))
    im = im.resize((width, nh), Image.Resampling.LANCZOS).convert("RGBA")
    bg = Image.new("RGBA", im.size, (17, 17, 17, 255))
    return Image.alpha_composite(bg, im).convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PREV.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, cfg in DESIGNS.items():
        results[name] = process(name, cfg)
    print("\n========== DONE ==========")
    for name, r in results.items():
        print(name, r["info"], "svg", r["svg"])


if __name__ == "__main__":
    main()
