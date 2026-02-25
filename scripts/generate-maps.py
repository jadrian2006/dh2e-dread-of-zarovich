#!/usr/bin/env python3
"""
generate-maps.py — SVG battle map generator for Dread of Zarovich (Foundry VTT)

Generates 19 SVG maps using only Python stdlib. Each map uses a themed color
palette and contains rooms, corridors, doors, features, grid overlay, and title.

Usage:
    python3 scripts/generate-maps.py

Output:
    assets/maps/*.svg (19 files)
"""

import math
import os
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Color Palettes
# ---------------------------------------------------------------------------

PALETTES = {
    "gothic_imperial": {
        "bg": "#1a1a1e",
        "floor": "#2a2a30",
        "wall": "#0a0a0e",
        "accent": "#8b7355",
        "text": "#c0b090",
    },
    "imperial_metal": {
        "bg": "#1e2025",
        "floor": "#2d3035",
        "wall": "#15171a",
        "accent": "#c8a832",
        "text": "#a0a8b0",
    },
    "organic_corrupt": {
        "bg": "#1a0a1e",
        "floor": "#2a1530",
        "wall": "#0e050f",
        "accent": "#cc44aa",
        "text": "#d088cc",
    },
    "clinical_horror": {
        "bg": "#0a1a0a",
        "floor": "#1a2a1a",
        "wall": "#051005",
        "accent": "#33cc66",
        "text": "#88cc88",
    },
    "alien_vault": {
        "bg": "#0a0a2e",
        "floor": "#151535",
        "wall": "#050518",
        "accent": "#d4a846",
        "text": "#a0a0d0",
    },
    "castle_gothic": {
        "bg": "#1e0a0a",
        "floor": "#2e1515",
        "wall": "#0e0505",
        "accent": "#8b1a1a",
        "text": "#c0a0a0",
    },
}

# ---------------------------------------------------------------------------
# SVG Namespace helpers
# ---------------------------------------------------------------------------

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"


def _se(parent, tag, **attrs):
    """Create a SubElement with string attributes."""
    el = ET.SubElement(parent, tag)
    for k, v in attrs.items():
        el.set(k.replace("_", "-"), str(v))
    return el


def create_svg(w, h):
    """Return root <svg> element sized w x h."""
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)
    root = ET.Element("svg")
    root.set("xmlns", SVG_NS)
    root.set("xmlns:xlink", XLINK_NS)
    root.set("viewBox", f"0 0 {w} {h}")
    root.set("width", str(w))
    root.set("height", str(h))
    return root


# ---------------------------------------------------------------------------
# Reusable SVG Component Functions
# ---------------------------------------------------------------------------


def render_background(parent, w, h, palette):
    """Radial-gradient background rectangle."""
    defs = _se(parent, "defs")
    grad = _se(defs, "radialGradient", id="bgGrad", cx="50%", cy="50%", r="70%")
    # Center is slightly lighter
    bg = palette["bg"]
    r_int = int(bg[1:3], 16)
    g_int = int(bg[3:5], 16)
    b_int = int(bg[5:7], 16)
    lighter = "#{:02x}{:02x}{:02x}".format(
        min(255, r_int + 20), min(255, g_int + 20), min(255, b_int + 20)
    )
    darker = "#{:02x}{:02x}{:02x}".format(
        max(0, r_int - 10), max(0, g_int - 10), max(0, b_int - 10)
    )
    _se(grad, "stop", offset="0%", stop_color=lighter)
    _se(grad, "stop", offset="100%", stop_color=darker)
    _se(parent, "rect", x="0", y="0", width=str(w), height=str(h), fill="url(#bgGrad)")


def render_grid(parent, w, h, color="#ffffff", opacity="0.05"):
    """Subtle 100px grid lines."""
    g = _se(parent, "g", opacity=str(opacity), stroke=color, stroke_width="1")
    for x in range(0, w + 1, 100):
        _se(g, "line", x1=str(x), y1="0", x2=str(x), y2=str(h))
    for y in range(0, h + 1, 100):
        _se(g, "line", x1="0", y1=str(y), x2=str(w), y2=str(y))


def render_room(parent, x, y, w, h, label, palette, highlight=False):
    """Filled rect with wall stroke and centered label."""
    fill = palette["accent"] if highlight else palette["floor"]
    stroke_w = "4" if highlight else "3"
    _se(
        parent, "rect",
        x=str(x), y=str(y), width=str(w), height=str(h),
        fill=fill, stroke=palette["wall"], stroke_width=stroke_w,
    )
    # Inner accent border for highlighted rooms
    if highlight:
        _se(
            parent, "rect",
            x=str(x + 4), y=str(y + 4),
            width=str(w - 8), height=str(h - 8),
            fill="none", stroke=palette["text"], stroke_width="1",
            stroke_dasharray="8,4", opacity="0.5",
        )
    # Label
    if label:
        tx = x + w // 2
        ty = y + h // 2
        txt = _se(
            parent, "text",
            x=str(tx), y=str(ty),
            fill=palette["text"],
            font_size="14", font_weight="bold",
            text_anchor="middle", dominant_baseline="central",
            font_family="monospace",
        )
        # Word-wrap long labels across two lines
        parts = label.split("/")
        if len(parts) > 1:
            txt.set("y", str(ty - 8))
            txt.text = parts[0].strip()
            _se(
                parent, "text",
                x=str(tx), y=str(ty + 10),
                fill=palette["text"],
                font_size="12", text_anchor="middle",
                dominant_baseline="central",
                font_family="monospace",
            ).text = parts[1].strip()
        else:
            txt.text = label


def render_corridor(parent, x1, y1, x2, y2, width, palette):
    """Rectangle corridor connecting two points."""
    if x1 == x2:
        # Vertical corridor
        min_y, max_y = min(y1, y2), max(y1, y2)
        _se(
            parent, "rect",
            x=str(x1 - width // 2), y=str(min_y),
            width=str(width), height=str(max_y - min_y),
            fill=palette["floor"], stroke=palette["wall"], stroke_width="2",
        )
    elif y1 == y2:
        # Horizontal corridor
        min_x, max_x = min(x1, x2), max(x1, x2)
        _se(
            parent, "rect",
            x=str(min_x), y=str(y1 - width // 2),
            width=str(max_x - min_x), height=str(width),
            fill=palette["floor"], stroke=palette["wall"], stroke_width="2",
        )
    else:
        # Angled — use a thick line
        _se(
            parent, "line",
            x1=str(x1), y1=str(y1), x2=str(x2), y2=str(y2),
            stroke=palette["floor"], stroke_width=str(width),
        )
        _se(
            parent, "line",
            x1=str(x1), y1=str(y1), x2=str(x2), y2=str(y2),
            stroke=palette["wall"], stroke_width=str(width + 4),
            opacity="0.3",
        )


def render_door(parent, x, y, orientation="h", door_type="normal"):
    """Door marker: rect=normal, circle=locked, triangle=trapped."""
    if door_type == "locked":
        _se(
            parent, "circle",
            cx=str(x), cy=str(y), r="8",
            fill="#cc3333", stroke="#ffcc00", stroke_width="2",
        )
    elif door_type == "trapped":
        if orientation == "h":
            pts = f"{x},{y - 10} {x - 8},{y + 6} {x + 8},{y + 6}"
        else:
            pts = f"{x - 10},{y} {x + 6},{y - 8} {x + 6},{y + 8}"
        _se(
            parent, "polygon",
            points=pts,
            fill="#ff6600", stroke="#ffcc00", stroke_width="2",
        )
    else:
        # Normal door — small gap
        if orientation == "h":
            _se(
                parent, "rect",
                x=str(x - 10), y=str(y - 4),
                width="20", height="8",
                fill="#8b7355", stroke="#c0b090", stroke_width="1",
            )
        else:
            _se(
                parent, "rect",
                x=str(x - 4), y=str(y - 10),
                width="8", height="20",
                fill="#8b7355", stroke="#c0b090", stroke_width="1",
            )


def render_feature(parent, x, y, feat_type, label="", palette=None):
    """Small icon feature.
    Types: altar, fountain, crate, table, crystal, warp, pillar, well,
           brazier, monument, stone
    """
    pal_text = (palette or {}).get("text", "#c0b090")
    pal_accent = (palette or {}).get("accent", "#8b7355")

    if feat_type in ("altar", "fountain", "well", "stone", "pillar"):
        _se(
            parent, "circle",
            cx=str(x), cy=str(y), r="15" if feat_type != "pillar" else "12",
            fill=pal_accent, stroke=pal_text, stroke_width="2",
            opacity="0.8",
        )
    elif feat_type in ("crate", "table"):
        sz = 20 if feat_type == "crate" else 30
        _se(
            parent, "rect",
            x=str(x - sz // 2), y=str(y - sz // 2),
            width=str(sz), height=str(sz),
            fill=pal_accent, stroke=pal_text, stroke_width="2",
            opacity="0.7",
        )
    elif feat_type in ("crystal", "diamond"):
        pts = f"{x},{y - 18} {x + 12},{y} {x},{y + 18} {x - 12},{y}"
        _se(
            parent, "polygon",
            points=pts,
            fill="#d4a846", stroke="#ffffff", stroke_width="2",
            opacity="0.9",
        )
    elif feat_type == "warp":
        # Star (8-point)
        pts_list = []
        for i in range(16):
            angle = math.pi * 2 * i / 16 - math.pi / 2
            r = 18 if i % 2 == 0 else 9
            px = x + r * math.cos(angle)
            py = y + r * math.sin(angle)
            pts_list.append(f"{px:.1f},{py:.1f}")
        _se(
            parent, "polygon",
            points=" ".join(pts_list),
            fill="#cc44aa", stroke="#ff88dd", stroke_width="1",
            opacity="0.8",
        )
    elif feat_type == "brazier":
        _se(
            parent, "circle",
            cx=str(x), cy=str(y), r="12",
            fill="#cc6600", stroke="#ffaa00", stroke_width="2",
        )
        _se(
            parent, "circle",
            cx=str(x), cy=str(y), r="6",
            fill="#ff8800", stroke="none", opacity="0.6",
        )
    elif feat_type == "monument":
        _se(
            parent, "rect",
            x=str(x - 8), y=str(y - 20),
            width="16", height="40",
            fill="#888888", stroke="#aaaaaa", stroke_width="2",
        )

    # Optional label
    if label:
        _se(
            parent, "text",
            x=str(x), y=str(y + 28),
            fill=pal_text, font_size="10",
            text_anchor="middle", font_family="monospace",
            opacity="0.7",
        ).text = label


def render_title(parent, w, h, title):
    """Map title watermark at bottom-right."""
    _se(
        parent, "text",
        x=str(w - 20), y=str(h - 15),
        fill="#ffffff", font_size="20",
        text_anchor="end", font_family="monospace",
        opacity="0.15",
    ).text = title


def render_hex_room(parent, cx, cy, radius, label, palette, highlight=False):
    """Regular hexagon room centered at (cx, cy)."""
    pts = []
    for i in range(6):
        angle = math.pi / 3 * i - math.pi / 6  # flat-top hex
        px = cx + radius * math.cos(angle)
        py = cy + radius * math.sin(angle)
        pts.append(f"{px:.1f},{py:.1f}")
    fill = palette["accent"] if highlight else palette["floor"]
    _se(
        parent, "polygon",
        points=" ".join(pts),
        fill=fill, stroke=palette["wall"], stroke_width="3",
    )
    if highlight:
        # Inner sigil ring
        _se(
            parent, "circle",
            cx=str(cx), cy=str(cy), r=str(int(radius * 0.6)),
            fill="none", stroke=palette["accent"], stroke_width="1",
            stroke_dasharray="6,4", opacity="0.5",
        )
    if label:
        txt = _se(
            parent, "text",
            x=str(cx), y=str(cy),
            fill=palette["text"],
            font_size="13", font_weight="bold",
            text_anchor="middle", dominant_baseline="central",
            font_family="monospace",
        )
        parts = label.split("/")
        if len(parts) > 1:
            txt.set("y", str(cy - 8))
            txt.text = parts[0].strip()
            _se(
                parent, "text",
                x=str(cx), y=str(cy + 10),
                fill=palette["text"],
                font_size="11", text_anchor="middle",
                dominant_baseline="central", font_family="monospace",
            ).text = parts[1].strip()
        else:
            txt.text = label


def render_sigil_circle(parent, cx, cy, r, palette):
    """Gold containment sigil circle with inner pattern."""
    _se(
        parent, "circle",
        cx=str(cx), cy=str(cy), r=str(r),
        fill="none", stroke=palette["accent"], stroke_width="2",
        opacity="0.6",
    )
    # Inner cross pattern
    _se(parent, "line", x1=str(cx - r), y1=str(cy), x2=str(cx + r), y2=str(cy),
        stroke=palette["accent"], stroke_width="1", opacity="0.3")
    _se(parent, "line", x1=str(cx), y1=str(cy - r), x2=str(cx), y2=str(cy + r),
        stroke=palette["accent"], stroke_width="1", opacity="0.3")
    # Small inner circle
    _se(
        parent, "circle",
        cx=str(cx), cy=str(cy), r=str(r // 3),
        fill="none", stroke=palette["accent"], stroke_width="1",
        opacity="0.4", stroke_dasharray="4,3",
    )


def render_hex_corridor(parent, x1, y1, x2, y2, width, palette):
    """Corridor between hex rooms — thick translucent line."""
    _se(
        parent, "line",
        x1=str(x1), y1=str(y1), x2=str(x2), y2=str(y2),
        stroke=palette["floor"], stroke_width=str(width),
        stroke_linecap="round",
    )
    _se(
        parent, "line",
        x1=str(x1), y1=str(y1), x2=str(x2), y2=str(y2),
        stroke=palette["wall"], stroke_width=str(width + 6),
        opacity="0.25", stroke_linecap="round",
    )


def render_hull_outline(parent, w, h, palette, organic=False):
    """Elongated ship hull outline (pointed bow on left, flat stern on right)."""
    margin = 100
    bow_indent = 300
    pts = [
        (margin + bow_indent, margin),                     # bow top
        (w - margin, margin),                               # stern top
        (w - margin, h - margin),                           # stern bottom
        (margin + bow_indent, h - margin),                  # bow bottom
        (margin, h // 2),                                   # bow point
    ]
    pts_str = " ".join(f"{x},{y}" for x, y in pts)
    _se(
        parent, "polygon",
        points=pts_str,
        fill="none", stroke=palette["wall"], stroke_width="5",
    )
    # If organic, add wavy vein lines inside
    if organic:
        g = _se(parent, "g", opacity="0.15", stroke=palette["accent"], stroke_width="2")
        for i in range(5):
            y_off = margin + 100 + i * ((h - 2 * margin - 200) // 4)
            # Wavy line using a polyline
            wave_pts = []
            for px in range(margin + bow_indent, w - margin, 40):
                py = y_off + 20 * math.sin(px / 80.0 + i)
                wave_pts.append(f"{px:.0f},{py:.0f}")
            _se(g, "polyline", points=" ".join(wave_pts), fill="none")


def render_outer_wall(parent, x, y, w, h, palette, gaps=None):
    """Rectangular wall outline with optional gaps (for ruins)."""
    if gaps:
        # Draw walls as separate line segments with gaps
        sides = [
            ((x, y), (x + w, y)),           # top
            ((x + w, y), (x + w, y + h)),   # right
            ((x + w, y + h), (x, y + h)),   # bottom
            ((x, y + h), (x, y)),            # left
        ]
        for side_idx, ((sx, sy), (ex, ey)) in enumerate(sides):
            if side_idx in gaps:
                # Draw with a gap in the middle
                mx = (sx + ex) // 2
                my = (sy + ey) // 2
                _se(parent, "line", x1=str(sx), y1=str(sy),
                    x2=str((sx + mx) // 2 + 30), y2=str((sy + my) // 2 + 30),
                    stroke=palette["wall"], stroke_width="4")
                _se(parent, "line",
                    x1=str((mx + ex) // 2 - 30), y1=str((my + ey) // 2 - 30),
                    x2=str(ex), y2=str(ey),
                    stroke=palette["wall"], stroke_width="4")
            else:
                _se(parent, "line", x1=str(sx), y1=str(sy), x2=str(ex), y2=str(ey),
                    stroke=palette["wall"], stroke_width="4")
    else:
        _se(
            parent, "rect",
            x=str(x), y=str(y), width=str(w), height=str(h),
            fill="none", stroke=palette["wall"], stroke_width="4",
        )


def render_road(parent, points, palette, width=80):
    """A road or path from a list of (x,y) tuples."""
    pts_str = " ".join(f"{x},{y}" for x, y in points)
    _se(
        parent, "polyline",
        points=pts_str,
        fill="none", stroke=palette["floor"], stroke_width=str(width),
        stroke_linecap="round", stroke_linejoin="round", opacity="0.6",
    )


def render_circle_area(parent, cx, cy, r, palette, label="", fill_override=None):
    """Circular area (arena, hilltop, etc.)."""
    _se(
        parent, "circle",
        cx=str(cx), cy=str(cy), r=str(r),
        fill=fill_override or palette["floor"],
        stroke=palette["wall"], stroke_width="3",
    )
    if label:
        _se(
            parent, "text",
            x=str(cx), y=str(cy),
            fill=palette["text"], font_size="14", font_weight="bold",
            text_anchor="middle", dominant_baseline="central",
            font_family="monospace",
        ).text = label


def render_vineyard_rows(parent, x, y, w, h, palette, rows=8):
    """Parallel diagonal lines for vineyard/crop rows."""
    g = _se(parent, "g", opacity="0.25", stroke=palette["accent"], stroke_width="2")
    spacing = h // rows
    for i in range(rows):
        ry = y + i * spacing
        _se(g, "line", x1=str(x), y1=str(ry), x2=str(x + w), y2=str(ry))


def render_water(parent, x, y, w, h, opacity="0.3"):
    """Semi-transparent water overlay."""
    _se(
        parent, "rect",
        x=str(x), y=str(y), width=str(w), height=str(h),
        fill="#1a3a5a", stroke="none", opacity=str(opacity),
    )
    # Subtle wave lines
    g = _se(parent, "g", opacity="0.1", stroke="#4488bb", stroke_width="1")
    for wy in range(y, y + h, 60):
        wave_pts = []
        for wx in range(x, x + w, 30):
            py = wy + 8 * math.sin(wx / 50.0 + wy / 40.0)
            wave_pts.append(f"{wx},{py:.0f}")
        if wave_pts:
            _se(g, "polyline", points=" ".join(wave_pts), fill="none")


def render_stairs(parent, x, y, orientation="down", palette=None):
    """Small stair marker."""
    pal_text = (palette or {}).get("text", "#c0b090")
    _se(parent, "rect", x=str(x - 15), y=str(y - 15), width="30", height="30",
        fill="none", stroke=pal_text, stroke_width="1")
    # Arrow direction
    if orientation == "down":
        _se(parent, "polygon",
            points=f"{x},{y + 10} {x - 8},{y - 5} {x + 8},{y - 5}",
            fill=pal_text, opacity="0.6")
    else:
        _se(parent, "polygon",
            points=f"{x},{y - 10} {x - 8},{y + 5} {x + 8},{y + 5}",
            fill=pal_text, opacity="0.6")
    _se(parent, "text", x=str(x), y=str(y + 28), fill=pal_text,
        font_size="9", text_anchor="middle", font_family="monospace",
        opacity="0.6").text = "Stairs " + orientation.capitalize()


# ---------------------------------------------------------------------------
# Map Layout Functions
# ---------------------------------------------------------------------------


def layout_village_barovus(parent, palette):
    """Map 1: Village of Barovus — 4000x3000"""
    # Village walls (outer boundary)
    render_outer_wall(parent, 200, 200, 3600, 2600, palette)

    # Burgomaster's Manor — top-center
    render_room(parent, 1600, 300, 800, 600, "Burgomaster's/Manor", palette, highlight=True)
    render_door(parent, 2000, 900, "v", "normal")

    # Chapel — right of manor
    render_room(parent, 2700, 400, 400, 400, "Chapel", palette)
    render_feature(parent, 2900, 600, "altar", "Altar", palette)

    # Tavern — left side
    render_room(parent, 400, 500, 500, 400, "Blood of the/Vine Tavern", palette)
    render_door(parent, 900, 700, "v", "normal")

    # Market Square — center
    render_room(parent, 1500, 1200, 600, 400, "Market Square", palette)

    # Hab-blocks — bottom half
    for i, lbl in enumerate(["Hab-Block A", "Hab-Block B", "Hab-Block C", "Hab-Block D"]):
        bx = 400 + i * 500
        render_room(parent, bx, 1900, 300, 200, lbl, palette)

    # Roads connecting
    render_road(parent, [(2000, 900), (2000, 1200)], palette, 60)
    render_road(parent, [(900, 700), (1500, 700), (1500, 1200)], palette, 60)
    render_road(parent, [(2100, 1600), (2100, 1900)], palette, 60)
    render_road(parent, [(550, 1900), (550 + 1500, 1900)], palette, 60)

    # Gate at bottom
    render_room(parent, 1900, 2700, 200, 100, "Gate", palette)
    render_road(parent, [(2000, 2700), (2000, 2200)], palette, 60)

    # Misc features
    render_feature(parent, 1800, 1400, "well", "Well", palette)
    render_feature(parent, 600, 1400, "crate", "Supplies", palette)


def layout_vessel_upper(parent, palette):
    """Map 2: Vessel Upper Deck — 4000x2500"""
    render_hull_outline(parent, 4000, 2500, palette)

    # Central corridor spine
    render_corridor(parent, 500, 1250, 3700, 1250, 100, palette)

    # Bridge (UD1) — bow
    render_room(parent, 500, 900, 600, 400, "UD1: Bridge", palette, highlight=True)
    render_door(parent, 1100, 1100, "v")

    # Officers' Quarters (UD2)
    render_room(parent, 1200, 700, 400, 300, "UD2: Officers'/Quarters", palette)
    render_door(parent, 1400, 1000, "h")

    # Observation Dome (UD3)
    render_room(parent, 1200, 1400, 400, 400, "UD3: Observation/Dome", palette)
    render_feature(parent, 1400, 1600, "crystal", "", palette)

    # Armory (UD4)
    render_room(parent, 1700, 700, 300, 300, "UD4: Armory", palette)
    render_door(parent, 1850, 1000, "h", "locked")
    render_feature(parent, 1850, 850, "crate", "", palette)

    # Medicae Bay (UD5)
    render_room(parent, 2100, 700, 300, 300, "UD5: Medicae/Bay", palette)
    render_door(parent, 2250, 1000, "h")

    # Storage (UD6)
    render_room(parent, 2500, 700, 400, 300, "UD6: Storage", palette)
    render_feature(parent, 2600, 850, "crate", "", palette)
    render_feature(parent, 2750, 850, "crate", "", palette)

    # Children's Cabin (UD7)
    render_room(parent, 2100, 1400, 300, 200, "UD7: Children's/Cabin", palette)
    render_door(parent, 2250, 1400, "h", "trapped")

    # Stairs down
    render_stairs(parent, 3200, 1250, "down", palette)


def layout_vessel_mid(parent, palette):
    """Map 3: Vessel Mid Deck — 4000x2500"""
    render_hull_outline(parent, 4000, 2500, palette)

    # Central corridor
    render_corridor(parent, 500, 1250, 3700, 1250, 100, palette)

    # Crew Quarters (MD1)
    render_room(parent, 500, 700, 500, 400, "MD1: Crew/Quarters", palette)
    render_door(parent, 750, 1100, "h")

    # Mess Hall (MD2)
    render_room(parent, 1100, 700, 400, 400, "MD2: Mess Hall", palette)
    render_door(parent, 1300, 1100, "h")
    render_feature(parent, 1200, 900, "table", "", palette)
    render_feature(parent, 1400, 900, "table", "", palette)

    # Chapel (MD3)
    render_room(parent, 1600, 700, 300, 400, "MD3: Chapel", palette)
    render_door(parent, 1750, 1100, "h")
    render_feature(parent, 1750, 800, "altar", "Altar", palette)

    # Cargo Bay (MD4) — large room
    render_room(parent, 2000, 600, 600, 500, "MD4: Cargo Bay", palette)
    render_door(parent, 2300, 1100, "h")
    render_feature(parent, 2100, 750, "crate", "", palette)
    render_feature(parent, 2200, 850, "crate", "", palette)
    render_feature(parent, 2400, 750, "crate", "", palette)

    # Preparation Chamber (MD5)
    render_room(parent, 1100, 1400, 300, 300, "MD5: Prep/Chamber", palette)
    render_door(parent, 1250, 1400, "h")

    # Navigator Cell (MD6)
    render_room(parent, 1500, 1400, 300, 300, "MD6: Navigator/Cell", palette)
    render_door(parent, 1650, 1400, "h", "locked")
    render_feature(parent, 1650, 1550, "warp", "", palette)

    # Power Junction (MD7)
    render_room(parent, 1900, 1400, 300, 300, "MD7: Power/Junction", palette)
    render_door(parent, 2050, 1400, "h")

    # Access Stairs (MD8)
    render_room(parent, 2800, 1050, 200, 200, "MD8: Stairs", palette)
    render_stairs(parent, 2900, 1150, "down", palette)
    render_stairs(parent, 2900, 1050, "up", palette)


def layout_vessel_lower(parent, palette):
    """Map 4: Vessel Lower Deck — 4000x2500 (organic/corrupt)"""
    render_hull_outline(parent, 4000, 2500, palette, organic=True)

    # Twisted central corridor
    corr_pts = []
    for px in range(500, 3700, 50):
        py = 1250 + 30 * math.sin(px / 200.0)
        corr_pts.append(f"{px},{py:.0f}")
    _se(
        parent, "polyline",
        points=" ".join(corr_pts),
        fill="none", stroke=palette["floor"], stroke_width="100",
        stroke_linecap="round",
    )

    # Enginarium (LD1)
    render_room(parent, 500, 750, 600, 500, "LD1: Enginarium", palette)
    render_door(parent, 800, 1250, "h")

    # Warp Drive (LD2) — BOSS ROOM
    render_room(parent, 1300, 700, 500, 500, "LD2: Warp Drive/BOSS ROOM", palette, highlight=True)
    render_door(parent, 1550, 1200, "h", "locked")
    render_feature(parent, 1550, 950, "warp", "Warp Core", palette)

    # Altar Chamber (LD3)
    render_room(parent, 2000, 750, 400, 400, "LD3: Altar/Chamber", palette)
    render_door(parent, 2200, 1150, "h", "trapped")
    render_feature(parent, 2200, 950, "altar", "Dark Altar", palette)

    # Cell Block (LD4)
    render_room(parent, 2600, 800, 400, 300, "LD4: Cell Block", palette)
    render_door(parent, 2800, 1100, "h")

    # Ritual Store (LD5)
    render_room(parent, 1200, 1400, 300, 300, "LD5: Ritual/Store", palette)
    render_door(parent, 1350, 1400, "h")
    render_feature(parent, 1350, 1550, "crate", "", palette)

    # Maintenance (LD6)
    render_room(parent, 1600, 1400, 300, 300, "LD6: Maintenance/Crawlway", palette)
    render_door(parent, 1750, 1400, "h")

    # Bilge (LD7) — long narrow at bottom
    render_room(parent, 600, 1900, 800, 200, "LD7: Bilge", palette)
    render_water(parent, 620, 1920, 760, 160, "0.2")


def layout_fortress_vallak(parent, palette):
    """Map 5: Fortress Vallak — 5000x4000"""
    # Town walls
    render_outer_wall(parent, 100, 100, 4800, 3800, palette)

    # Gate
    render_room(parent, 2400, 3700, 200, 200, "Gate", palette)

    # Roads — main crossroads
    render_road(parent, [(2500, 3700), (2500, 200)], palette, 80)
    render_road(parent, [(200, 2000), (4800, 2000)], palette, 80)

    # Blue Water Inn — center
    render_room(parent, 2000, 1500, 600, 500, "Blue Water Inn", palette, highlight=True)
    render_door(parent, 2300, 2000, "h")
    render_feature(parent, 2100, 1700, "table", "", palette)
    render_feature(parent, 2400, 1700, "table", "", palette)

    # Wachter Estate — northeast
    render_room(parent, 3500, 500, 500, 500, "Wachter Estate", palette)
    render_door(parent, 3750, 1000, "h")

    # St. Andral Chapel — northwest
    render_room(parent, 500, 500, 400, 400, "St. Andral/Chapel", palette)
    render_feature(parent, 700, 700, "altar", "Altar", palette)
    render_door(parent, 700, 900, "h")

    # Market Square — south-center
    render_room(parent, 2200, 2400, 600, 600, "Market Square", palette)
    render_feature(parent, 2400, 2600, "crate", "", palette)
    render_feature(parent, 2600, 2700, "crate", "", palette)

    # Barracks — east
    render_room(parent, 3800, 1500, 500, 400, "Barracks", palette)
    render_door(parent, 3800, 1700, "v")

    # Burgomaster's Hall — north-center
    render_room(parent, 2000, 300, 600, 400, "Burgomaster's Hall", palette, highlight=True)
    render_door(parent, 2300, 700, "h")

    # Misc buildings
    render_room(parent, 500, 1200, 400, 300, "Provisioner", palette)
    render_room(parent, 500, 2400, 400, 300, "Coffin-Maker", palette)
    render_room(parent, 3800, 2400, 400, 300, "Stockade", palette)

    # Well
    render_feature(parent, 2500, 2000, "well", "Town Well", palette)


def layout_krezk_ground(parent, palette):
    """Map 6: Krezk Ground Floor — 3000x2500"""
    # Reception
    render_room(parent, 300, 1000, 400, 300, "Reception", palette)
    render_door(parent, 700, 1150, "v")

    # Corridors
    render_corridor(parent, 700, 1150, 2700, 1150, 80, palette)
    render_corridor(parent, 1200, 600, 1200, 1700, 80, palette)

    # Operating Theater 1
    render_room(parent, 800, 400, 400, 400, "Operating/Theater 1", palette)
    render_door(parent, 1000, 800, "h")
    render_feature(parent, 1000, 600, "table", "Slab", palette)

    # Operating Theater 2
    render_room(parent, 1400, 400, 400, 400, "Operating/Theater 2", palette)
    render_door(parent, 1600, 800, "h")
    render_feature(parent, 1600, 600, "table", "Slab", palette)

    # Vat Chamber
    render_room(parent, 1900, 600, 500, 400, "Vat Chamber", palette)
    render_door(parent, 1900, 800, "v")
    render_feature(parent, 2050, 750, "fountain", "Vat", palette)
    render_feature(parent, 2250, 750, "fountain", "Vat", palette)

    # Mongrelfolk Ward
    render_room(parent, 800, 1400, 400, 300, "Mongrelfolk/Ward", palette)
    render_door(parent, 1000, 1400, "h", "locked")

    # Storage
    render_room(parent, 1400, 1400, 300, 200, "Storage", palette)
    render_feature(parent, 1550, 1500, "crate", "", palette)

    render_stairs(parent, 2500, 1150, "up", palette)


def layout_krezk_upper(parent, palette):
    """Map 7: Krezk Upper Floor — 3000x2500"""
    # Corridor
    render_corridor(parent, 400, 1200, 2600, 1200, 80, palette)

    # Abaron's Lab — large
    render_room(parent, 400, 400, 500, 500, "Abaron's Lab", palette, highlight=True)
    render_door(parent, 650, 900, "h")
    render_feature(parent, 550, 600, "table", "", palette)
    render_feature(parent, 750, 600, "table", "", palette)
    render_feature(parent, 650, 550, "warp", "", palette)

    # The Bride Chamber
    render_room(parent, 1100, 400, 400, 400, "The Bride/Chamber", palette, highlight=True)
    render_door(parent, 1300, 800, "h", "locked")
    render_feature(parent, 1300, 600, "altar", "Construct", palette)

    # Sacred Pool Courtyard — with circle
    render_room(parent, 1700, 300, 600, 500, "Sacred Pool/Courtyard", palette)
    render_circle_area(parent, 2000, 550, 120, palette, "Pool")

    # Record Room
    render_room(parent, 400, 1400, 300, 300, "Record Room", palette)
    render_door(parent, 550, 1400, "h")
    render_feature(parent, 550, 1550, "crate", "", palette)

    # Observation Gallery
    render_room(parent, 1100, 1400, 300, 200, "Observation/Gallery", palette)
    render_door(parent, 1250, 1400, "h")

    render_stairs(parent, 2500, 1200, "down", palette)


def layout_astartes_outpost(parent, palette):
    """Map 8: Fallen Outpost — 3500x3000"""
    # Ruined outer walls — with gaps
    render_outer_wall(parent, 200, 200, 3100, 2600, palette, gaps={0, 2})

    # Courtyard — central
    render_room(parent, 1000, 800, 800, 600, "Courtyard", palette)

    # Barracks — left
    render_room(parent, 300, 800, 500, 400, "Barracks", palette)
    render_door(parent, 800, 1000, "v")

    # Armory/Relic Vault — right
    render_room(parent, 2000, 800, 400, 400, "Armory / Relic/Vault", palette)
    render_door(parent, 2000, 1000, "v", "locked")
    render_feature(parent, 2200, 1000, "crystal", "Dawn's Edge?", palette)

    # Chapel — top center
    render_room(parent, 1200, 300, 500, 400, "Chapel of the/Silver Drakes", palette)
    render_door(parent, 1450, 700, "h")
    render_feature(parent, 1450, 500, "altar", "Altar", palette)

    # Strategium — bottom center
    render_room(parent, 1200, 1600, 400, 300, "Strategium", palette)
    render_door(parent, 1400, 1600, "h")
    render_feature(parent, 1400, 1750, "table", "Holo-Table", palette)

    # Beacon Tower — top right (circle)
    render_circle_area(parent, 2800, 500, 150, palette, "Beacon Tower")

    # Guard towers at corners
    for tx, ty in [(300, 300), (3100, 300), (300, 2600), (3100, 2600)]:
        render_room(parent, tx, ty, 200, 200, "Tower", palette)


def layout_warp_nexus(parent, palette):
    """Map 9: Warp Nexus — 3000x3000"""
    cx, cy = 1500, 1500

    # Circular hilltop
    render_circle_area(parent, cx, cy, 1200, palette)

    # Ritual ring
    _se(parent, "circle", cx=str(cx), cy=str(cy), r="600",
        fill="none", stroke=palette["accent"], stroke_width="3",
        stroke_dasharray="15,8", opacity="0.5")

    # 12 standing stones
    for i in range(12):
        angle = math.pi * 2 * i / 12 - math.pi / 2
        sx = cx + 1000 * math.cos(angle)
        sy = cy + 1000 * math.sin(angle)
        render_feature(parent, int(sx), int(sy), "stone", f"Stone {i + 1}", palette)

    # Warp-Tree — central large circle
    render_circle_area(parent, cx, cy, 200, palette, "Warp-Tree")
    # Inner corruption effect
    for i in range(8):
        angle = math.pi * 2 * i / 8
        ex = cx + 180 * math.cos(angle)
        ey = cy + 180 * math.sin(angle)
        _se(parent, "line", x1=str(cx), y1=str(cy), x2=str(int(ex)), y2=str(int(ey)),
            stroke=palette["accent"], stroke_width="2", opacity="0.4")

    # Path up from bottom
    render_road(parent, [(1500, 2900), (1500, 2700), (1400, 2500), (1500, 2300)], palette, 60)

    # Warp features
    render_feature(parent, cx, cy, "warp", "", palette)


def layout_munitorum_transport(parent, palette):
    """Map 10: Crashed Transport — 2500x1500"""
    # Hillside terrain (diagonal line)
    _se(parent, "line", x1="100", y1="1400", x2="2400", y2="800",
        stroke=palette["wall"], stroke_width="4", stroke_dasharray="20,10",
        opacity="0.3")
    _se(parent, "text", x="200", y="1350", fill=palette["text"],
        font_size="12", font_family="monospace", opacity="0.4").text = "Hillside slope"

    # Vehicle outline — tilted slightly via transform
    g = _se(parent, "g", transform="rotate(-8, 1250, 650)")

    # Cab
    render_room(g, 300, 400, 400, 400, "Cab", palette)
    render_door(g, 300, 600, "v")

    # Cargo Bay — main body
    render_room(g, 700, 350, 800, 500, "Cargo Bay", palette, highlight=True)
    render_door(g, 700, 600, "v")
    render_feature(g, 900, 500, "crate", "", palette)
    render_feature(g, 1000, 600, "crate", "", palette)
    render_feature(g, 1100, 500, "crate", "", palette)
    render_feature(g, 1200, 600, "crate", "", palette)
    render_feature(g, 1300, 500, "crate", "", palette)

    # Rear Section
    render_room(g, 1500, 400, 400, 400, "Rear Section", palette)
    render_door(g, 1500, 600, "v")

    # Scattered crates outside the vehicle
    for cx, cy in [(400, 1000), (600, 1050), (1600, 950), (1800, 1100), (2000, 1000)]:
        render_feature(parent, cx, cy, "crate", "", palette)

    _se(parent, "text", x="1800", y="1050", fill=palette["text"],
        font_size="11", font_family="monospace", opacity="0.5").text = "Scattered debris"


def layout_recaf_distillery(parent, palette):
    """Map 11: Recaf Distillery — 2500x2000"""
    # Main Building
    render_room(parent, 800, 300, 800, 600, "Main Building", palette)
    render_door(parent, 1200, 900, "h")

    # Fermentation Hall
    render_room(parent, 200, 300, 500, 500, "Fermentation/Hall", palette)
    render_door(parent, 700, 550, "v")
    render_feature(parent, 350, 500, "fountain", "Vat", palette)
    render_feature(parent, 550, 500, "fountain", "Vat", palette)

    # Storage Cellars
    render_room(parent, 1700, 400, 400, 300, "Storage/Cellars", palette)
    render_door(parent, 1700, 550, "v")
    render_feature(parent, 1800, 550, "crate", "", palette)
    render_feature(parent, 2000, 550, "crate", "", palette)

    # Loading Dock
    render_room(parent, 1700, 800, 300, 200, "Loading Dock", palette)
    render_door(parent, 1700, 900, "v")

    # Courtyard
    render_room(parent, 800, 1000, 500, 400, "Courtyard", palette)

    # Vineyard rows
    render_vineyard_rows(parent, 200, 1500, 2000, 400, palette, 8)
    _se(parent, "text", x="1200", y="1650", fill=palette["text"],
        font_size="12", font_family="monospace", opacity="0.4").text = "Recaf Groves"


def layout_berez(parent, palette):
    """Map 12: Drowned Ruins — 4000x3500"""
    # Water covering most of map
    render_water(parent, 0, 500, 4000, 3000)

    # Raised paths through water
    render_road(parent, [(200, 3200), (800, 2500), (1500, 2200), (2500, 2000), (3500, 1500)],
                palette, 60)
    render_road(parent, [(1500, 2200), (1500, 1000)], palette, 50)

    # Ruined buildings (partial rect outlines — only 2-3 sides)
    for rx, ry, rw, rh in [(400, 800, 300, 250), (900, 600, 250, 200),
                            (2500, 900, 300, 200), (3000, 700, 200, 250)]:
        # Draw only 2 sides to show ruins
        _se(parent, "line", x1=str(rx), y1=str(ry), x2=str(rx + rw), y2=str(ry),
            stroke=palette["wall"], stroke_width="3", opacity="0.6")
        _se(parent, "line", x1=str(rx), y1=str(ry), x2=str(rx), y2=str(ry + rh),
            stroke=palette["wall"], stroke_width="3", opacity="0.6")
        _se(parent, "text", x=str(rx + rw // 2), y=str(ry + rh // 2),
            fill=palette["text"], font_size="11", text_anchor="middle",
            font_family="monospace", opacity="0.5").text = "Ruin"

    # Lysaga's Hut — walking hab-unit (circle base + room)
    render_circle_area(parent, 2000, 1800, 200, palette)
    render_room(parent, 1800, 1600, 400, 400, "Lysaga's Hut/Walking Hab-Unit", palette, highlight=True)

    # Marina's Monument
    render_feature(parent, 1500, 1000, "monument", "Marina's/Monument", palette)

    # Dock ruins
    _se(parent, "rect", x="300", y="2800", width="200", height="80",
        fill=palette["floor"], stroke=palette["wall"], stroke_width="2", opacity="0.5")
    _se(parent, "text", x="400", y="2860", fill=palette["text"],
        font_size="10", text_anchor="middle", font_family="monospace",
        opacity="0.4").text = "Dock Ruins"


def layout_vault_level1(parent, palette):
    """Map 13: Empyrean Vault L1 — 4500x3500 (hexagonal rooms)"""
    # Grand Entry
    render_hex_room(parent, 700, 1750, 300, "Grand Entry", palette)

    # Antechamber
    render_hex_room(parent, 1400, 1750, 200, "Antechamber", palette)
    render_hex_corridor(parent, 1000, 1750, 1200, 1750, 60, palette)

    # Guardian Chamber
    render_hex_room(parent, 2200, 1750, 250, "Guardian/Chamber", palette)
    render_hex_corridor(parent, 1600, 1750, 1950, 1750, 60, palette)
    render_feature(parent, 2200, 1750, "warp", "", palette)

    # Corridor of Trials — chain of small hexes
    trial_xs = [2800, 3200, 3600]
    for i, tx in enumerate(trial_xs):
        render_hex_room(parent, tx, 1750, 150, f"Trial {i + 1}", palette)
        if i > 0:
            render_hex_corridor(parent, trial_xs[i - 1], 1750, tx, 1750, 50, palette)
    render_hex_corridor(parent, 2450, 1750, 2650, 1750, 50, palette)

    # Archive — upper
    render_hex_room(parent, 2200, 900, 200, "Archive", palette)
    render_hex_corridor(parent, 2200, 1500, 2200, 1100, 50, palette)
    render_sigil_circle(parent, 2200, 900, 100, palette)

    # Stairway Down — lower right
    render_hex_room(parent, 4000, 1750, 150, "Stairway Down", palette)
    render_hex_corridor(parent, 3750, 1750, 3850, 1750, 50, palette)
    render_stairs(parent, 4000, 1750, "down", palette)

    # Sigil circles in entry areas
    render_sigil_circle(parent, 700, 1750, 150, palette)
    render_sigil_circle(parent, 1400, 1750, 100, palette)

    # Additional Archive branch
    render_hex_room(parent, 1400, 900, 180, "Xenos Records", palette)
    render_hex_corridor(parent, 1400, 1550, 1400, 1080, 50, palette)
    render_sigil_circle(parent, 1400, 900, 90, palette)


def layout_vault_level2(parent, palette):
    """Map 14: Empyrean Vault L2 — 4500x3500 (hexagonal rooms)"""
    cx, cy = 2250, 1750

    # Central Nexus
    render_hex_room(parent, cx, cy, 300, "Central Nexus", palette, highlight=True)
    render_sigil_circle(parent, cx, cy, 200, palette)

    # 5 Containment Cells around nexus
    cell_names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    for i, name in enumerate(cell_names):
        angle = math.pi * 2 * i / 5 - math.pi / 2
        ccx = cx + 900 * math.cos(angle)
        ccy = cy + 900 * math.sin(angle)
        is_prime = (name == "Alpha")
        render_hex_room(parent, int(ccx), int(ccy), 150,
                        f"Cell {name}" + ("/Strahd's Pact" if is_prime else ""),
                        palette, highlight=is_prime)
        render_hex_corridor(parent, cx, cy, int(ccx), int(ccy), 50, palette)
        render_sigil_circle(parent, int(ccx), int(ccy), 80, palette)

    # Alpha-Prime — highlight extra
    alpha_x = cx + int(900 * math.cos(-math.pi / 2))
    alpha_y = cy + int(900 * math.sin(-math.pi / 2))
    render_feature(parent, alpha_x, alpha_y, "warp", "", palette)

    # Archive Annex — far right
    render_hex_room(parent, 3800, cy, 200, "Archive Annex", palette)
    render_hex_corridor(parent, cx + 300, cy, 3600, cy, 50, palette)

    # Exit Shaft — bottom
    render_hex_room(parent, cx, 3200, 150, "Exit Shaft", palette)
    render_hex_corridor(parent, cx, cy + 300, cx, 3050, 50, palette)
    render_stairs(parent, cx, 3200, "up", palette)


def layout_spire_courtyard(parent, palette):
    """Map 15: Spire Courtyard — 3000x2500"""
    # Outer wall
    render_outer_wall(parent, 100, 100, 2800, 2300, palette)

    # Inner courtyard
    render_room(parent, 500, 500, 2000, 1600, "Inner Courtyard", palette)

    # Gatehouse
    render_room(parent, 1300, 2200, 400, 200, "Gatehouse", palette)
    render_door(parent, 1500, 2200, "h")

    # Drawbridge gap
    _se(parent, "rect", x="1350", y="2050", width="300", height="150",
        fill="#0a0505", stroke=palette["accent"], stroke_width="2",
        stroke_dasharray="10,5")
    _se(parent, "text", x="1500", y="2130", fill=palette["text"],
        font_size="11", text_anchor="middle", font_family="monospace",
        opacity="0.5").text = "Drawbridge"

    # Guard towers at corners
    for tx, ty, lbl in [(200, 200, "NW Tower"), (2700, 200, "NE Tower"),
                         (200, 2100, "SW Tower"), (2700, 2100, "SE Tower")]:
        render_room(parent, tx, ty, 200, 200, lbl, palette)

    # Stables
    render_room(parent, 600, 1800, 300, 200, "Stables", palette)

    # Well
    render_feature(parent, 1500, 1200, "well", "Well", palette)

    # Approach road
    render_road(parent, [(1500, 2500), (1500, 2400)], palette, 80)


def layout_spire_ground(parent, palette):
    """Map 16: Spire Ground Level — 4000x3500"""
    # Grand Hall — central
    render_room(parent, 1500, 400, 800, 600, "Grand Hall", palette, highlight=True)
    render_door(parent, 1900, 1000, "h")

    # Entrance Vestibule
    render_room(parent, 1700, 1100, 400, 300, "Entrance/Vestibule", palette)
    render_door(parent, 1900, 1400, "h")

    # Dining Hall — left of grand hall
    render_room(parent, 600, 400, 600, 500, "Dining Hall", palette)
    render_door(parent, 1200, 650, "v")
    render_feature(parent, 800, 600, "table", "", palette)
    render_feature(parent, 1000, 600, "table", "", palette)

    # Chapel of Bones
    render_room(parent, 2600, 400, 500, 500, "Chapel of Bones", palette)
    render_door(parent, 2600, 650, "v")
    render_feature(parent, 2850, 650, "altar", "Bone Altar", palette)

    # Kitchen
    render_room(parent, 600, 1200, 400, 300, "Kitchen", palette)
    render_door(parent, 1000, 1350, "v")
    render_feature(parent, 800, 1350, "table", "", palette)

    # Servant Quarters
    render_room(parent, 600, 1700, 400, 300, "Servant/Quarters", palette)
    render_door(parent, 1000, 1850, "v")

    # Gallery — long horizontal
    render_room(parent, 1200, 1500, 800, 200, "Gallery", palette)

    # Armory
    render_room(parent, 2600, 1200, 300, 300, "Armory", palette)
    render_door(parent, 2600, 1350, "v", "locked")
    render_feature(parent, 2750, 1350, "crate", "", palette)

    # Corridors
    render_corridor(parent, 1000, 650, 1500, 650, 80, palette)
    render_corridor(parent, 2300, 650, 2600, 650, 80, palette)
    render_corridor(parent, 1000, 1350, 1200, 1350, 80, palette)
    render_corridor(parent, 2000, 1600, 2600, 1600, 80, palette)

    # Stairs
    render_stairs(parent, 3200, 1000, "up", palette)
    render_stairs(parent, 3200, 1200, "down", palette)


def layout_spire_upper(parent, palette):
    """Map 17: Spire Upper Levels — 4000x3500"""
    # Strahd's Study
    render_room(parent, 1600, 300, 500, 500, "Strahd's Study", palette, highlight=True)
    render_door(parent, 1850, 800, "h")
    render_feature(parent, 1750, 500, "table", "Desk", palette)

    # Throne Room
    render_room(parent, 700, 300, 600, 500, "Throne Room", palette, highlight=True)
    render_door(parent, 1000, 800, "h")
    render_feature(parent, 1000, 550, "altar", "Throne", palette)

    # Library
    render_room(parent, 2400, 400, 500, 400, "Library", palette)
    render_door(parent, 2400, 600, "v")
    render_feature(parent, 2550, 550, "crate", "", palette)
    render_feature(parent, 2750, 550, "crate", "", palette)

    # Guest Chambers
    render_room(parent, 700, 1100, 400, 300, "Guest Chambers", palette)
    render_door(parent, 900, 1100, "h")

    # Observatory — with circle
    render_room(parent, 2400, 1100, 400, 400, "Observatory", palette)
    render_circle_area(parent, 2600, 1300, 120, palette, "Lens")
    render_door(parent, 2400, 1300, "v")

    # Heart Chamber Access
    render_room(parent, 1600, 1100, 300, 300, "Heart Chamber/Access", palette, highlight=True)
    render_door(parent, 1750, 1100, "h", "locked")

    # Balcony — long horizontal
    render_room(parent, 700, 1600, 600, 200, "Balcony", palette)

    # Corridors
    render_corridor(parent, 1000, 850, 1600, 850, 80, palette)
    render_corridor(parent, 2100, 600, 2400, 600, 80, palette)
    render_corridor(parent, 1100, 1250, 1600, 1250, 80, palette)
    render_corridor(parent, 1900, 1250, 2400, 1250, 80, palette)

    # Stairs
    render_stairs(parent, 3200, 850, "down", palette)
    render_stairs(parent, 3200, 1100, "up", palette)


def layout_spire_crypts(parent, palette):
    """Map 18: Spire Crypts — 4000x4000"""
    # Central corridor — vertical
    render_corridor(parent, 2000, 200, 2000, 3800, 100, palette)

    # Side branches
    render_corridor(parent, 800, 1000, 3200, 1000, 100, palette)
    render_corridor(parent, 800, 2500, 3200, 2500, 100, palette)

    # 12 crypt cells along corridors
    crypt_positions = [
        # Along central corridor
        (1700, 400, "Crypt 1"), (2200, 400, "Crypt 2"),
        (1700, 700, "Crypt 3"), (2200, 700, "Crypt 4"),
        # Along upper branch
        (900, 700, "Crypt 5"), (900, 1100, "Crypt 6"),
        (2900, 700, "Crypt 7"), (2900, 1100, "Crypt 8"),
        # Along lower branch
        (900, 2200, "Crypt 9"), (900, 2600, "Crypt 10"),
        (2900, 2200, "Crypt 11"), (2900, 2600, "Crypt 12"),
    ]
    for cx, cy, lbl in crypt_positions:
        render_room(parent, cx, cy, 200, 200, lbl, palette)

    # Strahd's Coffin Chamber — highlighted
    render_room(parent, 1800, 3000, 400, 400, "Strahd's Coffin/Chamber", palette, highlight=True)
    render_door(parent, 2000, 3000, "h", "trapped")
    render_feature(parent, 2000, 3200, "altar", "Coffin", palette)

    # Sergei's Tomb
    render_room(parent, 1850, 1500, 300, 300, "Sergei's Tomb", palette)
    render_door(parent, 2000, 1500, "h")
    render_feature(parent, 2000, 1650, "altar", "Sarcophagus", palette)

    # Teleportation Braziers
    for bx, by in [(800, 500), (3200, 500), (2000, 2200)]:
        render_feature(parent, bx, by, "brazier", "Brazier", palette)


def layout_spire_heart(parent, palette):
    """Map 19: Heart Chamber — 2000x2000"""
    cx, cy = 1000, 1000

    # Walkway ring (outer)
    _se(parent, "circle", cx=str(cx), cy=str(cy), r="850",
        fill="none", stroke=palette["floor"], stroke_width="80")
    _se(parent, "circle", cx=str(cx), cy=str(cy), r="850",
        fill="none", stroke=palette["wall"], stroke_width="3")

    # Circular arena
    render_circle_area(parent, cx, cy, 700, palette, "")

    # 4 pillars at cardinal points
    for angle_deg in [0, 90, 180, 270]:
        angle = math.radians(angle_deg)
        px = cx + int(500 * math.cos(angle))
        py = cy + int(500 * math.sin(angle))
        render_feature(parent, px, py, "pillar", "Pillar", palette)

    # Warp energy lines radiating from center
    g = _se(parent, "g", opacity="0.3", stroke=palette["accent"], stroke_width="2")
    for i in range(12):
        angle = math.pi * 2 * i / 12
        ex = cx + int(650 * math.cos(angle))
        ey = cy + int(650 * math.sin(angle))
        _se(g, "line", x1=str(cx), y1=str(cy), x2=str(ex), y2=str(ey))

    # Central crystal (diamond)
    render_feature(parent, cx, cy, "crystal", "Heart of/the Spire", palette)

    # Entrance from south
    render_corridor(parent, cx, cy + 700, cx, cy + 900, 80, palette)
    render_door(parent, cx, cy + 700, "h", "locked")
    _se(parent, "text", x=str(cx), y=str(cy + 950),
        fill=palette["text"], font_size="12", text_anchor="middle",
        font_family="monospace", opacity="0.5").text = "Entrance"


# ---------------------------------------------------------------------------
# Main — Generate all 19 maps
# ---------------------------------------------------------------------------

def write_svg(root, filepath):
    """Write an SVG element tree to a file."""
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    with open(filepath, "wb") as f:
        tree.write(f, xml_declaration=True, encoding="utf-8")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    module_dir = os.path.dirname(script_dir)
    output_dir = os.path.join(module_dir, "assets", "maps")
    os.makedirs(output_dir, exist_ok=True)

    maps = [
        ("village-of-barovus.svg",   "Village of Barovus",    4000, 3000, "gothic_imperial",  layout_village_barovus),
        ("vessel-upper.svg",         "Vessel Upper Deck",     4000, 2500, "imperial_metal",   layout_vessel_upper),
        ("vessel-mid.svg",           "Vessel Mid Deck",       4000, 2500, "imperial_metal",   layout_vessel_mid),
        ("vessel-lower.svg",         "Vessel Lower Deck",     4000, 2500, "organic_corrupt",  layout_vessel_lower),
        ("fortress-vallak.svg",      "Fortress Vallak",       5000, 4000, "gothic_imperial",  layout_fortress_vallak),
        ("krezk-ground.svg",         "Krezk Ground Floor",    3000, 2500, "clinical_horror",  layout_krezk_ground),
        ("krezk-upper.svg",          "Krezk Upper Floor",     3000, 2500, "clinical_horror",  layout_krezk_upper),
        ("astartes-outpost.svg",     "Fallen Outpost",        3500, 3000, "gothic_imperial",  layout_astartes_outpost),
        ("warp-nexus.svg",           "Warp Nexus",            3000, 3000, "organic_corrupt",  layout_warp_nexus),
        ("munitorum-transport.svg",  "Crashed Transport",     2500, 1500, "imperial_metal",   layout_munitorum_transport),
        ("recaf-distillery.svg",     "Recaf Distillery",      2500, 2000, "gothic_imperial",  layout_recaf_distillery),
        ("berez.svg",                "Drowned Ruins",         4000, 3500, "organic_corrupt",  layout_berez),
        ("vault-level1.svg",         "Empyrean Vault L1",     4500, 3500, "alien_vault",      layout_vault_level1),
        ("vault-level2.svg",         "Empyrean Vault L2",     4500, 3500, "alien_vault",      layout_vault_level2),
        ("spire-courtyard.svg",      "Spire Courtyard",       3000, 2500, "castle_gothic",    layout_spire_courtyard),
        ("spire-ground.svg",         "Spire Ground Level",    4000, 3500, "castle_gothic",    layout_spire_ground),
        ("spire-upper.svg",          "Spire Upper Levels",    4000, 3500, "castle_gothic",    layout_spire_upper),
        ("spire-crypts.svg",         "Spire Crypts",          4000, 4000, "castle_gothic",    layout_spire_crypts),
        ("spire-heart.svg",          "Heart Chamber",         2000, 2000, "castle_gothic",    layout_spire_heart),
    ]

    for filename, scene_name, w, h, palette_name, layout_fn in maps:
        svg = create_svg(w, h)
        palette = PALETTES[palette_name]
        render_background(svg, w, h, palette)
        render_grid(svg, w, h)
        layout_fn(svg, palette)
        render_title(svg, w, h, scene_name)
        write_svg(svg, os.path.join(output_dir, filename))

    print(f"Generated {len(maps)} maps in {output_dir}")

    # Print file sizes
    print("\nFile sizes:")
    total = 0
    for filename, *_ in maps:
        fpath = os.path.join(output_dir, filename)
        size = os.path.getsize(fpath)
        total += size
        print(f"  {filename:35s} {size:>8,d} bytes")
    print(f"  {'TOTAL':35s} {total:>8,d} bytes")


if __name__ == "__main__":
    main()
