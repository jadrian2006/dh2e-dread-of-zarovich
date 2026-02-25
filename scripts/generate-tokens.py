#!/usr/bin/env python3
"""Generate SVG token icons for the Dread of Zarovich Foundry VTT module.

Uses only Python stdlib (xml.etree.ElementTree). Produces 280x280 circle-framed
portrait icons with a dark background, colored ring, central glyph, and name label.

Output: ../assets/tokens/*.svg (17 files)
"""

import os
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "tokens")

BG_FILL = "#1a1a2e"
SYMBOL_FILL = "#e0e0e0"
RING_RADIUS = 120
RING_STROKE = 8
CX, CY = 140, 130
LABEL_Y = 265
VIEWBOX = "0 0 280 280"
NS = "http://www.w3.org/2000/svg"

# ---------------------------------------------------------------------------
# Token definitions
# ---------------------------------------------------------------------------

# Each entry: (filename, label, ring_color, symbol_type, symbol_data)
#
# symbol_type is one of:
#   "text"   - symbol_data is the text string (rendered via <text>)
#   "paths"  - symbol_data is a list of dicts with SVG element specs
#              Each dict: {"tag": "path"/"circle"/"line"/..., "attribs": {...}}

TOKENS = [
    # ── NPC Tokens ──────────────────────────────────────────────────────
    {
        "file": "strahd.svg",
        "label": "STRAHD",
        "ring": "#8b1a1a",
        "symbol": "paths",
        "data": [
            # Ornate "S" monogram - main S path
            {"tag": "text", "attribs": {
                "x": str(CX), "y": str(CY + 28),
                "text-anchor": "middle",
                "font-family": "serif",
                "font-size": "100",
                "font-weight": "bold",
                "font-style": "italic",
                "fill": SYMBOL_FILL,
            }, "text": "S"},
            # Decorative serifs / flourishes
            {"tag": "line", "attribs": {
                "x1": str(CX - 35), "y1": str(CY - 42),
                "x2": str(CX + 35), "y2": str(CY - 42),
                "stroke": "#8b1a1a", "stroke-width": "3",
            }},
            {"tag": "line", "attribs": {
                "x1": str(CX - 35), "y1": str(CY + 38),
                "x2": str(CX + 35), "y2": str(CY + 38),
                "stroke": "#8b1a1a", "stroke-width": "3",
            }},
        ],
    },
    {
        "file": "van-richten.svg",
        "label": "VAN RICHTEN",
        "ring": "#d4a846",
        "symbol": "paths",
        "data": [
            # Inquisition "I" letter
            {"tag": "text", "attribs": {
                "x": str(CX), "y": str(CY + 20),
                "text-anchor": "middle",
                "font-family": "serif",
                "font-size": "80",
                "font-weight": "bold",
                "fill": SYMBOL_FILL,
            }, "text": "I"},
            # Rosette circle around the I
            {"tag": "circle", "attribs": {
                "cx": str(CX), "cy": str(CY),
                "r": "52",
                "fill": "none",
                "stroke": "#d4a846",
                "stroke-width": "3",
            }},
            # Small dots on rosette (N, S, E, W)
            {"tag": "circle", "attribs": {"cx": str(CX), "cy": str(CY - 52), "r": "4", "fill": "#d4a846"}},
            {"tag": "circle", "attribs": {"cx": str(CX), "cy": str(CY + 52), "r": "4", "fill": "#d4a846"}},
            {"tag": "circle", "attribs": {"cx": str(CX - 52), "cy": str(CY), "r": "4", "fill": "#d4a846"}},
            {"tag": "circle", "attribs": {"cx": str(CX + 52), "cy": str(CY), "r": "4", "fill": "#d4a846"}},
        ],
    },
    {
        "file": "ireena.svg",
        "label": "IREENA",
        "ring": "#6688cc",
        "symbol": "paths",
        "data": [
            # Psi symbol
            {"tag": "text", "attribs": {
                "x": str(CX), "y": str(CY + 28),
                "text-anchor": "middle",
                "font-family": "serif",
                "font-size": "100",
                "fill": "#aabbee",
            }, "text": "\u03a8"},
        ],
    },
    {
        "file": "ismark.svg",
        "label": "ISMARK",
        "ring": "#7788aa",
        "symbol": "paths",
        "data": [
            # Crossed swords - two diagonal lines
            {"tag": "line", "attribs": {
                "x1": str(CX - 40), "y1": str(CY - 40),
                "x2": str(CX + 40), "y2": str(CY + 40),
                "stroke": SYMBOL_FILL, "stroke-width": "6", "stroke-linecap": "round",
            }},
            {"tag": "line", "attribs": {
                "x1": str(CX + 40), "y1": str(CY - 40),
                "x2": str(CX - 40), "y2": str(CY + 40),
                "stroke": SYMBOL_FILL, "stroke-width": "6", "stroke-linecap": "round",
            }},
            # Hilts (cross-guards) - short perpendicular lines at the midpoints
            {"tag": "line", "attribs": {
                "x1": str(CX - 10), "y1": str(CY + 18),
                "x2": str(CX + 10), "y2": str(CY + 18),
                "stroke": "#7788aa", "stroke-width": "4", "stroke-linecap": "round",
            }},
            {"tag": "line", "attribs": {
                "x1": str(CX - 10), "y1": str(CY + 18),
                "x2": str(CX + 10), "y2": str(CY + 18),
                "stroke": "#7788aa", "stroke-width": "4", "stroke-linecap": "round",
            }},
        ],
    },
    {
        "file": "abaron.svg",
        "label": "ABARON",
        "ring": "#33cc66",
        "symbol": "paths",
        "data": _cog_symbol(CX, CY, 42, 8, "#33cc66", SYMBOL_FILL)
        if False else [],  # placeholder - will be built below
    },
    {
        "file": "madam-eva.svg",
        "label": "MADAM EVA",
        "ring": "#8844aa",
        "symbol": "paths",
        "data": [],  # placeholder
    },

    # ── Enemy Tokens ────────────────────────────────────────────────────
    {
        "file": "plague-revenant.svg",
        "label": "REVENANT",
        "ring": "#446633",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "warp-thrall.svg",
        "label": "THRALL",
        "ring": "#442255",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "warp-mutant.svg",
        "label": "MUTANT",
        "ring": "#cc44aa",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "gargoyle-servitor.svg",
        "label": "GARGOYLE",
        "ring": "#667766",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "malfunctioning-servitor.svg",
        "label": "SERVITOR",
        "ring": "#885533",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "lesser-daemon.svg",
        "label": "DAEMON",
        "ring": "#ee3399",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "warp-hound.svg",
        "label": "HOUND",
        "ring": "#553366",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "mongrelfolk.svg",
        "label": "MONGREL",
        "ring": "#665544",
        "symbol": "paths",
        "data": [],
    },

    # ── Additional NPC / Boss Tokens ──────────────────────────────────
    {
        "file": "baba-lysaga.svg",
        "label": "BABA LYSAGA",
        "ring": "#44aa44",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "elite-guard.svg",
        "label": "ELITE GUARD",
        "ring": "#8b1a1a",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "servitor-guard.svg",
        "label": "SERVITOR-GUARD",
        "ring": "#556677",
        "symbol": "paths",
        "data": [],
    },

    # ── Weapon Icons ────────────────────────────────────────────────────
    {
        "file": "dawns-edge.svg",
        "label": "DAWN'S EDGE",
        "ring": "#d4a846",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "grief.svg",
        "label": "GRIEF",
        "ring": "#8b1a1a",
        "symbol": "paths",
        "data": [],
    },
    {
        "file": "inferno-pistol.svg",
        "label": "INFERNO",
        "ring": "#cc4400",
        "symbol": "paths",
        "data": [],
    },
]


# ---------------------------------------------------------------------------
# Symbol builder helpers (pure functions, no external deps)
# ---------------------------------------------------------------------------

import math


def _cog_teeth_path(cx, cy, outer_r, inner_r, teeth, tooth_width_deg=8):
    """Return an SVG path `d` string for a cog/gear outline."""
    points = []
    for i in range(teeth):
        angle_center = (360 / teeth) * i
        # tooth outer corners
        a1 = math.radians(angle_center - tooth_width_deg)
        a2 = math.radians(angle_center + tooth_width_deg)
        # gap (inner) midpoints
        a_gap_before = math.radians(angle_center - (360 / teeth) / 2)
        a_gap_after = math.radians(angle_center + (360 / teeth) / 2)

        # inner point before tooth
        points.append((cx + inner_r * math.cos(a_gap_before),
                        cy + inner_r * math.sin(a_gap_before)))
        # outer tooth
        points.append((cx + outer_r * math.cos(a1),
                        cy + outer_r * math.sin(a1)))
        points.append((cx + outer_r * math.cos(a2),
                        cy + outer_r * math.sin(a2)))

    d = "M {:.1f},{:.1f}".format(points[0][0], points[0][1])
    for p in points[1:]:
        d += " L {:.1f},{:.1f}".format(p[0], p[1])
    d += " Z"
    return d


def _star_path(cx, cy, outer_r, inner_r, points_count):
    """Return an SVG path `d` string for a star shape."""
    pts = []
    for i in range(points_count * 2):
        angle = math.radians(-90 + (360 / (points_count * 2)) * i)
        r = outer_r if i % 2 == 0 else inner_r
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    d = "M {:.1f},{:.1f}".format(pts[0][0], pts[0][1])
    for p in pts[1:]:
        d += " L {:.1f},{:.1f}".format(p[0], p[1])
    d += " Z"
    return d


def build_symbol_abaron():
    """Cog/gear with inner circle (Mechanicus style)."""
    elements = []
    # Cog outline
    cog_d = _cog_teeth_path(CX, CY, 48, 36, 10, tooth_width_deg=7)
    elements.append({"tag": "path", "attribs": {
        "d": cog_d,
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "3",
    }})
    # Inner circle
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY),
        "r": "22",
        "fill": "none",
        "stroke": "#33cc66",
        "stroke-width": "2.5",
    }})
    # Center dot
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY),
        "r": "5",
        "fill": "#33cc66",
    }})
    return elements


def build_symbol_madam_eva():
    """Eye symbol - almond eye shape with circle iris and dot pupil."""
    elements = []
    # Eye outline (almond shape using two arcs)
    left_x = CX - 45
    right_x = CX + 45
    elements.append({"tag": "path", "attribs": {
        "d": "M {lx},{cy} Q {cx},{ty} {rx},{cy} Q {cx},{by} {lx},{cy} Z".format(
            lx=left_x, rx=right_x, cx=CX,
            cy=CY, ty=CY - 30, by=CY + 30),
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "3",
    }})
    # Iris
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY),
        "r": "16",
        "fill": "none",
        "stroke": "#8844aa",
        "stroke-width": "3",
    }})
    # Pupil
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY),
        "r": "7",
        "fill": "#8844aa",
    }})
    return elements


def build_symbol_revenant():
    """Skull shape - circle head, eye sockets, jaw."""
    elements = []
    # Cranium
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY - 5),
        "r": "35",
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "3",
    }})
    # Left eye socket
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX - 13), "cy": str(CY - 12),
        "r": "8",
        "fill": "#446633",
    }})
    # Right eye socket
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX + 13), "cy": str(CY - 12),
        "r": "8",
        "fill": "#446633",
    }})
    # Nose (inverted triangle)
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} L {},{} L {},{} Z".format(
            CX, CY + 8, CX - 5, CY, CX + 5, CY),
        "fill": "#446633",
    }})
    # Jaw / teeth line
    elements.append({"tag": "line", "attribs": {
        "x1": str(CX - 18), "y1": str(CY + 20),
        "x2": str(CX + 18), "y2": str(CY + 20),
        "stroke": SYMBOL_FILL, "stroke-width": "2",
    }})
    # Teeth marks
    for dx in range(-15, 18, 6):
        elements.append({"tag": "line", "attribs": {
            "x1": str(CX + dx), "y1": str(CY + 17),
            "x2": str(CX + dx), "y2": str(CY + 23),
            "stroke": SYMBOL_FILL, "stroke-width": "1.5",
        }})
    return elements


def build_symbol_thrall():
    """Blank face - circle with dot eyes, no mouth."""
    elements = []
    # Face circle
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY),
        "r": "38",
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "2.5",
    }})
    # Left eye dot
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX - 14), "cy": str(CY - 6),
        "r": "5",
        "fill": "#442255",
    }})
    # Right eye dot
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX + 14), "cy": str(CY - 6),
        "r": "5",
        "fill": "#442255",
    }})
    return elements


def build_symbol_mutant():
    """8-pointed chaos star."""
    elements = []
    # 8-pointed star (two overlapping 4-pointed stars rotated 45 degrees)
    star1 = _star_path(CX, CY, 45, 16, 4)
    elements.append({"tag": "path", "attribs": {
        "d": star1, "fill": SYMBOL_FILL, "opacity": "0.9",
    }})
    # Rotated star (build manually - 4 narrow diamond arms at 45 degree offsets)
    pts2 = []
    for i in range(8):
        angle = math.radians(-90 + 45 + (360 / 8) * i)
        r = 45 if i % 2 == 0 else 16
        pts2.append((CX + r * math.cos(angle), CY + r * math.sin(angle)))
    d2 = "M {:.1f},{:.1f}".format(pts2[0][0], pts2[0][1])
    for p in pts2[1:]:
        d2 += " L {:.1f},{:.1f}".format(p[0], p[1])
    d2 += " Z"
    elements.append({"tag": "path", "attribs": {
        "d": d2, "fill": SYMBOL_FILL, "opacity": "0.9",
    }})
    # Center circle
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY),
        "r": "10",
        "fill": "#cc44aa",
    }})
    return elements


def build_symbol_gargoyle():
    """Wings - V-shape with feathered edges."""
    elements = []
    # Main V-shape wings
    elements.append({"tag": "path", "attribs": {
        "d": "M {cx},{bot} L {lx},{ty} L {lmx},{my} M {cx},{bot} L {rx},{ty} L {rmx},{my}".format(
            cx=CX, bot=CY + 25,
            lx=CX - 50, ty=CY - 35,
            lmx=CX - 30, my=CY - 10,
            rx=CX + 50,
            rmx=CX + 30),
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "4",
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
    }})
    # Secondary feather lines (left wing)
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} L {},{}".format(CX - 20, CY + 5, CX - 45, CY - 20),
        "stroke": SYMBOL_FILL, "stroke-width": "2.5", "fill": "none",
        "stroke-linecap": "round",
    }})
    # Secondary feather lines (right wing)
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} L {},{}".format(CX + 20, CY + 5, CX + 45, CY - 20),
        "stroke": SYMBOL_FILL, "stroke-width": "2.5", "fill": "none",
        "stroke-linecap": "round",
    }})
    return elements


def build_symbol_servitor():
    """Cracked cog - gear outline with a crack line through it."""
    elements = []
    cog_d = _cog_teeth_path(CX, CY, 45, 33, 8, tooth_width_deg=9)
    elements.append({"tag": "path", "attribs": {
        "d": cog_d,
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "3",
    }})
    # Inner circle
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY),
        "r": "18",
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "2",
    }})
    # Crack line (jagged)
    crack_x = [CX - 5, CX + 8, CX - 3, CX + 6, CX - 2]
    crack_y = [CY - 42, CY - 15, CY, CY + 18, CY + 42]
    crack_d = "M {},{} ".format(crack_x[0], crack_y[0])
    for i in range(1, len(crack_x)):
        crack_d += "L {},{} ".format(crack_x[i], crack_y[i])
    elements.append({"tag": "path", "attribs": {
        "d": crack_d,
        "fill": "none",
        "stroke": "#885533",
        "stroke-width": "3",
        "stroke-linecap": "round",
    }})
    return elements


def build_symbol_daemon():
    """Daemon face - circle with horns and glowing eyes."""
    elements = []
    # Head circle
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY + 5),
        "r": "30",
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "3",
    }})
    # Left horn
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} Q {},{} {},{}".format(
            CX - 22, CY - 20,
            CX - 40, CY - 50,
            CX - 15, CY - 48),
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "3.5",
        "stroke-linecap": "round",
    }})
    # Right horn
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} Q {},{} {},{}".format(
            CX + 22, CY - 20,
            CX + 40, CY - 50,
            CX + 15, CY - 48),
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "3.5",
        "stroke-linecap": "round",
    }})
    # Eyes (glowing)
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX - 12), "cy": str(CY),
        "r": "5",
        "fill": "#ee3399",
    }})
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX + 12), "cy": str(CY),
        "r": "5",
        "fill": "#ee3399",
    }})
    # Mouth slit
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} Q {},{} {},{}".format(
            CX - 12, CY + 18,
            CX, CY + 25,
            CX + 12, CY + 18),
        "fill": "none",
        "stroke": "#ee3399",
        "stroke-width": "2",
    }})
    return elements


def build_symbol_hound():
    """Wolf head silhouette - pointed ears, snout."""
    elements = []
    # Head outline path
    d = (
        "M {cx},{bot} "  # chin
        "L {le},{ey} "   # left jaw to ear base
        "L {let},{et} "  # left ear tip
        "L {lei},{ei} "  # left ear inner
        "L {cx},{top} "  # forehead center
        "L {rei},{ei2} " # right ear inner
        "L {ret},{et2} " # right ear tip
        "L {re},{ey2} "  # right jaw
        "Z"
    ).format(
        cx=CX, bot=CY + 40,
        le=CX - 35, ey=CY + 5,
        let=CX - 35, et=CY - 42,
        lei=CX - 18, ei=CY - 20,
        top=CX, ret=CX + 35,
        rei=CX + 18, ei2=CY - 20,
        et2=CY - 42,
        re=CX + 35, ey2=CY + 5,
    )
    elements.append({"tag": "path", "attribs": {
        "d": d,
        "fill": SYMBOL_FILL,
        "opacity": "0.85",
    }})
    # Eyes
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX - 12), "cy": str(CY - 2),
        "r": "4",
        "fill": "#553366",
    }})
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX + 12), "cy": str(CY - 2),
        "r": "4",
        "fill": "#553366",
    }})
    # Snout line
    elements.append({"tag": "line", "attribs": {
        "x1": str(CX), "y1": str(CY + 8),
        "x2": str(CX), "y2": str(CY + 22),
        "stroke": "#553366", "stroke-width": "2",
    }})
    return elements


def build_symbol_mongrel():
    """Hunched figure silhouette."""
    elements = []
    # Body path - hunched humanoid
    d = (
        "M {cx},{bot} "          # feet
        "L {lh},{hip} "          # left hip
        "L {ls},{sh} "           # left shoulder (hunched)
        "Q {hx},{hy} {nx},{ny} " # hunched back to neck
        "L {hd},{hdy} "          # head top
        "Q {hrx},{hry} {nx2},{ny2} " # head curve
        "L {rs},{sh2} "          # right shoulder
        "L {rh},{hip2} "         # right hip
        "Z"
    ).format(
        cx=CX, bot=CY + 42,
        lh=CX - 18, hip=CY + 30,
        ls=CX - 28, sh=CY - 5,
        hx=CX - 25, hy=CY - 30,
        nx=CX - 5, ny=CY - 30,
        hd=CX + 2, hdy=CY - 42,
        hrx=CX + 15, hry=CY - 42,
        nx2=CX + 12, ny2=CY - 25,
        rs=CX + 20, sh2=CY + 0,
        rh=CX + 15, hip2=CY + 30,
    )
    elements.append({"tag": "path", "attribs": {
        "d": d,
        "fill": SYMBOL_FILL,
        "opacity": "0.8",
    }})
    # Dot eye
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX + 5), "cy": str(CY - 32),
        "r": "3",
        "fill": "#665544",
    }})
    return elements


def build_symbol_dawns_edge():
    """Sword blade pointing up - golden power sword."""
    elements = []
    # Blade
    elements.append({"tag": "path", "attribs": {
        "d": "M {cx},{tip} L {lb},{gb} L {lb},{ge} L {rb},{ge} L {rb},{gb} Z".format(
            cx=CX, tip=CY - 52,
            lb=CX - 8, gb=CY - 44,
            ge=CY + 15,
            rb=CX + 8),
        "fill": SYMBOL_FILL,
        "opacity": "0.95",
    }})
    # Fuller (central groove)
    elements.append({"tag": "line", "attribs": {
        "x1": str(CX), "y1": str(CY - 40),
        "x2": str(CX), "y2": str(CY + 10),
        "stroke": "#d4a846", "stroke-width": "2",
    }})
    # Cross-guard
    elements.append({"tag": "line", "attribs": {
        "x1": str(CX - 25), "y1": str(CY + 15),
        "x2": str(CX + 25), "y2": str(CY + 15),
        "stroke": "#d4a846", "stroke-width": "5", "stroke-linecap": "round",
    }})
    # Grip
    elements.append({"tag": "rect", "attribs": {
        "x": str(CX - 4), "y": str(CY + 18),
        "width": "8", "height": "22",
        "fill": SYMBOL_FILL,
    }})
    # Pommel
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY + 44),
        "r": "6",
        "fill": "#d4a846",
    }})
    return elements


def build_symbol_grief():
    """Dark sword shape - similar to Dawn's Edge but darker, more menacing."""
    elements = []
    # Blade - slightly wider, jagged
    elements.append({"tag": "path", "attribs": {
        "d": "M {cx},{tip} L {lb},{gb} L {lm},{mb} L {lb2},{ge} L {rb2},{ge} L {rm},{mb} L {rb},{gb} Z".format(
            cx=CX, tip=CY - 52,
            lb=CX - 10, gb=CY - 40,
            lm=CX - 6, mb=CY - 15,
            lb2=CX - 10, ge=CY + 15,
            rb2=CX + 10,
            rm=CX + 6,
            rb=CX + 10),
        "fill": SYMBOL_FILL,
        "opacity": "0.8",
    }})
    # Blood drip line
    elements.append({"tag": "line", "attribs": {
        "x1": str(CX), "y1": str(CY - 40),
        "x2": str(CX), "y2": str(CY + 10),
        "stroke": "#8b1a1a", "stroke-width": "2",
    }})
    # Cross-guard (curved down - menacing)
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} Q {},{} {},{}".format(
            CX - 28, CY + 12,
            CX, CY + 22,
            CX + 28, CY + 12),
        "fill": "none",
        "stroke": "#8b1a1a",
        "stroke-width": "4",
        "stroke-linecap": "round",
    }})
    # Grip
    elements.append({"tag": "rect", "attribs": {
        "x": str(CX - 4), "y": str(CY + 18),
        "width": "8", "height": "20",
        "fill": SYMBOL_FILL, "opacity": "0.7",
    }})
    # Pommel (skull-like)
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY + 42),
        "r": "6",
        "fill": "#8b1a1a",
    }})
    return elements


def build_symbol_inferno():
    """Pistol shape - side profile of a compact pistol."""
    elements = []
    # Pistol body (barrel + receiver)
    elements.append({"tag": "path", "attribs": {
        "d": (
            "M {bx},{by} "    # barrel tip
            "L {brx},{by} "   # barrel to receiver top
            "L {brx},{ry} "   # receiver top-right
            "L {grx},{ry} "   # grip top-right
            "L {gbx},{gby} "  # grip bottom-right
            "L {glx},{gby} "  # grip bottom-left
            "L {glx},{gy2} "  # grip top-left
            "L {trx},{ty} "   # trigger guard
            "L {bx},{ty} "    # back to barrel bottom
            "Z"
        ).format(
            bx=CX - 40, by=CY - 12,
            brx=CX + 20,
            ry=CY - 4,
            grx=CX + 15,
            gbx=CX + 18, gby=CY + 35,
            glx=CX + 4,
            gy2=CY + 8,
            trx=CX - 10, ty=CY,
        ),
        "fill": SYMBOL_FILL,
        "opacity": "0.9",
    }})
    # Barrel bore
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX - 40), "cy": str(CY - 6),
        "r": "3",
        "fill": "#cc4400",
    }})
    # Muzzle flare lines
    elements.append({"tag": "line", "attribs": {
        "x1": str(CX - 44), "y1": str(CY - 6),
        "x2": str(CX - 55), "y2": str(CY - 12),
        "stroke": "#cc4400", "stroke-width": "2", "stroke-linecap": "round",
    }})
    elements.append({"tag": "line", "attribs": {
        "x1": str(CX - 44), "y1": str(CY - 6),
        "x2": str(CX - 55), "y2": str(CY - 1),
        "stroke": "#cc4400", "stroke-width": "2", "stroke-linecap": "round",
    }})
    return elements


def build_symbol_baba_lysaga():
    """Twisted tree/hag — gnarled branches spreading from a hunched form."""
    elements = []
    # Trunk (bent, gnarled)
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} Q {},{} {},{} Q {},{} {},{}".format(
            CX, CY + 42,
            CX - 8, CY + 20,
            CX - 5, CY,
            CX - 15, CY - 20,
            CX - 8, CY - 38),
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "5",
        "stroke-linecap": "round",
    }})
    # Left branch
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} Q {},{} {},{}".format(
            CX - 10, CY - 10,
            CX - 35, CY - 25,
            CX - 45, CY - 40),
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "3",
        "stroke-linecap": "round",
    }})
    # Right branch
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} Q {},{} {},{}".format(
            CX - 5, CY - 15,
            CX + 20, CY - 30,
            CX + 40, CY - 38),
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "3",
        "stroke-linecap": "round",
    }})
    # Small branch
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} L {},{}".format(
            CX - 8, CY + 5,
            CX + 25, CY - 5),
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "2",
        "stroke-linecap": "round",
    }})
    # Glowing eye
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX - 3), "cy": str(CY - 30),
        "r": "5",
        "fill": "#44aa44",
    }})
    return elements


def build_symbol_elite_guard():
    """Shield with Zarovich crest — heraldic shield outline with S monogram."""
    elements = []
    # Shield shape
    elements.append({"tag": "path", "attribs": {
        "d": "M {},{} L {},{} L {},{} Q {},{} {},{} Q {},{} {},{} L {},{} Z".format(
            CX, CY - 42,
            CX + 35, CY - 30,
            CX + 35, CY + 5,
            CX + 35, CY + 30,
            CX, CY + 42,
            CX - 35, CY + 30,
            CX - 35, CY + 5,
            CX - 35, CY - 30),
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "3.5",
    }})
    # S monogram inside
    elements.append({"tag": "text", "attribs": {
        "x": str(CX), "y": str(CY + 15),
        "text-anchor": "middle",
        "font-family": "serif",
        "font-size": "55",
        "font-weight": "bold",
        "font-style": "italic",
        "fill": "#8b1a1a",
    }, "text": "S"})
    return elements


def build_symbol_servitor_guard():
    """Combat servitor — cog with targeting reticle."""
    elements = []
    # Cog outline
    cog_d = _cog_teeth_path(CX, CY, 42, 32, 8, tooth_width_deg=8)
    elements.append({"tag": "path", "attribs": {
        "d": cog_d,
        "fill": "none",
        "stroke": SYMBOL_FILL,
        "stroke-width": "2.5",
    }})
    # Targeting crosshair (horizontal)
    elements.append({"tag": "line", "attribs": {
        "x1": str(CX - 20), "y1": str(CY),
        "x2": str(CX + 20), "y2": str(CY),
        "stroke": "#556677", "stroke-width": "2",
    }})
    # Targeting crosshair (vertical)
    elements.append({"tag": "line", "attribs": {
        "x1": str(CX), "y1": str(CY - 20),
        "x2": str(CX), "y2": str(CY + 20),
        "stroke": "#556677", "stroke-width": "2",
    }})
    # Center dot
    elements.append({"tag": "circle", "attribs": {
        "cx": str(CX), "cy": str(CY),
        "r": "4",
        "fill": "#556677",
    }})
    return elements


# ---------------------------------------------------------------------------
# Assign dynamically-built symbols to their token entries
# ---------------------------------------------------------------------------

def _assign_symbols():
    """Populate the placeholder `data` lists with actual symbol elements."""
    builders = {
        "abaron.svg": build_symbol_abaron,
        "madam-eva.svg": build_symbol_madam_eva,
        "plague-revenant.svg": build_symbol_revenant,
        "warp-thrall.svg": build_symbol_thrall,
        "warp-mutant.svg": build_symbol_mutant,
        "gargoyle-servitor.svg": build_symbol_gargoyle,
        "malfunctioning-servitor.svg": build_symbol_servitor,
        "lesser-daemon.svg": build_symbol_daemon,
        "warp-hound.svg": build_symbol_hound,
        "mongrelfolk.svg": build_symbol_mongrel,
        "baba-lysaga.svg": build_symbol_baba_lysaga,
        "elite-guard.svg": build_symbol_elite_guard,
        "servitor-guard.svg": build_symbol_servitor_guard,
        "dawns-edge.svg": build_symbol_dawns_edge,
        "grief.svg": build_symbol_grief,
        "inferno-pistol.svg": build_symbol_inferno,
    }
    for token in TOKENS:
        fname = token["file"]
        if fname in builders:
            token["data"] = builders[fname]()

_assign_symbols()


# ---------------------------------------------------------------------------
# SVG generation
# ---------------------------------------------------------------------------

def _make_svg(token):
    """Build an ElementTree for a single token SVG."""
    svg = ET.Element("svg")
    svg.set("xmlns", NS)
    svg.set("viewBox", VIEWBOX)
    svg.set("width", "280")
    svg.set("height", "280")

    # Clip path for circular boundary
    defs = ET.SubElement(svg, "defs")
    clip = ET.SubElement(defs, "clipPath")
    clip.set("id", "token-clip")
    clip_circle = ET.SubElement(clip, "circle")
    clip_circle.set("cx", str(CX))
    clip_circle.set("cy", str(CY))
    clip_circle.set("r", str(RING_RADIUS))

    # Background circle
    bg = ET.SubElement(svg, "circle")
    bg.set("cx", str(CX))
    bg.set("cy", str(CY))
    bg.set("r", str(RING_RADIUS))
    bg.set("fill", BG_FILL)

    # Symbol group (clipped to circle)
    sym_g = ET.SubElement(svg, "g")
    sym_g.set("clip-path", "url(#token-clip)")

    for elem_spec in token["data"]:
        el = ET.SubElement(sym_g, elem_spec["tag"])
        for k, v in elem_spec["attribs"].items():
            el.set(k, v)
        if "text" in elem_spec:
            el.text = elem_spec["text"]

    # Ring stroke
    ring = ET.SubElement(svg, "circle")
    ring.set("cx", str(CX))
    ring.set("cy", str(CY))
    ring.set("r", str(RING_RADIUS))
    ring.set("fill", "none")
    ring.set("stroke", token["ring"])
    ring.set("stroke-width", str(RING_STROKE))

    # Label text
    label = ET.SubElement(svg, "text")
    label.set("x", str(CX))
    label.set("y", str(LABEL_Y))
    label.set("text-anchor", "middle")
    label.set("font-family", "sans-serif")
    label.set("font-size", "12")
    label.set("font-weight", "bold")
    label.set("fill", token["ring"])
    label.text = token["label"]

    return svg


def write_svg(token, output_dir):
    """Generate and write one SVG file."""
    svg = _make_svg(token)
    tree = ET.ElementTree(svg)
    filepath = os.path.join(output_dir, token["file"])

    # ET.indent requires Python 3.9+; fallback for older versions
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")

    tree.write(filepath, encoding="unicode", xml_declaration=True)

    return filepath


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Generating {len(TOKENS)} token SVGs...\n")

    generated = []
    for token in TOKENS:
        path = write_svg(token, OUTPUT_DIR)
        generated.append(path)
        print(f"  [OK] {token['file']:35s}  {token['label']}")

    print(f"\n{'='*60}")
    print(f"Generated {len(generated)} SVG token files.")
    print(f"Output: {OUTPUT_DIR}/")

    # Categories summary
    npcs = [t for t in TOKENS if t["file"] in {
        "strahd.svg", "van-richten.svg", "ireena.svg",
        "ismark.svg", "abaron.svg", "madam-eva.svg", "baba-lysaga.svg"}]
    enemies = [t for t in TOKENS if t["file"] in {
        "plague-revenant.svg", "warp-thrall.svg", "warp-mutant.svg",
        "gargoyle-servitor.svg", "malfunctioning-servitor.svg",
        "lesser-daemon.svg", "warp-hound.svg", "mongrelfolk.svg",
        "elite-guard.svg", "servitor-guard.svg"}]
    weapons = [t for t in TOKENS if t["file"] in {
        "dawns-edge.svg", "grief.svg", "inferno-pistol.svg"}]

    print(f"  NPC tokens:    {len(npcs)}")
    print(f"  Enemy tokens:  {len(enemies)}")
    print(f"  Weapon icons:  {len(weapons)}")


if __name__ == "__main__":
    main()
