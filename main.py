"""Supersonic Client - UI (CustomTkinter). Run: python main.py"""
import base64
import hashlib
import io
import json
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageDraw

import backend as B

try:
    import logo_data                         # embedded Supersonic logo + icon (works inside the .exe too)
except ImportError:                          # pragma: no cover - falls back to a drawn logo
    logo_data = None

VERSION = "2.5.0"
ctk.set_appearance_mode("Dark")
ASSETS = Path(__file__).parent / "assets"   # optional overrides: logo.png, icon.png, agent.png

BG, PANEL, CARD, CARD2, BORDER = "#050810", "#080D18", "#0B1220", "#101A2E", "#18253D"
BLUE, BLUE_H, CYAN, GREEN, PURPLE, AMBER, RED = "#2563EB", "#1D4ED8", "#38BDF8", "#22C55E", "#7C3AED", "#F59E0B", "#EF4444"
TXT, MUTED = "#F3F6FB", "#8B97AD"

# (name, modrinth slug, category, description)
ADDONS = [
    ("Sodium", "sodium", "Performance", "Boosts FPS and reduces lag."),
    ("Iris Shaders", "iris", "Visuals", "Shaders mod for stunning visuals."),
    ("Lithium", "lithium", "Performance", "Improves game performance."),
    ("Indium", "indium", "Visuals", "Better Mod Compatibility."),
    ("Phosphor", "phosphor", "Performance", "Lighting engine improvements."),
    ("FerriteCore", "ferrite-core", "Performance", "Reduces memory usage."),
    ("Starlight", "starlight", "Performance", "Lighting engine optimizer."),
    ("Entity Culling", "entityculling", "Performance", "Optimizes entity rendering."),
    ("ImmediatelyFast", "immediatelyfast", "Performance", "Reduces CPU overhead."),
    ("More Culling", "moreculling", "Performance", "Culls more, gets more FPS."),
    ("Cloth Config API", "cloth-config", "Libraries", "Config library for many mods."),
    ("Mod Menu", "modmenu", "Utility", "Add a mod menu to the game."),
    ("JEI (Just Enough Items)", "jei", "Gameplay", "View items and recipes easily."),
    ("JourneyMap", "journeymap", "Gameplay", "Real-time mapping in your world."),
    ("AppleSkin", "appleskin", "Utility", "Food stats HUD improvements."),
    ("Mouse Tweaks", "mouse-tweaks", "Utility", "Inventory management."),
    ("Krypton", "krypton", "Performance", "Optimizes the network stack."),
    ("C2ME", "c2me-fabric", "Performance", "Faster chunk loading."),
    ("ModernFix", "modernfix", "Performance", "Fixes lag, memory use and load time."),
    ("Continuity", "continuity", "Visuals", "Connected textures support."),
    ("LambDynamicLights", "lambdynamiclights", "Visuals", "Dynamic lighting from items."),
    ("Reese's Sodium Options", "reeses-sodium-options", "Visuals", "Better video settings screen."),
    ("Sodium Extra", "sodium-extra", "Visuals", "Extra video options for Sodium."),
    ("Xaero's Minimap", "xaeros-minimap", "Gameplay", "Minimap with waypoints."),
    ("Xaero's World Map", "xaeros-world-map", "Gameplay", "Full world map screen."),
    ("Jade", "jade", "Gameplay", "Shows info about what you look at."),
    ("Zoomify", "zoomify", "Gameplay", "Configurable zoom key."),
    ("Inventory Profiles Next", "inventory-profiles-next", "Utility", "Sort and organize inventory."),
    ("No Chat Reports", "no-chat-reports", "Utility", "Disables chat reporting."),
    ("Fabric API", "fabric-api", "Libraries", "Core Fabric modding library."),
    ("Architectury API", "architectury-api", "Libraries", "Cross-loader mod library."),
    ("Fabric Language Kotlin", "fabric-language-kotlin", "Libraries", "Kotlin support for Fabric mods."),
]
ADDON_MAP = {a[0]: a for a in ADDONS}
# short captions used on the Dashboard tiles
SHORT_DESC = {"Sodium": "Boosts FPS", "Iris Shaders": "Shaders Mod", "Lithium": "Performance", "Indium": "Better Mod Compat",
              "Phosphor": "Lighting Engine", "FerriteCore": "Memory Usage", "Starlight": "Lighting Optimizer",
              "Entity Culling": "Optimized Entities", "ImmediatelyFast": "Performance Boost", "More Culling": "Extra Culling"}
ESSENTIALS = [a[0] for a in ADDONS[:10]]
ADDON_TABS = ["All Addons", "Performance", "Visuals", "Gameplay", "Utility", "World Gen", "Libraries"]
MC_VERSIONS = ["1.21.4", "1.21.1", "1.20.6", "1.20.4", "1.20.1", "1.19.4", "1.18.2", "1.16.5"]


# ----------------------------------------------------------------------------
# Small UI helpers
# ----------------------------------------------------------------------------
def F(size=13, weight="normal", italic=False):
    return ctk.CTkFont(family="Segoe UI", size=size, weight=weight, slant="italic" if italic else "roman")


def card(parent, **kw):
    kw.setdefault("fg_color", CARD)
    kw.setdefault("corner_radius", 12)
    kw.setdefault("border_width", 1)
    kw.setdefault("border_color", BORDER)
    return ctk.CTkFrame(parent, **kw)


def label(parent, text="", size=13, weight="normal", color=TXT, **kw):
    justify = kw.pop("justify", None)
    kw.pop("padx", None)
    kw.pop("pady", None)
    lbl = ctk.CTkLabel(parent, text=text, font=F(size, weight), text_color=color, **kw)
    if justify:
        try:
            lbl._label.configure(justify=justify)
        except Exception:
            pass
    return lbl


def button(parent, text, command=None, primary=True, **kw):
    kw.setdefault("height", 34)
    kw.setdefault("corner_radius", 8)
    kw.setdefault("font", F(13, "bold"))
    if primary:
        kw.setdefault("fg_color", BLUE)
        kw.setdefault("hover_color", BLUE_H)
    else:
        kw.setdefault("fg_color", CARD2)
        kw.setdefault("hover_color", BORDER)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", BORDER)
    return ctk.CTkButton(parent, text=text, command=command, **kw)


def menu(parent, values, variable=None, command=None, width=150):
    return ctk.CTkOptionMenu(parent, values=values, variable=variable, command=command, width=width, height=28,
                             fg_color=CARD2, button_color=CARD2, button_hover_color=BORDER,
                             dropdown_fg_color=CARD2, font=F(12))


_LOGO_CACHE = {}


def _embedded(name):
    data = getattr(logo_data, name, None) if logo_data else None
    return Image.open(io.BytesIO(base64.b64decode(data))).convert("RGBA") if data else None


def make_logo(px):
    """The Supersonic logo as a PIL image: assets/logo.png if present, else the embedded one, else a drawn bolt."""
    if px not in _LOGO_CACHE:
        path = ASSETS / "logo.png"
        base = Image.open(path).convert("RGBA") if path.exists() else _embedded("LOGO_PNG")
        if base is not None:
            _LOGO_CACHE[px] = base.resize((px, px), Image.LANCZOS)
        else:
            s = px * 4
            im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            d.ellipse((s * .04, s * .04, s * .96, s * .96), outline=(56, 189, 248, 255), width=max(2, s // 28))
            bolt = [(.56, .10), (.24, .55), (.46, .55), (.38, .90), (.76, .42), (.52, .42)]
            d.polygon([(x * s, y * s) for x, y in bolt], fill=(37, 99, 235, 255), outline=(125, 211, 252, 255))
            _LOGO_CACHE[px] = im.resize((px, px), Image.LANCZOS)
    return _LOGO_CACHE[px]


def set_window_icon(win):
    """Taskbar / title-bar icon. CustomTkinter resets the icon shortly after start-up on Windows, so set it late."""
    try:
        icon = ASSETS / "icon.png"
        img = Image.open(icon).convert("RGBA") if icon.exists() else _embedded("ICON_PNG")
        if img is None:
            return
        ico = B.APP_DIR / "icon.ico"
        B.APP_DIR.mkdir(parents=True, exist_ok=True)
        img.save(ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

        def apply():
            try:
                if B.platform.system() == "Windows":
                    win.iconbitmap(str(ico))
                else:
                    import tkinter
                    win._icon_ref = tkinter.PhotoImage(data=base64.b64encode(_png_bytes(img.resize((128, 128)))))
                    win.iconphoto(True, win._icon_ref)
            except Exception:
                pass
        win.after(250, apply)
        win.after(900, apply)
    except Exception:
        pass


def _png_bytes(im):
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def cover(im, size, radius=10, scale=2):
    w, h = size[0] * scale, size[1] * scale
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1), Image.LANCZOS)
    left, top = (im.width - w) // 2, (im.height - h) // 2
    im = im.crop((left, top, left + w, top + h))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius * scale, fill=255)
    im.putalpha(mask)
    return im


def sparkline(parent, color, rising=True, w=90, h=28):
    cv = ctk.CTkCanvas(parent, width=w, height=h, bg=CARD2, highlightthickness=0)
    ys = [h - 4, h * .62, h * .7, h * .32, 4]
    pts = []
    for i, y in enumerate(ys):
        pts += [w * i / 4, y if rising else h - y]
    cv.create_line(*pts, fill=color, width=2, smooth=True)
    return cv


# ----------------------------------------------------------------------------
# Drawn artwork (PIL): line icons, header banner, agent robot - crisp at any size, no extra files
# ----------------------------------------------------------------------------
def _hex(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def line_icon(name, px=22, color=MUTED, stroke=2.0):
    """Outline icon drawn on a 24x24 grid, 4x supersampled. Returns a PIL RGBA image of px x px."""
    k = 4 * 4
    im = Image.new("RGBA", (24 * k, 24 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col, w = _hex(color) + (255,), int((1.6 if name == "servers" else stroke) * k)

    def P(*pts):
        return [(x * k, y * k) for x, y in pts]

    def line(*pts):
        d.line(P(*pts), fill=col, width=w, joint="curve")
        for x, y in P(pts[0], pts[-1]):
            d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=col)

    def poly(*pts):
        line(*pts, pts[0])

    def circle(cx, cy, r, fill=False):
        box = ((cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k)
        d.ellipse(box, outline=None if fill else col, fill=col if fill else None, width=w)

    def rrect(x0, y0, x1, y1, r, clear=False):
        d.rounded_rectangle((x0 * k, y0 * k, x1 * k, y1 * k), r * k, outline=col, width=w,
                            fill=(0, 0, 0, 0) if clear else None)

    if name == "home":
        line((3, 11.5), (12, 3.5), (21, 11.5))
        line((5.5, 10), (5.5, 20.5), (18.5, 20.5), (18.5, 10))
        line((10, 20.5), (10, 14), (14, 14), (14, 20.5))
    elif name == "cube":
        poly((12, 2.5), (20, 7), (20, 17), (12, 21.5), (4, 17), (4, 7))
        line((4, 7), (12, 11.8), (20, 7))
        line((12, 11.8), (12, 21.5))
    elif name == "puzzle":
        circle(10.5, 5.2, 2.6)
        circle(19.8, 14, 2.6)
        rrect(3.5, 7, 18, 21, 2.2, clear=True)
    elif name == "servers":
        for y in (3.5, 9.5, 15.5):
            rrect(3.5, y, 20.5, y + 5, 1.6)
            circle(7, y + 2.5, 0.9, fill=True)
    elif name == "image":
        rrect(3, 4, 21, 20, 2.2)
        line((3.5, 17), (9, 11.5), (13.5, 16), (16.5, 13), (20.5, 17))
        circle(16.5, 8.5, 1.5)
    elif name in ("worlds", "globe"):
        circle(12, 12, 9)
        d.ellipse((7.6 * k, 3 * k, 16.4 * k, 21 * k), outline=col, width=w)
        line((3, 12), (21, 12))
        line((4.4, 7.5), (19.6, 7.5))
        line((4.4, 16.5), (19.6, 16.5))
    elif name == "os":
        for x0, y0 in ((3, 3), (12.6, 3), (3, 12.6), (12.6, 12.6)):
            d.rectangle((x0 * k, y0 * k, (x0 + 8.4) * k, (y0 + 8.4) * k), fill=col)
    elif name == "cpu":
        rrect(6, 6, 18, 18, 1.8)
        rrect(9.6, 9.6, 14.4, 14.4, 0.8)
        for t in (9.5, 12, 14.5):
            line((t, 3), (t, 6))
            line((t, 18), (t, 21))
            line((3, t), (6, t))
            line((18, t), (21, t))
    elif name == "ram":
        rrect(3, 6.5, 21, 16, 1.6)
        for x in (6.5, 10, 13.5, 17):
            d.rectangle(((x - .7) * k, 9.2 * k, (x + .7) * k, 13 * k), fill=col)
            line((x, 16), (x, 19.5))
    elif name == "gpu":
        rrect(2.5, 5.5, 21.5, 17, 1.8)
        circle(12, 11.2, 3.3)
        circle(12, 11.2, 0.8, fill=True)
        line((6, 17), (6, 20))
        line((18, 17), (18, 20))
    elif name == "disk":
        rrect(3.5, 3.5, 20.5, 20.5, 2.4)
        line((3.5, 14), (20.5, 14))
        circle(16.5, 17.2, 0.9, fill=True)
    elif name == "bolt":
        poly((13.5, 2.5), (5, 13.5), (11, 13.5), (10, 21.5), (19, 10), (13, 10))
    elif name == "trash":
        line((4, 6.5), (20, 6.5))
        line((9, 6.5), (9, 3.8), (15, 3.8), (15, 6.5))
        line((6, 6.5), (7, 20.5), (17, 20.5), (18, 6.5))
        line((10.5, 10.5), (10.5, 17))
        line((13.5, 10.5), (13.5, 17))
    elif name == "refresh":
        d.arc((4 * k, 4 * k, 20 * k, 20 * k), 40, 320, fill=col, width=w)
        d.polygon(P((19.6, 3.2), (20.4, 9.6), (14, 8.6)), fill=col)
    elif name == "chevron":
        line((9, 5), (16, 12), (9, 19))
    elif name == "search":
        circle(10.5, 10.5, 6.5)
        line((15.4, 15.4), (20.5, 20.5))
    elif name == "download":
        line((12, 3.5), (12, 14.5))
        line((7, 10), (12, 15), (17, 10))
        line((4, 17.5), (4, 20.5), (20, 20.5), (20, 17.5))
    elif name == "gear":
        import math
        pts = []
        for i in range(16):
            a0 = math.pi * 2 * i / 16 - math.pi / 16
            r = 9.4 if i % 2 == 0 else 7.2
            pts.append((12 + r * math.cos(a0), 12 + r * math.sin(a0)))
        poly(*pts)
        circle(12, 12, 3.2)
    elif name == "robot":
        rrect(5, 8, 19, 20, 3.5)
        line((12, 8), (12, 4.5))
        circle(12, 3.6, 1.1, fill=True)
        circle(9, 13.5, 1.4, fill=True)
        circle(15, 13.5, 1.4, fill=True)
        line((3, 12), (3, 16))
        line((21, 12), (21, 16))
        line((10, 17), (14, 17))
    elif name == "discord":
        rrect(3, 6, 21, 18, 5.5)
        circle(9, 12, 1.3, fill=True)
        circle(15, 12, 1.3, fill=True)
    elif name == "github":
        circle(12, 13, 8)
        poly((5.2, 9), (5, 3.8), (9.4, 6.4))
        poly((18.8, 9), (19, 3.8), (14.6, 6.4))
        line((9, 21), (9, 18))
        line((15, 21), (15, 18))
    return im.resize((px * 2, px * 2), Image.LANCZOS)


def chip_icon(name, px=18):
    """Small coloured icons for the dashboard chips (Minecraft block, rocket, calendar)."""
    k = 16
    im = Image.new("RGBA", (24 * k, 24 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def P(*pts):
        return [(x * k, y * k) for x, y in pts]
    if name == "block":
        d.polygon(P((12, 3), (21, 7.5), (12, 12), (3, 7.5)), fill=(106, 190, 48, 255))
        d.polygon(P((3, 7.5), (12, 12), (12, 21.5), (3, 17)), fill=(134, 96, 67, 255))
        d.polygon(P((21, 7.5), (12, 12), (12, 21.5), (21, 17)), fill=(96, 68, 48, 255))
        d.polygon(P((3, 7.5), (12, 12), (12, 14), (3, 9.6)), fill=(78, 150, 36, 255))
    elif name == "rocket":
        d.polygon(P((12, 2), (16.5, 8), (15.5, 17), (8.5, 17), (7.5, 8)), fill=(226, 232, 244, 255))
        d.polygon(P((7.5, 11), (4, 17), (8.5, 15.5)), fill=(99, 102, 241, 255))
        d.polygon(P((16.5, 11), (20, 17), (15.5, 15.5)), fill=(99, 102, 241, 255))
        d.ellipse((10 * k, 7.5 * k, 14 * k, 11.5 * k), fill=(56, 189, 248, 255))
        d.polygon(P((9.5, 17), (14.5, 17), (12, 22.5)), fill=(249, 115, 22, 255))
    elif name == "calendar":
        col = (186, 196, 214, 255)
        d.rounded_rectangle((3.5 * k, 5 * k, 20.5 * k, 20.5 * k), 2.5 * k, outline=col, width=int(1.8 * k))
        d.line(P((3.5, 10), (20.5, 10)), fill=col, width=int(1.8 * k))
        d.line(P((8, 3), (8, 7)), fill=col, width=int(1.8 * k))
        d.line(P((16, 3), (16, 7)), fill=col, width=int(1.8 * k))
        d.ellipse((11 * k, 13 * k, 14.4 * k, 16.4 * k), fill=(56, 189, 248, 255))
    return im.resize((px * 2, px * 2), Image.LANCZOS)


def header_banner(w=620, h=44):
    """Glowing slanted banner behind the header tagline."""
    from PIL import ImageFilter
    s = 2
    W, H, sl = w * s, h * s, 26 * s
    pts = [(sl, 6 * s), (W - sl, 6 * s), (W - 4 * s, H - 8 * s), (4 * s, H - 8 * s)]
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.line(pts + [pts[0]], fill=(56, 189, 248, 255), width=5 * s)
    glow = glow.filter(ImageFilter.GaussianBlur(5 * s))
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(im).polygon(pts, fill=(8, 22, 48, 235))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    d.line([pts[3], pts[2]], fill=(56, 189, 248, 255), width=2 * s)                # bright bottom edge
    d.line([pts[0], pts[3]], fill=(30, 110, 190, 255), width=2 * s)
    d.line([pts[1], pts[2]], fill=(30, 110, 190, 255), width=2 * s)
    d.line([pts[0], pts[1]], fill=(20, 60, 110, 255), width=1 * s)
    return im.resize((w, h), Image.LANCZOS)


def robot_image(px=200):
    """The friendly Agent (AI) robot mascot."""
    from PIL import ImageFilter
    s, W = 3, px * 3
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    u = W / 300.0

    def R(x0, y0, x1, y1):
        return (x0 * u, y0 * u, x1 * u, y1 * u)
    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(R(40, 215, 260, 295), fill=(56, 189, 248, 90))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14 * u)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(R(95, 205, 205, 285), 38 * u, fill=(226, 232, 244, 255))                  # body
    d.rounded_rectangle(R(130, 222, 170, 250), 10 * u, fill=(18, 30, 58, 255))
    d.ellipse(R(144, 230, 156, 242), fill=(56, 189, 248, 255))
    d.ellipse(R(62, 214, 106, 262), fill=(214, 222, 238, 255))                                     # arms
    d.ellipse(R(194, 214, 238, 262), fill=(214, 222, 238, 255))
    for x0 in (30, 252):                                                                          # headphones
        d.rounded_rectangle(R(x0, 95, x0 + 24, 160), 11 * u, fill=(37, 99, 235, 255))
    d.rounded_rectangle(R(52, 38, 248, 205), 62 * u, fill=(236, 241, 250, 255))                    # head
    d.rounded_rectangle(R(52, 150, 248, 205), 62 * u, fill=(208, 217, 234, 255))
    d.rounded_rectangle(R(52, 38, 248, 190), 62 * u, fill=(238, 243, 252, 255))
    d.rounded_rectangle(R(76, 70, 224, 165), 44 * u, fill=(8, 14, 34, 255))                        # visor
    eyes = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ed = ImageDraw.Draw(eyes)
    for cx in (121, 179):
        ed.rounded_rectangle(R(cx - 13, 95, cx + 13, 135), 13 * u, fill=(34, 211, 238, 255))
    ed.arc(R(133, 118, 167, 150), 20, 160, fill=(34, 211, 238, 255), width=int(5 * u))
    im.alpha_composite(eyes.filter(ImageFilter.GaussianBlur(5 * u)))
    im.alpha_composite(eyes)
    return im.resize((px, px), Image.LANCZOS)


def shield_image(px=54):
    """Green check-shield shown on the Addons page when everything is up to date."""
    s = 4
    W = px * s
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(.5, .04), (.9, .18), (.9, .52), (.5, .96), (.1, .52), (.1, .18)]
    d.polygon([(x * W, y * W) for x, y in pts], fill=(21, 128, 61, 255))
    inner = [(.5, .12), (.82, .23), (.82, .5), (.5, .86), (.18, .5), (.18, .23)]
    d.polygon([(x * W, y * W) for x, y in inner], fill=(34, 197, 94, 255))
    d.line([(.32 * W, .48 * W), (.46 * W, .62 * W), (.70 * W, .34 * W)], fill=(6, 40, 20, 255), width=int(.09 * W), joint="curve")
    return im.resize((px, px), Image.LANCZOS)


def shield_img(px=54):
    return _cached(("shield", px), lambda: shield_image(px), (px, px))


def badge_img(name, fg, bg, px=38):
    """Rounded colour tile with a line icon on it (Quick Actions)."""
    s = 4
    W = px * s
    tile = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle((0, 0, W - 1, W - 1), 9 * s, fill=_hex(bg) + (255,))
    ic = line_icon(name, int(px * .56), fg).resize((int(px * .56) * s, int(px * .56) * s), Image.LANCZOS)
    tile.alpha_composite(ic, ((W - ic.width) // 2, (W - ic.height) // 2))
    return tile.resize((px, px), Image.LANCZOS)


def badge_icon(name, fg, bg, px=38):
    return _cached(("badge", name, fg, bg, px), lambda: badge_img(name, fg, bg, px), (px, px))


_ART = {}


def _cached(key, make, size):
    if key not in _ART:
        im = make()
        _ART[key] = ctk.CTkImage(light_image=im, dark_image=im, size=size)
    return _ART[key]


def icon_img(name, px=22, color=MUTED):
    return _cached(("icon", name, px, color), lambda: line_icon(name, px, color), (px, px))


def chip_img(name, px=18):
    return _cached(("chip", name, px), lambda: chip_icon(name, px), (px, px))


def banner_img(w=620, h=44):
    return _cached(("banner", w, h), lambda: header_banner(w, h), (w, h))


def robot_img(px=120):
    return _cached(("robot", px), lambda: robot_image(px * 2), (px, px))


class ImageStore:
    """Downloads, caches (disk + memory) and rounds images; sets them on a label when ready."""

    def __init__(self, app):
        self.app, self.mem = app, {}
        self.pool = ThreadPoolExecutor(6)

    def load(self, url, size, widget, radius=10):
        if not url:
            return
        key = (url, tuple(size), radius)
        if key in self.mem:
            return self._set(widget, self.mem[key])
        self.pool.submit(self._work, key, widget)

    def _work(self, key, widget):
        url, size, radius = key
        path = B.CACHE_DIR / "img" / (hashlib.sha1(url.encode()).hexdigest() + ".bin")
        try:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(B.http_get(url).content)
            im = cover(Image.open(path).convert("RGBA"), size, radius)
            ci = ctk.CTkImage(light_image=im, dark_image=im, size=size)
        except Exception:
            path.unlink(missing_ok=True)
            return
        self.mem[key] = ci
        self.app.ui(self._set, widget, ci)

    @staticmethod
    def _set(widget, ci):
        try:
            widget.configure(image=ci, text="")
        except Exception:
            pass    # widget was destroyed meanwhile


class TabBar(ctk.CTkFrame):
    def __init__(self, parent, labels, command):
        super().__init__(parent, fg_color="transparent")
        self.command, self.items = command, {}
        for text in labels:
            box = ctk.CTkFrame(self, fg_color="transparent")
            box.pack(side="left", padx=(0, 6))
            btn = ctk.CTkButton(box, text=text, width=len(text) * 8 + 24, height=30, fg_color="transparent",
                                hover=False, font=F(13), command=lambda t=text: self.select(t))
            btn.pack()
            line = ctk.CTkFrame(box, height=2, fg_color="transparent")
            line.pack(fill="x", padx=8)
            self.items[text] = (btn, line)
        self.select(labels[0], fire=False)

    def select(self, text, fire=True):
        for key, (btn, line) in self.items.items():
            on = key == text
            btn.configure(text_color=CYAN if on else MUTED)
            line.configure(fg_color=CYAN if on else "transparent")
        if fire:
            self.command(text)


class FormDialog(ctk.CTkToplevel):
    """fields: (key, label, 'entry', default?) or (key, label, 'menu', [values])"""

    def __init__(self, app, title, fields, on_submit, submit_text="Save"):
        super().__init__(app)
        self.title(title)
        self.configure(fg_color=PANEL)
        self.geometry(f"380x{130 + len(fields) * 74}")
        self.transient(app)
        self.after(120, self.grab_set)
        self.vars, self.on_submit = {}, on_submit
        for key, text, kind, *rest in fields:
            label(self, text, 12, color=MUTED).pack(anchor="w", padx=20, pady=(14, 2))
            if kind == "menu":
                var = ctk.StringVar(value=rest[0][0])
                menu(self, rest[0], var, width=340).pack(fill="x", padx=20)
            else:
                var = ctk.StringVar(value=rest[0] if rest else "")
                ctk.CTkEntry(self, textvariable=var, height=34).pack(fill="x", padx=20)
            self.vars[key] = var
        button(self, submit_text, self._ok).pack(fill="x", padx=20, pady=20)

    def _ok(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}
        self.destroy()
        self.on_submit(data)


class Page(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

    def on_show(self):
        pass

    def refresh_addons(self):
        pass

    def refresh_instances(self):
        pass


def make_pack_card(parent, app, pack, full=True, badge=None):
    """Modpack card used by Dashboard (compact) and Modpacks page (full)."""
    c = card(parent, corner_radius=10)
    tw, th = (215, 118) if full else (118, 66)
    thumb = label(c, "📦", 26, width=tw, height=th, fg_color=CARD2, corner_radius=10)
    thumb.pack(padx=8, pady=8)
    app.images.load(pack["thumb"], (tw, th), thumb)
    if badge:
        label(c, f" {badge} ", 9, "bold", "white", fg_color=BLUE, corner_radius=5).place(x=16, y=16)
    label(c, pack["title"], 14 if full else 11, "bold", anchor="w", wraplength=tw).pack(anchor="w", padx=10)
    sub = f"{pack['mc']}  •  by {pack['author']}" if full else pack["mc"]
    label(c, sub, 11 if full else 10, color=MUTED, anchor="w").pack(anchor="w", padx=10)
    if full:
        tags = ctk.CTkFrame(c, fg_color="transparent")
        tags.pack(anchor="w", padx=10, pady=6)
        for t in pack["tags"]:
            label(tags, f" {t} ", 10, color=CYAN, fg_color=CARD2, corner_radius=6).pack(side="left", padx=(0, 4))
        stats = ctk.CTkFrame(c, fg_color="transparent")
        stats.pack(anchor="w", padx=10)
        label(stats, f"⬇ {B.fmt_num(pack['downloads'])}", 11, color=MUTED).pack(side="left")
        label(stats, f"   ♥ {B.fmt_num(pack['rating'])}", 11, color=AMBER).pack(side="left")
    if not full:
        tag = (pack.get("tags") or ["Modpack"])[0]
        label(c, f"⚡ {tag}", 9, color=MUTED, anchor="w").pack(anchor="w", padx=10, pady=(0, 8), side="bottom")
    button(c, "⬇  Install", lambda: app.install_pack(pack), height=30 if full else 26,
           font=F(12, "bold")).pack(fill="x", padx=10, pady=(10, 6 if not full else 10), side="bottom")
    return c


# ----------------------------------------------------------------------------
# Agent panel (right column on Dashboard, full width on Agent page)
# ----------------------------------------------------------------------------
class AgentPanel(ctk.CTkFrame):
    def __init__(self, parent, app, big=False):
        super().__init__(parent, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
        self.app = app
        app.panels.append(self)
        if not big:
            self.configure(width=290)
            self.pack_propagate(False)
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 0))
        label(head, "AGENT (AI)", 15, "bold").pack(side="left")
        label(head, " BETA ", 9, "bold", "white", fg_color=BLUE, corner_radius=5).pack(side="left", padx=8)
        label(self, "Your personal AI assistant", 11, color=MUTED).pack(anchor="w", padx=16)
        bot = label(self, "", image=robot_img(150))
        bot.pack(pady=(2, 0))
        if (ASSETS / "agent.png").exists():
            bot.configure(image=ctk.CTkImage(Image.open(ASSETS / "agent.png"), size=(130, 130)))
        online = ctk.CTkFrame(self, fg_color="transparent")
        online.pack(fill="x", padx=16, pady=(2, 6))
        label(online, "●", 12, color=GREEN).pack(side="left")
        label(online, "  Agent Online", 12, color=TXT).pack(side="left")
        label(online, "⌄", 12, color=MUTED).pack(side="right")
        self.chat = ctk.CTkTextbox(self, height=400 if big else 150, fg_color=CARD2, corner_radius=10,
                                   font=F(12), wrap="word")
        self.chat.pack(fill="both" if big else "x", expand=big, padx=12)
        self.say("", f"Hello {app.cfg.get('username')}! 👋\nI am your Supersonic Agent. I can help you:\n"
                     "✓ Auto fix errors\n✓ Optimize performance\n✓ Detect crashes\n✓ Suggest solutions\n\nAsk me anything!")
        fix = card(self, fg_color=CARD2, corner_radius=10)
        fix.pack(fill="x", padx=12, pady=8)
        label(fix, "Auto Fix (One Click)", 12, "bold").pack(anchor="w", padx=12, pady=(8, 0))
        label(fix, "Detect and fix common issues", 10, color=MUTED).pack(anchor="w", padx=12)
        button(fix, "🛠  Scan & Fix", app.run_scan, fg_color=PURPLE, hover_color="#6D28D9").pack(
            fill="x", padx=12, pady=10)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16)
        label(row, "Recent Logs", 12, "bold").pack(side="left")
        ctk.CTkButton(row, text="View all", width=50, height=20, fg_color="transparent", hover=False, text_color=CYAN,
                      font=F(11), command=lambda: app.show("Agent (AI)")).pack(side="right")
        self.logs = label(self, "", 10, color=MUTED, anchor="w", justify="left", wraplength=270)
        self.logs.pack(anchor="w", padx=16, pady=(2, 6))
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(0, 12), side="bottom")
        self.entry = ctk.CTkEntry(bar, placeholder_text="Ask the Agent...", height=36)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.send())
        button(bar, "➤", self.send, width=40, height=36).pack(side="left", padx=(6, 0))
        self.refresh_logs()

    def say(self, who, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", (f"{who}: " if who else "") + text + "\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def refresh_logs(self):
        lines = [f"[{t}] {m} ✓" for t, m in self.app.logs[-4:]][::-1]
        self.logs.configure(text="\n".join(lines) or "No activity yet.")

    def send(self):
        msg = self.entry.get().strip()
        if not msg:
            return
        self.entry.delete(0, "end")
        self.say("You", msg)

        def work():
            text, action = self.app.agent.respond(msg)
            self.app.ui(self.app.say_all, text)
            if action:
                self.app.ui(self.app.run_action, action)
        self.app.bg(work)


# ----------------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------------
class DashboardPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.mini = {}
        self.packs_loaded = False
        self._job = None
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)
        self.build_hero(left)
        self.build_addons(left)
        self.build_packs(left)
        self.build_stats(left)
        AgentPanel(self, app).grid(row=0, column=1, sticky="ns")

    def build_hero(self, parent):
        hero = card(parent, corner_radius=14, height=215)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        hero.grid_propagate(False)
        title = label(hero, "SUPERSONIC CLIENT", 36, "bold")
        title.configure(font=F(36, "bold", True))
        title.place(x=28, y=22)
        label(hero, "Hyper optimized. Ultra fast. Future ready.", 16, color=TXT).place(x=30, y=82)
        logo = label(hero, "", image=ctk.CTkImage(make_logo(512), size=(250, 250)), fg_color=CARD)
        logo.place(relx=.64, rely=.5, anchor="center")
        chips = ctk.CTkFrame(hero, fg_color="transparent")
        chips.place(x=28, y=150)
        self.chips = {}
        for key, icon in (("mc", "block"), ("perf", "rocket"), ("last", "calendar")):
            box = ctk.CTkFrame(chips, fg_color=CARD2, corner_radius=8, height=38, border_width=1, border_color=BORDER)
            box.pack(side="left", padx=(0, 10))
            label(box, "", image=chip_img(icon, 18)).pack(side="left", padx=(10, 6), pady=8)
            key_lbl = label(box, "", 12, color=TXT)
            key_lbl.pack(side="left")
            val_lbl = label(box, "", 12, color=GREEN)
            val_lbl.pack(side="left", padx=(4, 12))
            self.chips[key] = (key_lbl, val_lbl)
        self.play_btn = button(hero, "▶  PLAY", self.app.launch_game, width=230, height=64, font=F(26, "bold"),
                               corner_radius=10)
        self.play_btn.place(relx=1, x=-26, y=22, anchor="ne")
        self.inst_var = ctk.StringVar()
        self.inst_menu = menu(hero, [""], self.inst_var, self.select_instance, width=230)
        self.inst_menu.configure(height=38, fg_color=CARD2, button_color=CARD2, font=F(13))
        self.inst_menu.place(relx=1, x=-26, y=100, anchor="ne")
        self.status = label(hero, "Ready to launch", 11, "bold", GREEN)
        self.status.place(relx=1, x=-26, y=150, anchor="ne")
        self.progress = ctk.CTkProgressBar(hero, width=230, height=6, progress_color=CYAN, fg_color=BORDER)
        self.progress.set(0)

    def build_addons(self, parent):
        box = card(parent)
        box.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        head = ctk.CTkFrame(box, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(12, 6))
        label(head, "⚡", 22, color=CYAN).pack(side="left", padx=(0, 10))
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "ALL ADDONS – ONE CLICK INSTALL", 14, "bold").pack(anchor="w")
        label(titles, "All essential addons. One click. Done.", 11, color=MUTED).pack(anchor="w")
        button(head, "⬇  Install All", lambda: self.app.install_addons(ESSENTIALS), primary=False,
               width=130).pack(side="right")
        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 12))
        for i, name in enumerate(ESSENTIALS):
            grid.grid_columnconfigure(i % 5, weight=1, uniform="a")
            _, slug, _, desc = ADDON_MAP[name]
            c = card(grid, corner_radius=10, height=72, fg_color=CARD2)
            c.grid(row=i // 5, column=i % 5, sticky="ew", padx=4, pady=4)
            ic = label(c, "🧩", 16, width=38, height=38, fg_color=CARD, corner_radius=9)
            ic.place(x=10, y=14)
            self.app.icon_for(ic, slug, (38, 38))
            label(c, name, 12, "bold", anchor="w").place(x=56, y=8)
            label(c, SHORT_DESC.get(name, desc.split(".")[0][:22]), 10, color=MUTED, anchor="w").place(x=56, y=28)
            st = label(c, "", 10, "bold", anchor="w")
            st.place(x=56, y=46)
            for w in (c, ic, st):
                w.bind("<Button-1>", lambda e, n=name: self.app.install_addons([n]))
            self.mini[name] = st

    def build_packs(self, parent):
        box = card(parent)
        box.grid(row=2, column=0, sticky="nsew", pady=(0, 12))
        head = ctk.CTkFrame(box, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(12, 4))
        label(head, "📦", 22, color=CYAN).pack(side="left", padx=(0, 10))
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "MODPACKS", 14, "bold").pack(anchor="w")
        label(titles, "Choose. Download. Play.", 11, color=MUTED).pack(anchor="w")
        button(head, "Browse All", lambda: self.app.show("Modpacks"), primary=False, width=110).pack(side="right")
        self.pack_row = ctk.CTkFrame(box, fg_color="transparent")
        self.pack_row.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        label(self.pack_row, "Loading modpacks from Modrinth...", 12, color=MUTED).pack(pady=30)

    def build_stats(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.grid(row=3, column=0, sticky="ew")
        row.grid_columnconfigure((0, 1, 2), weight=1, uniform="s")
        self.stat = {}
        for i, (key, title, color) in enumerate((("ram", "RAM Usage", BLUE), ("fps", "FPS Boost", GREEN),
                                                  ("ping", "Ping", PURPLE))):
            c = card(row, corner_radius=10)
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 6, 0 if i == 2 else 6))
            top = ctk.CTkFrame(c, fg_color="transparent")
            top.pack(fill="x", padx=14, pady=(10, 4))
            label(top, title, 13, color=CYAN).pack(side="left")
            val = label(top, "-", 13, "bold")
            val.pack(side="right")
            bar = ctk.CTkProgressBar(c, height=6, progress_color=color, fg_color=BORDER)
            bar.set(0)
            bar.pack(fill="x", padx=14, pady=(0, 12))
            self.stat[key] = (val, bar)

    # -- behaviour --
    def on_show(self):
        self.inst_labels = {f"{i.name} ({i.mc})": i.name for i in self.app.mgr.items}
        self.inst_menu.configure(values=list(self.inst_labels))
        self.inst_var.set(f"{self.app.inst.name} ({self.app.inst.mc})")
        self.refresh_chips()
        self.refresh_addons()
        if not self.packs_loaded:
            self.packs_loaded = True
            self.app.bg(self.load_packs)
        self.after(400, self.tick)

    def refresh_instances(self):
        self.on_show()

    def select_instance(self, shown):
        self.app.cfg.set("selected_instance", self.inst_labels.get(shown, shown))
        self.refresh_chips()
        self.app.refresh_addon_views()
        self.app.warm_instance()

    def refresh_chips(self):
        inst = self.app.inst
        self.chips["mc"][0].configure(text=f"Minecraft {inst.mc}")
        self.chips["mc"][1].configure(text="")
        self.chips["perf"][0].configure(text="Performance:")
        self.chips["perf"][1].configure(text=self.app.cfg.get("perf_mode").split()[0])
        if not inst.last_played:
            last = "Never"
        elif time.strftime("%Y%m%d", time.localtime(inst.last_played)) == time.strftime("%Y%m%d"):
            last = "Today"
        else:
            last = time.strftime("%b %d", time.localtime(inst.last_played))
        self.chips["last"][0].configure(text="Last Played:")
        self.chips["last"][1].configure(text=last, text_color="#F472B6")

    def refresh_addons(self):
        inst = self.app.inst
        for name, st in self.mini.items():
            ok = inst.has_addon(name)
            st.configure(text="✓ Installed" if ok else "Click to install", text_color=GREEN if ok else MUTED)

    def set_status(self, text, color=GREEN):
        self.status.configure(text=text[:42], text_color=color)

    def load_packs(self):
        try:
            packs, _ = self.app.mr.search(sort="downloads", limit=12)
        except Exception as e:
            self.app.ui(self.set_status, f"Modrinth offline: {e}", AMBER)
            self.packs_loaded = False
            return
        self.app.ui(self.render_packs, packs)

    def render_packs(self, packs=None):
        if packs is not None:
            self.all_packs, self.pack_offset = packs, 0
        else:                                           # arrow button: show the next six modpacks
            self.pack_offset = 0 if self.pack_offset + 6 >= len(self.all_packs) else self.pack_offset + 6
        for w in self.pack_row.winfo_children():
            w.destroy()
        shown = self.all_packs[self.pack_offset:self.pack_offset + 6]
        for i, p in enumerate(shown):
            self.pack_row.grid_columnconfigure(i, weight=1, uniform="p")
            make_pack_card(self.pack_row, self.app, p, full=False).grid(row=0, column=i, sticky="nsew", padx=4)
        if len(self.all_packs) > 6:
            self.pack_row.grid_columnconfigure(6, weight=0)
            ctk.CTkButton(self.pack_row, text="›", width=26, height=26, corner_radius=13, fg_color=CARD2,
                          hover_color=BORDER, font=F(16, "bold"), command=self.render_packs).grid(row=0, column=6, padx=(4, 0))

    def tick(self):
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        if not self.winfo_ismapped():
            return
        self.app.bg(self.measure)
        self._job = self.after(8000, self.tick)

    def measure(self):
        ram_text, ram_frac = f"{self.app.cfg.get('ram_mb') / 1024:.0f} GB alloc", 0.0
        if B.psutil:
            vm = B.psutil.virtual_memory()
            ram_text, ram_frac = f"{vm.used / 2 ** 30:.1f} GB / {vm.total / 2 ** 30:.0f} GB", vm.percent / 100
        try:
            t = time.time()
            B.requests.head("https://api.modrinth.com", timeout=5)
            ms = int((time.time() - t) * 1000)
        except Exception:
            ms = -1
        perf = [a[0] for a in ADDONS if a[2] == "Performance"]
        frac = sum(self.app.inst.has_addon(n) for n in perf) / len(perf)
        self.app.ui(self.show_stats, ram_text, ram_frac, int(120 * frac), ms)

    def show_stats(self, ram_text, ram_frac, fps, ms):
        self.stat["ram"][0].configure(text=ram_text)
        self.stat["ram"][1].set(ram_frac)
        self.stat["fps"][0].configure(text=f"+{fps}% (est.)", text_color=GREEN)
        self.stat["fps"][1].set(min(fps / 120, 1))
        self.stat["ping"][0].configure(text=f"{ms}ms" if ms >= 0 else "offline")
        self.stat["ping"][1].set(min(ms / 300, 1) if ms >= 0 else 0)


# ----------------------------------------------------------------------------
# Modpacks
# ----------------------------------------------------------------------------
class ModpacksPage(Page):
    SORTS = {"Popularity": ("downloads", 2), "Newest": ("newest", 11), "Recently Updated": ("updated", 3),
             "Relevance": ("relevance", 1), "Most Followed": ("follows", 2)}
    TABS = {"All Modpacks": None, "Popular": None, "New Releases": None, "Adventure": "adventure",
            "Tech": "technology", "Magic": "magic", "PvP": "combat", "Survival": "challenging",
            "Addons Included": "kitchen-sink"}
    CATS = {"All Categories": None, "Adventure": "adventure", "Technology": "technology", "Magic": "magic",
            "Combat": "combat", "Challenging": "challenging", "Lightweight": "lightweight", "Quests": "quests",
            "Optimization": "optimization", "Vanilla-like": "vanilla-like", "Kitchen Sink": "kitchen-sink"}

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.q, self.page, self.sort, self.cat = "", 0, "Popularity", None
        self.version, self.loader, self.source, self.token, self.loaded = "All Versions", "All Loaders", "Modrinth", 0, False
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(3, weight=1)
        head = ctk.CTkFrame(main, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew")
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "MODPACKS", 30, "bold").pack(anchor="w")
        titles.winfo_children()[0].configure(font=F(30, "bold", True))
        label(titles, "Choose. Download. Play.", 13, color=MUTED).pack(anchor="w")
        button(head, "Browse CurseForge  ↗", lambda: webbrowser.open("https://www.curseforge.com/minecraft/modpacks"),
               width=190, height=38).pack(side="right")
        button(head, "＋  Import Modpack", self.import_pack, primary=False, width=170, height=38).pack(side="right", padx=8)
        TabBar(main, list(self.TABS), self.on_tab).grid(row=1, column=0, sticky="w", pady=(8, 6))
        bar = ctk.CTkFrame(main, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        label(bar, "Sort by:", 12, color=MUTED).pack(side="left", padx=(0, 8))
        self.sort_var = ctk.StringVar(value=self.sort)
        menu(bar, list(self.SORTS), self.sort_var, self.on_sort, 170).pack(side="left")
        self.filter_var = ctk.StringVar(value="All Versions")
        menu(bar, ["All Versions"] + MC_VERSIONS, self.filter_var, lambda v: self.on_filter("version", v), 170).pack(side="right")
        label(bar, "Filter:", 12, color=MUTED).pack(side="right", padx=(0, 8))
        self.grid_host = ctk.CTkFrame(main, fg_color="transparent")
        self.grid_host.grid(row=3, column=0, sticky="nsew")
        for c in range(4):
            self.grid_host.grid_columnconfigure(c, weight=1, uniform="c")
        self.pager = ctk.CTkFrame(main, fg_color="transparent")
        self.pager.grid(row=4, column=0, pady=8)
        self.footer = card(main, corner_radius=10)
        self.footer.grid(row=5, column=0, sticky="ew")
        self.foot_labels = []
        for i, (title, icon) in enumerate((("Total Modpacks", "puzzle"), ("Installed", "cube"), ("Total Downloads", "download"),
                                           ("Storage Used", "servers"), ("Auto Update", None))):
            self.footer.grid_columnconfigure(i, weight=1, uniform="f")
            box = ctk.CTkFrame(self.footer, fg_color="transparent")
            box.grid(row=0, column=i, pady=10)
            if icon:
                label(box, "", image=icon_img(icon, 26, MUTED)).pack(side="left", padx=(0, 10))
            else:
                label(box, "●", 14, color=GREEN).pack(side="left", padx=(0, 10))
            col = ctk.CTkFrame(box, fg_color="transparent")
            col.pack(side="left")
            label(col, title, 11, color=MUTED, anchor="w").pack(anchor="w")
            v = label(col, "-", 14, "bold", anchor="w")
            v.pack(anchor="w")
            self.foot_labels.append(v)
        self.build_side()

    def build_side(self):
        side = ctk.CTkFrame(self, fg_color="transparent", width=290)
        side.grid(row=0, column=1, sticky="ns")
        self.search = ctk.CTkEntry(side, placeholder_text="Search modpacks...", height=40, width=290, fg_color=CARD,
                                   border_color=BORDER)
        self.search.pack()
        label(self.search, "", image=icon_img("search", 18, MUTED), fg_color="transparent").place(relx=1, x=-10, rely=.5, anchor="e")
        self.search.bind("<Return>", lambda e: self.do_search())
        f = card(side, width=290)
        f.pack(fill="x", pady=10)
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 4))
        label(top, "FILTERS", 13, "bold").pack(side="left")
        ctk.CTkButton(top, text="Clear All", width=60, height=20, fg_color="transparent", hover=False,
                      text_color=CYAN, font=F(11), command=self.clear_filters).pack(side="right")
        self.vars = {}
        for key, title, values in (("source", "Source", ["Modrinth", "CurseForge"]),
                                   ("version", "Minecraft Version", ["All Versions"] + MC_VERSIONS),
                                   ("loader", "Mod Loader", ["All Loaders", "Fabric", "Forge", "NeoForge", "Quilt"]),
                                   ("cat", "Categories", list(self.CATS))):
            label(f, title, 11, color=MUTED).pack(anchor="w", padx=14, pady=(6, 0))
            var = ctk.StringVar(value=values[0])
            menu(f, values, var, lambda v, k=key: self.on_filter(k, v), 262).pack(padx=14, pady=(2, 4))
            self.vars[key] = var
        self.inc_installed, self.inc_outdated = ctk.BooleanVar(value=False), ctk.BooleanVar(value=False)
        for text, var in (("Include Installed", self.inc_installed), ("Include Outdated", self.inc_outdated)):
            ctk.CTkCheckBox(f, text=text, variable=var, font=F(12), checkbox_width=18, checkbox_height=18,
                            fg_color=BLUE, border_color=BORDER, command=self.reload).pack(anchor="w", padx=14, pady=(8, 2))
        ctk.CTkFrame(f, height=10, fg_color="transparent").pack()
        feat = card(side, width=290)
        feat.pack(fill="x")
        label(feat, "FEATURED MODPACK", 12, "bold").pack(anchor="w", padx=14, pady=(12, 6))
        self.feat_img = label(feat, "📦", 26, width=262, height=110, fg_color=CARD2, corner_radius=10)
        self.feat_img.pack(padx=14)
        self.feat_name = label(feat, "-", 14, "bold", anchor="w")
        self.feat_name.pack(anchor="w", padx=14, pady=(8, 0))
        self.feat_desc = label(feat, "", 11, color=MUTED, anchor="w", justify="left", wraplength=255)
        self.feat_desc.pack(anchor="w", padx=14)
        self.feat_btn = button(feat, "⬇  Install", None)
        self.feat_btn.pack(fill="x", padx=14, pady=12)
        ask = card(side, width=290)
        ask.pack(fill="x", pady=10)
        label(ask, "Need Help Choosing?", 12, "bold").pack(anchor="w", padx=14, pady=(10, 0))
        label(ask, "Let Agent (AI) recommend the perfect modpack for you!", 10, color=MUTED, wraplength=255,
              justify="left").pack(anchor="w", padx=14)
        button(ask, "🤖  Ask Agent (AI)", lambda: self.app.show("Agent (AI)"), primary=False).pack(
            fill="x", padx=14, pady=10)

    def on_show(self):
        if not self.loaded:
            self.loaded = True
            self.reload()

    def on_tab(self, tab):
        self.page = 0
        if tab == "Popular":
            self.sort, self.cat = "Popularity", None
        elif tab == "New Releases":
            self.sort, self.cat = "Newest", None
        else:
            self.cat = self.TABS[tab]
        self.sort_var.set(self.sort)
        self.reload()

    def on_sort(self, v):
        self.sort, self.page = v, 0
        self.reload()

    def on_filter(self, key, value):
        if key == "source":
            self.source = value
        elif key == "version":
            self.version = value
            self.vars["version"].set(value)
            self.filter_var.set(value)
        elif key == "loader":
            self.loader = value
        else:
            self.cat = self.CATS[value]
        self.page = 0
        self.reload()

    def clear_filters(self):
        for key, var in self.vars.items():
            var.set({"source": "Modrinth", "version": "All Versions", "loader": "All Loaders",
                     "cat": "All Categories"}[key])
        self.filter_var.set("All Versions")
        self.source, self.version, self.loader, self.cat, self.q, self.page = "Modrinth", "All Versions", "All Loaders", None, "", 0
        self.search.delete(0, "end")
        self.reload()

    def do_search(self):
        self.q, self.page = self.search.get().strip(), 0
        self.reload()

    def goto(self, page):
        self.page = page
        self.reload()

    def reload(self):
        self.token += 1
        tok = self.token
        for w in self.grid_host.winfo_children():
            w.destroy()
        label(self.grid_host, "Loading...", 14, color=MUTED).grid(row=0, column=0, columnspan=4, pady=60)
        ver = None if self.version.startswith("All") else self.version
        loader = None if self.loader.startswith("All") else self.loader.lower()
        sort_mr, sort_cf = self.SORTS[self.sort]

        def work():
            try:
                if self.source == "Modrinth":
                    res, total = self.app.mr.search(self.q, "modpack", self.cat, ver, loader, sort_mr, self.page * 8, 8)
                else:
                    res, total = self.app.cf.search(self.q, sort_cf, ver, loader, self.page * 8, 8)
                self.app.ui(self.render, tok, res, total)
            except Exception as e:
                self.app.ui(self.show_error, tok, str(e))
        self.app.bg(work)

    def show_error(self, tok, msg):
        if tok != self.token:
            return
        for w in self.grid_host.winfo_children():
            w.destroy()
        label(self.grid_host, f"Could not load modpacks:\n{msg}", 13, color=AMBER, wraplength=700).grid(
            row=0, column=0, columnspan=4, pady=60)

    def render(self, tok, packs, total):
        if tok != self.token:
            return
        for w in self.grid_host.winfo_children():
            w.destroy()
        installed = {i.name.lower() for i in self.app.mgr.items}
        packs = [p for p in packs
                 if (self.inc_installed.get() or p["title"].lower() not in installed)
                 and (self.inc_outdated.get() or (B.mc_parts(p["mc"]) or (9,))[:2] >= (1, 20))]   # outdated = older than 1.20
        if not packs:
            label(self.grid_host, "No modpacks found.", 14, color=MUTED).grid(row=0, column=0, columnspan=4, pady=60)
        for i, p in enumerate(packs):
            badge = "MOST POPULAR" if i == 0 and self.page == 0 and self.sort == "Popularity" else (
                "NEW" if self.sort == "Newest" else None)
            make_pack_card(self.grid_host, self.app, p, True, badge).grid(
                row=i // 4, column=i % 4, sticky="nsew", padx=5, pady=5)
        if packs:
            f = packs[0]
            self.feat_name.configure(text=f["title"])
            self.feat_desc.configure(text=f["summary"][:110])
            self.feat_btn.configure(command=lambda: self.app.install_pack(f))
            self.app.images.load(f["thumb"], (262, 110), self.feat_img)
        self.build_pager(total)
        vals = (B.fmt_num(total), str(len(self.app.mgr.items)), B.fmt_num(sum(p["downloads"] for p in packs)),
                "...", "Enabled" if self.app.cfg.get("download_updates") else "Disabled")
        for lbl, v in zip(self.foot_labels, vals):
            lbl.configure(text=v)
        self.foot_labels[4].configure(text_color=GREEN)

        def size():
            gb = B.dir_size(B.INSTANCES_DIR) / 1e9
            self.app.ui(lambda: self.foot_labels[3].configure(text=f"{gb:.1f} GB"))
        self.app.bg(size)

    def build_pager(self, total):
        for w in self.pager.winfo_children():
            w.destroy()
        pages = max(1, min(-(-total // 8), 500))
        cur = self.page

        def add(text, pg, active=False, enabled=True):
            button(self.pager, text, lambda pg=pg: self.goto(pg), primary=active, width=36, height=32,
                   state="normal" if enabled else "disabled").pack(side="left", padx=3)
        add("‹", cur - 1, enabled=cur > 0)
        prev = None
        for n in sorted({0, pages - 1, *range(max(0, cur - 2), min(pages, cur + 3))}):
            if prev is not None and n - prev > 1:
                label(self.pager, "…", 13, color=MUTED).pack(side="left", padx=4)
            add(str(n + 1), n, active=n == cur)
            prev = n
        add("›", cur + 1, enabled=cur < pages - 1)

    def import_pack(self):
        path = filedialog.askopenfilename(title="Import modpack", filetypes=[("Modpack", "*.mrpack *.zip")])
        if path:
            self.app.install_pack(None, path)


# ----------------------------------------------------------------------------
# Addons
# ----------------------------------------------------------------------------
class AddonsPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.tab, self.query, self.layout, self.selected = "All Addons", "", "grid", "Sodium"
        self.remote = None      # online search results (Modrinth + CurseForge) or None for the catalog
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(3, weight=1)
        head = ctk.CTkFrame(main, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew")
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "ADDONS", 30, "bold").pack(anchor="w")
        titles.winfo_children()[0].configure(font=F(30, "bold", True))
        label(titles, "All essential addons. One click install.", 13, color=MUTED).pack(anchor="w")
        ia = ctk.CTkButton(head, text="⚡  Install All\nOne click install all addons", width=240, height=60,
                           fg_color=CARD2, hover_color=BORDER, border_width=1, border_color=BLUE, font=F(12, "bold"),
                           command=lambda: app.install_addons([a[0] for a in ADDONS]))
        ia.pack(side="right")
        self.tabbar = TabBar(main, ADDON_TABS, self.on_tab)
        self.tabbar.grid(row=1, column=0, sticky="w", pady=(8, 4))
        sec = ctk.CTkFrame(main, fg_color="transparent")
        sec.grid(row=2, column=0, sticky="ew", pady=4)
        label(sec, "⚡", 18, color=CYAN).pack(side="left", padx=(0, 8))
        t = ctk.CTkFrame(sec, fg_color="transparent")
        t.pack(side="left")
        label(t, "Essential Addons", 14, "bold").pack(anchor="w")
        self.sec_sub = label(t, "Core addons for the best experience.", 11, color=MUTED)
        self.sec_sub.pack(anchor="w")
        self.seg = ctk.CTkSegmentedButton(sec, values=["Grid", "List"], command=self.on_layout, height=30,
                                          selected_color=BLUE, unselected_color=CARD2)
        self.seg.set("Grid")
        self.seg.pack(side="right")
        self.host = ctk.CTkScrollableFrame(main, fg_color="transparent")
        self.host.grid(row=3, column=0, sticky="nsew")
        self.perf = card(main, corner_radius=10)
        self.perf.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self.build_side()

    def build_side(self):
        side = ctk.CTkFrame(self, fg_color="transparent", width=300)
        side.grid(row=0, column=1, sticky="ns")
        tiles = card(side, width=300)
        tiles.pack(fill="x")
        for i, title in enumerate(("Total Addons", "Installed")):
            box = ctk.CTkFrame(tiles, fg_color="transparent")
            box.grid(row=0, column=i, padx=18, pady=10, sticky="w")
            label(box, title, 12, color=MUTED).pack(anchor="w")
            v = label(box, "-", 22, "bold", GREEN if i else TXT)
            v.pack(anchor="w")
            setattr(self, "tile_total" if i == 0 else "tile_inst", v)
        self.uptodate = card(side, width=300)
        self.uptodate.pack(fill="x", pady=8)
        label(self.uptodate, "", image=shield_img(54)).pack(side="right", padx=16, pady=10)
        txt = ctk.CTkFrame(self.uptodate, fg_color="transparent")
        txt.pack(side="left", fill="x", expand=True)
        self.up_title = label(txt, "", 13, "bold", GREEN)
        self.up_title.pack(anchor="w", padx=14, pady=(14, 0))
        self.up_sub = label(txt, "", 11, color=MUTED)
        self.up_sub.pack(anchor="w", padx=14, pady=(0, 14))
        cats = card(side, width=300)
        cats.pack(fill="x")
        row = ctk.CTkFrame(cats, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=10)
        self.search = ctk.CTkEntry(row, placeholder_text="Search addons... (Enter = search online)", height=34)
        self.search.pack(fill="x")
        label(self.search, "", image=icon_img("search", 18, MUTED), fg_color="transparent").place(relx=1, x=-10, rely=.5, anchor="e")
        self.search.bind("<KeyRelease>", self.on_query)
        self.search.bind("<Return>", lambda e: self.search_online())
        top = ctk.CTkFrame(cats, fg_color="transparent")
        top.pack(fill="x", padx=14)
        label(top, "Categories", 13, "bold").pack(side="left")
        ctk.CTkButton(top, text="Clear", width=44, height=20, fg_color="transparent", hover=False, text_color=CYAN,
                      font=F(11), command=self.clear).pack(side="right")
        self.cat_box = ctk.CTkFrame(cats, fg_color="transparent")
        self.cat_box.pack(fill="x", padx=8, pady=(4, 10))
        info = card(side, width=300)
        info.pack(fill="x", pady=8)
        label(info, "Addon Info", 13, "bold").pack(anchor="w", padx=14, pady=(12, 6))
        top = ctk.CTkFrame(info, fg_color="transparent")
        top.pack(fill="x", padx=14)
        self.info_icon = label(top, "🧩", 22, width=56, height=56, fg_color=CARD2, corner_radius=12)
        self.info_icon.pack(side="left")
        t = ctk.CTkFrame(top, fg_color="transparent")
        t.pack(side="left", padx=10)
        self.info_name = label(t, "", 14, "bold", anchor="w")
        self.info_name.pack(anchor="w")
        self.info_cat = label(t, "", 11, color=MUTED, anchor="w")
        self.info_cat.pack(anchor="w")
        self.info_desc = label(top, "", 11, color=MUTED, anchor="w", justify="left", wraplength=120)
        self.info_desc.pack(side="left", padx=(6, 0))
        self.info_rows = {}
        rows = ctk.CTkFrame(info, fg_color="transparent")
        rows.pack(fill="x", padx=14, pady=(10, 0))
        rows.grid_columnconfigure(1, weight=1)
        for n, key in enumerate(("Status", "Version", "Minecraft", "Author")):
            label(rows, key, 11, color=MUTED, anchor="w").grid(row=n, column=0, sticky="w", pady=2)
            v = label(rows, "-", 11, anchor="w")
            v.grid(row=n, column=1, sticky="w", padx=(36, 0), pady=2)
            self.info_rows[key] = v
        ctk.CTkFrame(info, height=10, fg_color="transparent").pack()
        agent = card(side, width=300, fg_color="#0A1A3A")
        agent.pack(fill="x")
        label(agent, "", image=robot_img(64)).pack(side="left", padx=12, pady=10)
        txt = ctk.CTkFrame(agent, fg_color="transparent")
        txt.pack(side="left", pady=10)
        label(txt, "Powered by Supersonic Agent (AI)", 12, "bold", CYAN, anchor="w").pack(anchor="w")
        label(txt, "We automatically select and update the best addons for your system.", 11, color="#9DB4E0",
              justify="left", wraplength=190, anchor="w").pack(anchor="w")

    def on_show(self):
        self.refresh_addons()
        self.select(self.selected)

    def on_tab(self, tab):
        self.tab = tab
        self.tabbar.select(tab, fire=False)
        self.refresh_addons()

    def on_layout(self, v):
        self.layout = v.lower()
        self.render()

    def on_query(self, event=None):
        if event is not None and event.keysym in ("Return", "KP_Enter"):
            return
        self.query = self.search.get().strip().lower()
        self.remote = None
        self.sec_sub.configure(text="Core addons for the best experience.")
        self.render()

    def clear(self):
        self.search.delete(0, "end")
        self.query, self.remote = "", None
        self.sec_sub.configure(text="Core addons for the best experience.")
        self.render()

    def search_online(self):
        q = self.search.get().strip()
        if not q:
            return
        inst = self.app.inst
        self.sec_sub.configure(text=f"Searching Modrinth + CurseForge for '{q}'...")

        def work():
            items, notes = self.app.store.search_all(q, "mod", inst.mc, inst.loader, 12)
            self.app.ui(self.show_remote, q, items, notes)
        self.app.bg(work)

    def show_remote(self, q, items, notes):
        inst = self.app.inst
        self.remote = {"items": items, "notes": notes}
        self.sec_sub.configure(text=f"Online results for '{q}' • {inst.mc} {inst.loader.title()}")
        self.render()

    def make_remote_card(self, item):
        installed = self.app.inst.has_addon(item["title"])
        c = card(self.host, height=112, corner_radius=10)
        ic = label(c, "🧩", 20, width=46, height=46, fg_color=CARD2, corner_radius=10)
        ic.place(x=12, y=14)
        self.app.images.load(item["icon"] or item["thumb"], (46, 46), ic)
        label(c, item["title"][:20], 13, "bold", anchor="w").place(x=68, y=10)
        label(c, item["summary"][:56], 11, color=MUTED, anchor="w", justify="left", wraplength=120).place(x=68, y=32)
        mr = item["source"] == "modrinth"
        label(c, " MR " if mr else " CF ", 9, "bold", "white", fg_color=GREEN if mr else AMBER,
              corner_radius=5).place(relx=1, x=-8, y=8, anchor="ne")
        if installed:
            label(c, "✓ Installed", 11, "bold", GREEN).place(x=68, y=80)
        else:
            button(c, "Install", lambda it=item: self.app.install_item(it), height=24, width=70,
                   font=F(11, "bold")).place(x=68, y=78)
        return c

    def render_remote(self, cols):
        items, notes = self.remote["items"], self.remote["notes"]
        for i, item in enumerate(items):
            self.make_remote_card(item).grid(row=i // cols, column=i % cols, sticky="ew", padx=4, pady=4)
        if not items:
            label(self.host, "No results found.", 13, color=MUTED).grid(row=0, column=0, columnspan=4, pady=30)
        if notes:
            label(self.host, "\n".join(notes), 11, color=AMBER, wraplength=600).grid(
                row=(len(items) - 1) // cols + 1 if items else 1, column=0, columnspan=4, pady=10)

    def visible(self):
        return [a for a in ADDONS if (self.tab == "All Addons" or a[2] == self.tab)
                and (not self.query or self.query in a[0].lower() or self.query in a[3].lower())]

    def refresh_addons(self):
        inst = self.app.inst
        done = sum(inst.has_addon(a[0]) for a in ADDONS)
        self.tile_total.configure(text=str(len(ADDONS)))
        self.tile_inst.configure(text=f"{done} / {len(ADDONS)}")
        if done == len(ADDONS):
            self.up_title.configure(text="All addons are up to date!", text_color=GREEN)
            self.up_sub.configure(text="Your client is fully optimized.")
        else:
            self.up_title.configure(text=f"{len(ADDONS) - done} addons not installed", text_color=AMBER)
            self.up_sub.configure(text="Press Install All to optimize your client.")
        for w in self.cat_box.winfo_children():
            w.destroy()
        for name in ["All Categories"] + ADDON_TABS[1:]:
            n = len(ADDONS) if name == "All Categories" else sum(a[2] == name for a in ADDONS)
            if n == 0:
                continue
            on = (name == "All Categories" and self.tab == "All Addons") or name == self.tab
            row = ctk.CTkFrame(self.cat_box, fg_color="#10234A" if on else "transparent", corner_radius=6)
            row.pack(fill="x", pady=1)
            go = (lambda e=None, t=name: self.on_tab("All Addons" if t == "All Categories" else t))
            left = label(row, f"  {name}", 12, color=TXT if on else MUTED, anchor="w")
            left.pack(side="left", pady=4)
            right = label(row, f"{n}  ", 12, color=TXT if on else MUTED, anchor="e")
            right.pack(side="right", pady=4)
            for w in (row, left, right):
                w.bind("<Button-1>", go)
        self.render()
        self.update_perf()

    def render(self):
        for w in self.host.winfo_children():
            w.destroy()
        cols = 4 if self.layout == "grid" else 1
        for c in range(4):
            self.host.grid_columnconfigure(c, weight=1 if c < cols else 0, uniform="a" if c < cols else "")
        if self.remote is not None:
            return self.render_remote(cols)
        shown = self.visible()
        for i, a in enumerate(shown):
            self.make_card(a).grid(row=i // cols, column=i % cols, sticky="ew", padx=4, pady=4)
        if not shown:
            label(self.host, "Nothing in this category yet.\nType a name in the search box and press Enter to search "
                  "Modrinth + CurseForge.", 12, color=MUTED, justify="center").grid(row=0, column=0, columnspan=4, pady=40)

    def make_card(self, a):
        name, slug, cat, desc = a
        installed = self.app.inst.has_addon(name)
        c = card(self.host, height=112, corner_radius=10, border_color=CYAN if name == self.selected else BORDER)
        ic = label(c, "🧩", 20, width=46, height=46, fg_color=CARD2, corner_radius=10)
        ic.place(x=12, y=14)
        self.app.icon_for(ic, slug, (46, 46))
        title = label(c, name, 13, "bold", anchor="w")
        title.place(x=68, y=10)
        d = label(c, desc, 11, color=MUTED, anchor="w", justify="left", wraplength=120)
        d.place(x=68, y=32)
        if installed:
            st = label(c, "✓ Installed", 11, "bold", GREEN)
            st.place(x=68, y=80)
        else:
            st = button(c, "Install", lambda n=name: self.app.install_addons([n]), height=24, width=70,
                        font=F(11, "bold"))
            st.place(x=68, y=78)
        for w in (c, ic, title, d):
            w.bind("<Button-1>", lambda e, n=name: self.select(n))
        return c

    def select(self, name):
        self.selected = name
        _, slug, cat, desc = ADDON_MAP[name]
        inst = self.app.inst
        self.info_name.configure(text=name.split(" (")[0])
        self.info_cat.configure(text=cat)
        self.info_desc.configure(text=desc)
        ok = inst.has_addon(name)
        self.info_rows["Status"].configure(text="Installed" if ok else "Not installed", text_color=GREEN if ok else AMBER)
        self.info_rows["Version"].configure(text=inst.addons.get(name, {}).get("version", "..."))
        self.info_rows["Minecraft"].configure(text=inst.mc)
        self.info_rows["Author"].configure(text="...")
        self.app.icon_for(self.info_icon, slug, (56, 56))

        def work():
            try:
                info = self.app.mr.addon_info(slug, inst.mc, inst.loader)
            except Exception:
                return
            if self.selected == name:
                self.app.ui(self.fill_info, info)
        self.app.bg(work)

    def fill_info(self, info):
        self.info_desc.configure(text=info["description"])
        self.info_rows["Version"].configure(text=info["version"])
        self.info_rows["Author"].configure(text=info["author"])

    def update_perf(self):
        for w in self.perf.winfo_children():
            w.destroy()
        perf = [a[0] for a in ADDONS if a[2] == "Performance"]
        frac = sum(self.app.inst.has_addon(n) for n in perf) / len(perf)
        label(self.perf, "Performance Summary", 14, "bold").pack(anchor="w", padx=14, pady=(8, 0))
        label(self.perf, "These addons work together to deliver the best performance and stability. "
              "(Estimated from installed addons)", 11, color=MUTED).pack(anchor="w", padx=14, pady=(0, 4))
        row = ctk.CTkFrame(self.perf, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 10))
        for i, (title, val, color, rising) in enumerate((
                ("FPS Boost", f"+{int(120 * frac)}%", GREEN, True), ("RAM Usage", f"-{int(35 * frac)}%", PURPLE, False),
                ("CPU Usage", f"-{int(28 * frac)}%", GREEN, False), ("Load Time", f"-{int(40 * frac)}%", AMBER, False))):
            row.grid_columnconfigure(i, weight=1, uniform="p")
            t = ctk.CTkFrame(row, fg_color=CARD2, corner_radius=8)
            t.grid(row=0, column=i, sticky="ew", padx=4)
            label(t, title, 11, color=color).pack(anchor="w", padx=10, pady=(6, 0))
            line = ctk.CTkFrame(t, fg_color="transparent")
            line.pack(fill="x", padx=10, pady=(0, 6))
            label(line, val, 20, "bold", color).pack(side="left")
            sparkline(line, color, rising).pack(side="right")


# ----------------------------------------------------------------------------
# Instances / Servers / Resource Packs / Worlds
# ----------------------------------------------------------------------------
class ListPage(Page):
    META = {"Instances": ("INSTANCES", "Manage your Minecraft installs."),
            "Servers": ("SERVERS", "Join your favourite servers in one click."),
            "Resource Packs": ("RESOURCE PACKS", "Packs installed in the selected instance."),
            "Worlds": ("WORLDS", "Singleplayer worlds in the selected instance.")}

    def __init__(self, parent, app, kind):
        super().__init__(parent, app)
        self.kind = kind
        self.ptype, self.results = "resourcepack", None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.pack(side="left")
        label(titles, self.META[kind][0], 30, "bold").pack(anchor="w")
        titles.winfo_children()[0].configure(font=F(30, "bold", True))
        label(titles, self.META[kind][1], 13, color=MUTED).pack(anchor="w")
        if kind == "Instances":
            button(head, "＋  New Instance", self.new_instance, width=160, height=38).pack(side="right")
        elif kind == "Servers":
            button(head, "＋  Add Server", self.add_server, width=160, height=38).pack(side="right")
        else:
            button(head, "Open Folder", lambda: B.open_path(self.folder()), primary=False, width=130,
                   height=38).pack(side="right")
            if kind == "Resource Packs":
                button(head, "＋  Add Pack", self.add_pack, primary=False, width=110, height=38).pack(side="right", padx=8)
                self.seg = ctk.CTkSegmentedButton(head, values=["Resource Packs", "Shaders"], command=self.on_type,
                                                  height=34, selected_color=BLUE, unselected_color=CARD2)
                self.seg.set("Resource Packs")
                self.seg.pack(side="right")
                self.search = ctk.CTkEntry(head, placeholder_text="Search Modrinth + CurseForge...", width=230, height=38)
                self.search.pack(side="right", padx=8)
                self.search.bind("<Return>", lambda e: self.search_online())
        self.host = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.host.grid(row=1, column=0, sticky="nsew")
        self.host.grid_columnconfigure(0, weight=1)

    def folder(self):
        if self.kind == "Worlds":
            return self.app.inst.dir / "saves"
        return self.app.inst.dir / B.CONTENT_DIRS[self.ptype]

    def on_show(self):
        self.render()

    def refresh_instances(self):
        self.render()

    def row(self, icon, title, sub, buttons, selected=False, img=None):
        r = card(self.host, height=64, corner_radius=10, border_color=CYAN if selected else BORDER)
        r.pack(fill="x", pady=4)
        ic = label(r, icon, 22, width=44, height=44)
        ic.pack(side="left", padx=(12, 6), pady=10)
        if img:
            self.app.images.load(img, (44, 44), ic)
        t = ctk.CTkFrame(r, fg_color="transparent")
        t.pack(side="left")
        label(t, title, 14, "bold", anchor="w").pack(anchor="w")
        label(t, sub, 11, color=MUTED, anchor="w").pack(anchor="w")
        for text, cmd, primary in reversed(buttons):
            button(r, text, cmd, primary=primary, width=90, height=30, font=F(12, "bold")).pack(
                side="right", padx=(0, 10))

    def render(self):
        for w in self.host.winfo_children():
            w.destroy()
        app = self.app
        if self.kind == "Instances":
            for inst in app.mgr.items:
                last = time.strftime("%b %d %H:%M", time.localtime(inst.last_played)) if inst.last_played else "never played"
                sel = inst.name == app.inst.name
                self.row("🧊", inst.name, f"{inst.mc} • {inst.loader.title()} • {len(inst.addons)} addons • {last}", [
                    ("Select", lambda i=inst: self.select(i), False), ("Backup", lambda i=inst: self.backup(i), False),
                    ("Delete", lambda i=inst: self.delete(i), False)], selected=sel)
        elif self.kind == "Servers":
            for s in app.cfg.get("servers"):
                self.row("🗄", s["name"], s["address"], [
                    ("Join", lambda a=s["address"]: app.launch_game(a), True),
                    ("Remove", lambda s=s: self.remove_server(s), False)])
            if not app.cfg.get("servers"):
                label(self.host, "No servers yet. Press 'Add Server'.", 13, color=MUTED).pack(pady=40)
        else:
            if self.kind == "Resource Packs" and self.results is not None:
                label(self.host, "Search results", 13, "bold", CYAN, anchor="w").pack(anchor="w", pady=(0, 2))
                for item in self.results["items"]:
                    done = app.inst.has_addon(item["title"])
                    src = "Modrinth" if item["source"] == "modrinth" else "CurseForge"
                    self.row("🖼", item["title"][:40], f"{src} • by {item['author']} • ⬇ {B.fmt_num(item['downloads'])}",
                             [("✓ Added" if done else "Install", lambda it=item: app.install_item(it, self.render), not done)],
                             img=item["icon"] or item["thumb"])
                if self.results["notes"]:
                    label(self.host, "\n".join(self.results["notes"]), 11, color=AMBER, wraplength=700).pack(pady=6)
                label(self.host, "Installed", 13, "bold", CYAN, anchor="w").pack(anchor="w", pady=(10, 2))
            folder = self.folder()
            entries = sorted(folder.iterdir()) if folder.exists() else []
            for p in entries:
                size = B.dir_size(p) if p.is_dir() else p.stat().st_size
                btns = [("Delete", lambda p=p: self.delete_pack(p), False)] if self.kind == "Resource Packs" else []
                self.row("🖼" if self.kind == "Resource Packs" else "🌍", p.name, f"{size / 1e6:.1f} MB", btns)
            if not entries:
                label(self.host, "Nothing here yet.", 13, color=MUTED).pack(pady=40)

    def on_type(self, value):
        self.ptype = "resourcepack" if value == "Resource Packs" else "shader"
        self.results = None
        self.render()

    def search_online(self):
        q = self.search.get().strip()
        if not q:
            self.results = None
            return self.render()
        inst = self.app.inst

        def work():
            items, notes = self.app.store.search_all(q, self.ptype, inst.mc, inst.loader, 10)
            self.app.ui(self.show_results, items, notes)
        self.app.bg(work)

    def show_results(self, items, notes):
        self.results = {"items": items, "notes": notes}
        self.render()

    def select(self, inst):
        self.app.cfg.set("selected_instance", inst.name)
        self.app.refresh_all_instances()

    def backup(self, inst):
        self.app.toast("Creating backup...")

        def work():
            out = B.backup_instance(inst)
            self.app.log(f"Backup created: {out.name}")
            self.app.ui(self.app.toast, f"✓ Backup saved: {out.name}", GREEN)
        self.app.bg(work)

    def delete(self, inst):
        if len(self.app.mgr.items) == 1:
            return self.app.toast("You need at least one instance.", AMBER)
        if messagebox.askyesno("Delete instance", f"Delete '{inst.name}' and all its files?"):
            self.app.mgr.delete(inst)
            if self.app.cfg.get("selected_instance") == inst.name:
                self.app.cfg.set("selected_instance", self.app.mgr.items[0].name)
            self.app.refresh_all_instances()

    def new_instance(self):
        def create(d):
            if not d["name"]:
                return
            inst = self.app.mgr.create(d["name"], d["mc"], d["loader"])
            self.app.cfg.set("selected_instance", inst.name)
            self.app.refresh_all_instances()
        FormDialog(self.app, "New Instance", [("name", "Name", "entry", "My Instance"),
                                              ("mc", "Minecraft version", "menu", MC_VERSIONS),
                                              ("loader", "Mod loader", "menu",
                                               ["fabric", "forge", "quilt", "neoforge", "vanilla"])],
                   create, "Create")

    def add_server(self):
        def save(d):
            if d["name"] and d["address"]:
                self.app.cfg.set("servers", self.app.cfg.get("servers") + [d])
                self.render()
        FormDialog(self.app, "Add Server", [("name", "Name", "entry"), ("address", "Address (host:port)", "entry")], save)

    def remove_server(self, server):
        self.app.cfg.set("servers", [s for s in self.app.cfg.get("servers") if s != server])
        self.render()

    def add_pack(self):
        path = filedialog.askopenfilename(title="Add resource pack", filetypes=[("Resource pack", "*.zip")])
        if path:
            self.folder().mkdir(parents=True, exist_ok=True)
            B.shutil.copy(path, self.folder())
            self.render()

    def delete_pack(self, p):
        if messagebox.askyesno("Delete", f"Delete {p.name}?"):
            (B.shutil.rmtree if p.is_dir() else Path.unlink)(p)
            self.render()


# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
class SettingsPage(Page):
    TAB_CARDS = {
        "General": None,                                   # everything (the six mockup cards first)
        "Performance": ["PERFORMANCE SETTINGS", "TRANSLATION"],
        "Minecraft": ["MINECRAFT SETTINGS"],
        "Launcher": ["LAUNCHER SETTINGS"],
        "Updates": ["LAUNCHER SETTINGS", "SUPERSONIC MODS"],
        "Privacy": ["LAUNCHER SETTINGS"],
        "Advanced": ["DOWNLOAD SETTINGS", "CLOUD & SYNC", "TRANSLATION", "SUPERSONIC MODS"]}

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.tab = "General"
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()
        app, cfg = self.app, self.app.cfg
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)
        head = ctk.CTkFrame(main, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew")
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "SETTINGS", 30, "bold").pack(anchor="w")
        titles.winfo_children()[0].configure(font=F(30, "bold", True))
        label(titles, "Customize your experience.", 13, color=MUTED).pack(anchor="w")
        button(head, "⟲  Reset to Default", self.reset, primary=False, width=170, height=38).pack(side="right")
        tabs = TabBar(main, list(self.TAB_CARDS), self.on_tab)
        tabs.grid(row=1, column=0, sticky="w", pady=(8, 6))
        tabs.select(self.tab, fire=False)
        scroll = ctk.CTkScrollableFrame(main, fg_color="transparent")
        scroll.grid(row=2, column=0, sticky="nsew")
        for c in range(3):
            scroll.grid_columnconfigure(c, weight=1, uniform="s")
        ram = dict(show=lambda v: f"{v} MB", conv=lambda s: int(s.split()[0]))
        sections = [
            ("GENERAL SETTINGS", [
                ("Language", "Choose your preferred language.", "menu", "language", ["English", "বাংলা", "Hindi", "Español"], {}),
                ("Theme", "Choose your preferred theme.", "menu", "theme", ["Dark (Default)", "Midnight"], {}),
                ("Start with Windows", "Launch Supersonic Client on system startup.", "switch", "start_with_windows", None, {}),
                ("Minimize to System Tray", "Close button will minimize the app to tray.", "switch", "minimize_to_tray", None, {}),
                ("Confirm Before Exit", "Show confirmation dialog when exiting.", "switch", "confirm_exit", None, {})]),
            ("PERFORMANCE SETTINGS", [
                ("Performance Mode", "Optimize launcher performance.", "menu", "perf_mode",
                 ["Ultra (Recommended)", "Balanced", "Low"], {}),
                ("RAM Allocation (Default)", "Set default RAM for new instances.", "menu", "ram_mb",
                 ["2048 MB", "4096 MB", "6144 MB", "8192 MB", "12288 MB", "16384 MB"], ram),
                ("Preload Assets", "Preload game assets in background.", "switch", "preload_assets", None, {}),
                ("Smart Memory Management", "Automatically clean memory when needed.", "switch", "smart_memory", None, {}),
                ("Optimize Launcher", "Apply advanced optimizations.", "switch", "optimize_launcher", None, {})]),
            ("MINECRAFT SETTINGS", [
                ("Default Java Version", "Select default Java runtime.", "menu", "java_version",
                 ["Auto (Recommended)", "Java 8", "Java 17", "Java 21"], {}),
                ("Minecraft Folder", "Change the .minecraft directory.", "button", "Open Folder",
                 lambda: B.open_path(B.MC_ROOT), {}),
                ("Automatically Install Java", "Install recommended Java if missing.", "switch", "auto_java", None, {}),
                ("Use Native Libraries", "Use native libraries for better performance.", "switch", "native_libs", None, {}),
                ("Launcher Visibility", "Keep launcher open while Minecraft is running.", "switch", "keep_launcher_open", None, {})]),
            ("LAUNCHER SETTINGS", [
                ("Check for Updates", "Automatically check for launcher updates.", "switch", "check_updates", None, {}),
                ("Download Updates", "Download updates in background.", "switch", "download_updates", None, {}),
                ("Beta Updates", "Receive beta updates and features.", "switch", "beta_updates", None, {}),
                ("Analytics", "Help improve Supersonic with anonymous data.", "switch", "analytics", None, {}),
                ("Crash Reports", "Automatically send crash reports.", "switch", "crash_reports", None, {})]),
            ("DOWNLOAD SETTINGS", [
                ("Download Speed Limit", "Limit download speed.", "menu", "download_limit", ["Unlimited", "10 MB/s", "5 MB/s"], {}),
                ("Max Connections", "Set maximum parallel downloads.", "menu", "max_connections",
                 ["4", "8", "16", "32"], dict(show=str, conv=int)),
                ("Metadata Sources", "Select mod download sources.", "button", "Configure", self.cf_key, {}),
                ("Verify Downloads", "Verify files after download.", "switch", "verify_downloads", None, {}),
                ("Delete Temp Files", "Automatically delete temporary files.", "menu", "delete_temp", ["Always", "Never"], {})]),
            ("CLOUD & SYNC", [
                ("Enable Cloud Sync", "Sync instances and settings.", "switch", "cloud_sync", None, {}),
                ("Sync Across Devices", "Keep data synced across devices.", "switch", "sync_devices", None, {}),
                ("Backup Instances", "Backup instances to cloud.", "button", "Manage", self.backup, {}),
                ("Restore from Backup", "Restore instances from cloud backup.", "button", "Restore", self.restore, {})]),
            ("TRANSLATION", [
                ("OpenGL → D3D12", "Windows only. Auto picks D3D12 when your PC supports it.", "menu",
                 "translation_mode", list(B.TRANSLATION_MODES), dict(after=self.translation_changed)),
                ("Translated Files", "Where translated files used by GPU/CPU while playing are kept.", "menu",
                 "translation_folder", list(B.TRANSLATION_FOLDERS), dict(width=160)),
                ("Translation Folder", "Open the folder with translated files.", "button", "Open Folder",
                 self.open_translation, {}),
                ("Translated Cache", "Delete translated shader files (rebuilt automatically).", "button", "Clear",
                 self.clear_translation, {})]),
            ("SUPERSONIC MODS", [
                ("Auto Install Mods", "Install mods from the Supersonic mods repo for supported versions.", "switch",
                 "auto_custom_mods", None, {}),
                ("Check for New Mods", "New mods are also checked every time the app starts.", "button",
                 "Check Now", lambda: self.app.sync_custom_mods(manual=True), {}),
                ("Mods Repository", "Open the GitHub repository with the mods.", "button", "Open",
                 lambda: webbrowser.open(f"https://github.com/{self.app.custom_mods.repo}"), {})]),
        ]
        wanted = self.TAB_CARDS[self.tab]
        if wanted:
            sections = [sec for sec in sections if sec[0] in wanted]
        for i, (title, rows) in enumerate(sections):
            c = card(scroll)
            c.grid(row=i // 3, column=i % 3, sticky="nsew", padx=5, pady=5)
            label(c, title, 12, "bold").pack(anchor="w", padx=16, pady=(14, 4))
            for r in rows:
                self.row(c, *r)
            if title == "CLOUD & SYNC":
                used = B.dir_size(B.BACKUP_DIR) / 1e9 if B.BACKUP_DIR.exists() else 0
                line = ctk.CTkFrame(c, fg_color="transparent")
                line.pack(fill="x", padx=16, pady=(8, 2))
                label(line, "Backup Storage Used", 11, color=TXT).pack(side="left")
                label(line, f"{used:.1f} GB / 10 GB", 11, color=MUTED).pack(side="right")
                bar = ctk.CTkProgressBar(c, height=6, progress_color=BLUE, fg_color=BORDER)
                bar.set(min(used / 10, 1))
                bar.pack(fill="x", padx=16, pady=(0, 14))
            if title == "TRANSLATION":
                self.tr_status = label(c, self.translation_text(), 10, color=MUTED, anchor="w", justify="left",
                                       wraplength=290)
                self.tr_status.pack(anchor="w", padx=16, pady=(2, 12))
            elif title == "SUPERSONIC MODS":
                self.mods_status = label(c, self.mods_text(), 10, color=MUTED, anchor="w", justify="left",
                                         wraplength=290)
                self.mods_status.pack(anchor="w", padx=16, pady=(2, 12))
        self.build_side()

    def row(self, parent, title, desc, kind, key, values, opts):
        cfg = self.app.cfg
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", padx=16, pady=6)
        left = ctk.CTkFrame(r, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        label(left, title, 12, "bold", anchor="w").pack(anchor="w")
        label(left, desc, 10, color=MUTED, anchor="w", justify="left", wraplength=150).pack(anchor="w")
        if kind == "menu":
            show, conv = opts.get("show", str), opts.get("conv", str)
            var = ctk.StringVar(value=show(cfg.get(key)))
            after = opts.get("after")

            def changed(v, key=key, conv=conv, after=after):
                cfg.set(key, conv(v))
                if after:
                    after()
            menu(r, values, var, changed, opts.get("width", 120)).pack(side="right")
        elif kind == "switch":
            var = ctk.BooleanVar(value=bool(cfg.get(key)))
            ctk.CTkSwitch(r, text="", width=44, variable=var, progress_color=BLUE,
                          command=lambda: cfg.set(key, var.get())).pack(side="right")
        else:
            button(r, key, values, primary=False, width=90, height=28, font=F(12)).pack(side="right")

    def on_tab(self, tab):
        self.tab = tab
        self.build()

    # -- translation / mods helpers --
    def translation_text(self):
        tr = self.app.launcher.translation
        folder = "hidden" if tr.hidden else "visible"
        return f"{tr.describe()}\nTranslated files folder: {folder}"

    def translation_changed(self):
        self.app.launcher.translation.reset_state()      # a new choice clears an automatic OpenGL fallback
        self.refresh_status()

    def open_translation(self):
        tr = self.app.launcher.translation
        tr._prepare_root()
        B.open_path(tr.root)

    def clear_translation(self):
        freed = self.app.launcher.translation.clear()
        self.app.log(f"Cleared {freed / 1e6:.0f} MB of translated files")
        self.app.toast(f"✓ Cleared {freed / 1e6:.0f} MB of translated files", GREEN)

    def mods_text(self):
        info = self.app.custom_mods.info()
        when = time.strftime("%d %b %H:%M", time.localtime(info["checked"])) if info["checked"] else "never"
        return f"{info['files']} mods in repo · {info['installed']} installed · last check: {when}"

    def refresh_status(self):
        try:
            self.tr_status.configure(text=self.translation_text())
            self.mods_status.configure(text=self.mods_text())
        except Exception:
            pass

    def build_side(self):
        side = ctk.CTkFrame(self, fg_color="transparent", width=300)
        side.grid(row=0, column=1, sticky="ns")
        sysbox = card(side, width=300)
        sysbox.pack(fill="x")
        label(sysbox, "SYSTEM OVERVIEW", 12, "bold").pack(anchor="w", padx=14, pady=(12, 6))
        self.sys_labels = {}
        for key, icon in (("OS", "os"), ("CPU", "cpu"), ("RAM", "ram"), ("GPU", "gpu"), ("Storage", "disk")):
            r = ctk.CTkFrame(sysbox, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=5)
            label(r, "", image=icon_img(icon, 22, "#3B82F6")).pack(side="left", padx=(0, 12))
            label(r, key, 12).pack(side="left")
            v = label(r, "...", 11, color=MUTED, wraplength=150, anchor="e", justify="right")
            v.pack(side="right")
            self.sys_labels[key] = v
        button(sysbox, "〰  Run Diagnostics", self.app.run_diagnostics, primary=False, height=40,
               text_color=CYAN).pack(fill="x", padx=14, pady=12)
        quick = card(side, width=300)
        quick.pack(fill="x", pady=8)
        label(quick, "AGENT (AI) QUICK ACTIONS", 12, "bold").pack(anchor="w", padx=14, pady=(12, 6))
        for title, sub, act, icon, fg, bg in (
                ("Auto Fix Errors", "Detect and fix issues.", "scan", "gear", "#60A5FA", "#12264D"),
                ("Optimize Performance", "Improve FPS & stability.", "essentials", "bolt", "#4ADE80", "#0F2E1E"),
                ("Clean Junk Files", "Free up storage space.", "clean", "trash", "#FBBF24", "#33260C"),
                ("Reset Configurations", "Reset settings to optimal.", "reset", "refresh", "#F472B6", "#33142B")):
            row = ctk.CTkFrame(quick, fg_color=CARD2, corner_radius=10, height=54)
            row.pack(fill="x", padx=12, pady=3)
            row.pack_propagate(False)
            ic = label(row, "", image=badge_icon(icon, fg, bg, 36))
            ic.pack(side="left", padx=(8, 10))
            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left")
            t1 = label(col, title, 12, "bold", anchor="w")
            t1.pack(anchor="w")
            t2 = label(col, sub, 10, color=MUTED, anchor="w")
            t2.pack(anchor="w")
            chev = label(row, "", image=icon_img("chevron", 14, MUTED))
            chev.pack(side="right", padx=12)
            for w in (row, ic, col, t1, t2, chev):
                w.bind("<Button-1>", lambda e, a=act: self.quick(a))
        ctk.CTkButton(quick, text="  Open Agent (AI)", image=robot_img(26), compound="left", height=44,
                      fg_color="#0E1F45", hover_color="#12295A", border_width=1, border_color=BLUE, text_color=CYAN,
                      font=F(14, "bold"), command=lambda: self.app.show("Agent (AI)")).pack(fill="x", padx=12, pady=10)
        about = card(side, width=300)
        about.pack(fill="x")
        label(about, "ABOUT", 12, "bold").pack(anchor="w", padx=14, pady=(12, 4))
        label(about, f"Supersonic Client v{VERSION}", 13, "bold").pack(anchor="w", padx=14)
        label(about, "The next generation Minecraft launcher.", 11, color=MUTED).pack(anchor="w", padx=14, pady=(0, 70))
        label(about, "", image=ctk.CTkImage(make_logo(256), size=(120, 120))).place(relx=1, x=-14, rely=1, y=-6, anchor="se")

    def on_show(self):
        if self.sys_labels["OS"].cget("text") == "...":
            def work():
                info = B.system_info()
                self.app.ui(lambda: [self.sys_labels[k].configure(text=v) for k, v in info.items()])
            self.app.bg(work)

    def quick(self, action):
        if action == "clean":
            freed = B.clean_cache()
            for log in self.app.inst.dir.glob("logs/*.gz"):
                freed += log.stat().st_size
                log.unlink(missing_ok=True)
            self.app.log(f"Cleaned {freed / 1e6:.0f} MB of cached downloads and old logs")
            self.app.toast(f"✓ Freed {freed / 1e6:.0f} MB", GREEN)
        elif action == "reset":
            self.reset()
        else:
            self.app.run_action(action)

    def reset(self):
        if messagebox.askyesno("Reset", "Reset all settings to default?"):
            self.app.cfg.reset()
            self.build()
            self.on_show()

    def cf_key(self):
        FormDialog(self.app, "CurseForge API key", [("key", "API key (console.curseforge.com)", "entry",
                                                     self.app.cfg.get("curseforge_key"))],
                   lambda d: self.app.cfg.set("curseforge_key", d["key"]))

    def backup(self):
        inst = self.app.inst
        self.app.toast("Creating backup...")
        self.app.bg(lambda: self.app.ui(self.app.toast, f"✓ Saved {B.backup_instance(inst).name}", GREEN))

    def restore(self):
        B.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        path = filedialog.askopenfilename(initialdir=str(B.BACKUP_DIR), filetypes=[("Backup", "*.zip")])
        if path:
            inst = B.restore_backup(path, self.app.mgr)
            self.app.log(f"Restored instance {inst.name}")
            self.app.refresh_all_instances()


# ----------------------------------------------------------------------------
# Agent page
# ----------------------------------------------------------------------------
class AgentPage(Page):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        label(self, "AGENT (AI)", 30, "bold").grid(row=0, column=0, sticky="w")
        self.winfo_children()[0].configure(font=F(30, "bold", True))
        AgentPanel(self, app, big=True).grid(row=1, column=0, sticky="nsew", pady=10)


# ----------------------------------------------------------------------------
# Application shell
# ----------------------------------------------------------------------------
NAV = [("Dashboard", "home"), ("Modpacks", "cube"), ("Addons", "puzzle"), ("Instances", "cube"), ("Servers", "servers"),
       ("Resource Packs", "image"), ("Worlds", "worlds"), ("Settings", "gear"), ("Agent (AI)", "robot")]
BADGES = {"Addons": ("NEW", PURPLE), "Agent (AI)": ("AI", GREEN)}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = B.Config()
        self.mgr = B.InstanceManager()
        self.launcher = B.Launcher(self.cfg)
        self.custom_mods = B.CustomMods(self.cfg)
        self.mods_busy = False
        self.mr, self.cf = B.Modrinth(), B.CurseForge(self.cfg)
        self.packs = B.PackInstaller(self.cfg, self.mgr, self.cf)
        self.store = B.Store(self.mr, self.cf)
        self.agent = B.Agent(self.cfg)
        self.images = ImageStore(self)
        self.logs, self.panels, self.icon_urls, self.icon_waiters = [], [], {}, []
        self.running = self.busy_addons = self.busy_pack = False
        self._toast_id = None
        self.title("Supersonic Client")
        set_window_icon(self)
        self.geometry("1440x900")
        self.minsize(1240, 780)
        self.configure(fg_color=BG)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.build_header()
        self.build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=1, column=1, sticky="nsew", padx=14, pady=(10, 14))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self.pages = {
            "Dashboard": DashboardPage(self.content, self), "Modpacks": ModpacksPage(self.content, self),
            "Addons": AddonsPage(self.content, self), "Instances": ListPage(self.content, self, "Instances"),
            "Servers": ListPage(self.content, self, "Servers"),
            "Resource Packs": ListPage(self.content, self, "Resource Packs"),
            "Worlds": ListPage(self.content, self, "Worlds"), "Settings": SettingsPage(self.content, self),
            "Agent (AI)": AgentPage(self.content, self)}
        self.toast_lbl = label(self, "", 13, "bold", "white", corner_radius=10, height=40, wraplength=760)
        self.show("Dashboard")
        self.bg(self.load_addon_icons)
        self.warm_instance()
        self.log("Supersonic Client started")
        self.after(1500, self.sync_custom_mods)          # check the mods repo for new / updated mods

    # -- threading helpers --
    def ui(self, fn, *args):
        self.after(0, lambda: fn(*args))

    def bg(self, fn, *args):
        threading.Thread(target=fn, args=args, daemon=True).start()

    # -- shell --
    def build_header(self):
        bar = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=70)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        bar.pack_propagate(False)
        label(bar, "", image=ctk.CTkImage(make_logo(256), size=(62, 62))).pack(side="left", padx=(16, 12))
        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.pack(side="left")
        top = ctk.CTkFrame(brand, fg_color="transparent")
        top.pack(anchor="w")
        name = label(top, "SUPERSONIC", 22, "bold")
        name.configure(font=F(22, "bold", True))
        name.pack(side="left")
        label(top, f"  v{VERSION}", 12, color=MUTED).pack(side="left", pady=(6, 0))
        label(brand, "C  L  I  E  N  T", 9, color=MUTED, anchor="w").pack(anchor="w")
        banner = label(bar, "", image=banner_img(640, 46))
        banner.place(relx=.5, rely=.5, anchor="center")
        tag = "THE  NEXT  GENERATION  MINECRAFT  LAUNCHER"
        label(bar, " ".join(tag), 11, "bold", CYAN, fg_color="#08162F").place(relx=.5, rely=.46, anchor="center")

    def build_sidebar(self):
        side = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, width=240)
        side.grid(row=1, column=0, sticky="ns")
        side.pack_propagate(False)
        self.nav = {}
        for name, icon in NAV:
            row = ctk.CTkFrame(side, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            btn = ctk.CTkButton(row, text=f"  {name}", image=icon_img(icon, 22, MUTED), compound="left", anchor="w",
                                height=44, corner_radius=10, fg_color="transparent", hover_color=CARD2,
                                text_color=MUTED, border_color=BLUE, font=F(14), command=lambda n=name: self.show(n))
            btn.pack(fill="x")
            self.nav[name] = btn
            if name in BADGES:
                text, color = BADGES[name]
                label(row, f" {text} ", 9, "bold", "white", fg_color=color, corner_radius=5).place(relx=1, x=-12, rely=.5,
                                                                                                    anchor="e")
        bottom = ctk.CTkFrame(side, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=14, pady=14)
        acc = card(bottom, corner_radius=10)
        acc.pack(fill="x")
        self.avatar = label(acc, "👤", 22, width=44, height=44, fg_color=CARD2, corner_radius=22)
        self.avatar.pack(side="left", padx=10, pady=10)
        t = ctk.CTkFrame(acc, fg_color="transparent")
        t.pack(side="left")
        self.acc_name = label(t, "", 13, "bold", anchor="w")
        self.acc_name.pack(anchor="w")
        label(t, "♛ Premium", 11, "bold", AMBER, anchor="w").pack(anchor="w")
        for w in (acc, self.avatar, t, self.acc_name):
            w.bind("<Button-1>", lambda e: self.edit_username())
        self.update_account()
        foot = ctk.CTkFrame(bottom, fg_color="transparent")
        foot.pack(fill="x", pady=(14, 0))
        label(foot, "SUPERSONIC CLIENT", 11, color=MUTED, anchor="w").pack(anchor="w", padx=4)
        label(foot, "© 2026 Supersonic Client", 10, color="#5D6B85", anchor="w").pack(anchor="w", padx=4)
        label(foot, "All rights reserved.", 10, color="#5D6B85", anchor="w").pack(anchor="w", padx=4, pady=(0, 6))
        for text, key, icon, color in (("Website", "website_url", "globe", MUTED), ("Discord", "discord_url", "discord", "#5B7CFA"),
                                       ("GitHub", "github_url", "github", MUTED)):
            ctk.CTkButton(foot, text=f"  {text}", image=icon_img(icon, 18, color), compound="left", anchor="w", width=120,
                          height=26, fg_color="transparent", hover=False, text_color=color if icon == "discord" else MUTED,
                          font=F(12), command=lambda k=key: webbrowser.open(self.cfg.get(k))).pack(anchor="w")

    def update_account(self):
        name = self.cfg.get("username")
        self.acc_name.configure(text=name)
        self.images.load(f"https://mc-heads.net/avatar/{name}/64", (44, 44), self.avatar, radius=22)

    def edit_username(self):
        def save(d):
            if d["name"]:
                self.cfg.set("username", d["name"])
                self.update_account()
        FormDialog(self, "Account", [("name", "Minecraft username (offline mode)", "entry", self.cfg.get("username"))], save)

    def show(self, name):
        icons = dict(NAV)
        for key, btn in self.nav.items():
            on = key == name
            btn.configure(fg_color="#0F2349" if on else "transparent", text_color=TXT if on else MUTED,
                          border_width=1 if on else 0, image=icon_img(icons[key], 22, CYAN if on else MUTED))
        for page in self.pages.values():
            page.grid_forget()
        page = self.pages[name]
        page.grid(row=0, column=0, sticky="nsew")
        page.on_show()

    def on_close(self):
        if self.cfg.get("confirm_exit") and not messagebox.askyesno("Exit", "Close Supersonic Client?"):
            return
        self.destroy()

    @property
    def inst(self):
        return self.mgr.get(self.cfg.get("selected_instance")) or self.mgr.items[0]

    def refresh_addon_views(self):
        for p in self.pages.values():
            p.refresh_addons()

    def refresh_all_instances(self):
        for p in self.pages.values():
            p.refresh_instances()
        self.refresh_addon_views()
        self.warm_instance()

    def warm_instance(self):
        """Install game files in the background so the PLAY button is instant (setting: Preload Assets)."""
        if not self.cfg.get("preload_assets"):
            return
        inst, dash = self.inst, self.pages["Dashboard"]

        def work():
            try:
                if self.launcher.is_ready(inst) or self.running:
                    return
                self.ui(dash.set_status, "Preparing game files in background...", CYAN)
                self.launcher.prepare(inst)
                if not self.running:
                    self.ui(dash.set_status, "Ready to launch (preloaded)", GREEN)
            except Exception:
                pass        # offline or failed: PLAY will retry and show the real error
        self.bg(work)

    # -- feedback --
    def toast(self, msg, color=BLUE):
        self.toast_lbl.configure(text=f"   {msg}   ", fg_color=color)
        self.toast_lbl.place(relx=.5, rely=.97, anchor="s")
        self.toast_lbl.lift()
        if self._toast_id:
            self.after_cancel(self._toast_id)
        self._toast_id = self.after(5000, self.toast_lbl.place_forget)

    def log(self, msg):
        self.logs.append((time.strftime("%H:%M"), msg))
        self.ui(lambda: [p.refresh_logs() for p in self.panels])

    def say_all(self, text):
        for p in self.panels:
            p.say("Agent", text)

    # -- icons --
    def icon_for(self, lbl, slug, size=(44, 44)):
        url = self.icon_urls.get(slug)
        if url:
            self.images.load(url, size, lbl)
        else:
            self.icon_waiters.append((lbl, slug, size))

    def load_addon_icons(self):
        cache = B.CACHE_DIR / "icons.json"
        urls = {}
        try:
            data = self.mr.projects([a[1] for a in ADDONS])
            urls = {slug: p.get("icon_url") for slug, p in data.items()}
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(urls))
        except Exception:
            if cache.exists():
                urls = json.loads(cache.read_text())
        self.icon_urls = urls
        self.ui(self.flush_icons)

    def flush_icons(self):
        for lbl, slug, size in self.icon_waiters:
            self.icon_for(lbl, slug, size)
        self.icon_waiters = []

    # -- actions --
    def sync_custom_mods(self, manual=False):
        """Installs / updates the Supersonic repo mods in all matching instances (runs in the background)."""
        if self.mods_busy or not (manual or self.cfg.get("auto_custom_mods")):
            return
        self.mods_busy = True
        if manual:
            self.toast("Checking Supersonic mods...")

        def work():
            try:
                rep = self.custom_mods.sync(list(self.mgr.items), prune=True)
                done = self.custom_mods.summary(rep)
                for key in ("installed", "updated", "removed", "skipped"):
                    for line in rep[key]:
                        self.log(f"Supersonic mods - {key}: {line}")
                for name in rep["new_in_repo"]:
                    self.log(f"New mod in Supersonic repo: {name}")
                for err in rep["errors"]:
                    self.log(f"Supersonic mods warning: {err}")
                if done:
                    self.ui(self.toast, f"✓ Supersonic mods: {done}", GREEN)
                elif manual and rep["errors"]:
                    self.ui(self.toast, rep["errors"][0], AMBER)
                elif manual:
                    self.ui(self.toast, "✓ Supersonic mods are up to date", GREEN)
            except Exception as e:                       # noqa: BLE001 - never break the app because of mods sync
                self.log(f"Supersonic mods sync failed: {e}")
            finally:
                self.mods_busy = False
                self.ui(self.pages["Settings"].refresh_status)
        self.bg(work)

    def launch_game(self, server=None):
        if self.running:
            return
        dash = self.pages["Dashboard"]
        inst = self.inst
        self.running = True
        dash.play_btn.configure(state="disabled", text="LAUNCHING...")
        dash.progress.place(relx=1, x=-26, y=162, anchor="ne")

        def work():
            retry = False
            try:
                if self.cfg.get("auto_custom_mods"):
                    self.ui(dash.set_status, "Checking Supersonic mods...", CYAN)
                    try:
                        rep = self.custom_mods.ensure(inst)
                        if rep["installed"] or rep["updated"] or rep["removed"]:
                            self.log(f"Supersonic mods for {inst.name}: {self.custom_mods.summary(rep)}")
                    except Exception as e:               # noqa: BLE001 - mods are optional, the game must still start
                        self.log(f"Supersonic mods check skipped: {e}")
                proc = self.launcher.launch(inst, lambda s: self.ui(dash.set_status, s, CYAN),
                                            lambda f: self.ui(dash.progress.set, f), server)
                inst.last_played = time.time()
                self.mgr.save()
                self.ui(dash.set_status, "Game is running!", GREEN)
                self.log(f"Launched {inst.name} ({inst.mc})")
                if proc.translation:
                    self.log("Rendering: OpenGL → D3D12 translation")
                elif proc.translation_note and self.cfg.get("translation_mode") != "OpenGL":
                    self.log(f"Rendering: OpenGL ({proc.translation_note})")
                hide = not self.cfg.get("keep_launcher_open")
                if hide:
                    self.ui(self.withdraw)
                started = time.time()
                proc.wait()
                if hide:
                    self.ui(self.deiconify)
                early_crash = bool(proc.returncode) and time.time() - started < 25
                if early_crash and self.launcher.translation.record_launch(proc.translation, True):
                    retry = True                         # Auto mode: D3D12 crashed, run again with plain OpenGL
                    self.log("D3D12 translation crashed at start - switching to OpenGL")
                    self.ui(self.toast, "D3D12 failed - restarting with OpenGL", AMBER)
                elif early_crash:
                    self.launcher.invalidate(inst)      # next PLAY re-verifies game files once
                if proc.returncode and not retry:
                    self.log(f"Game exited with code {proc.returncode}")
                    self.ui(self.toast, "Game crashed - open Agent (AI) and press Scan & Fix", AMBER)
            except Exception as e:
                self.ui(dash.set_status, f"Error: {e}", RED)
                self.log(f"Launch failed: {e}")
            finally:
                self.ui(self.launch_done)
                if retry:
                    self.ui(self.launch_game, server)
        self.bg(work)

    def launch_done(self):
        dash = self.pages["Dashboard"]
        self.running = False
        dash.play_btn.configure(state="normal", text="▶  PLAY")
        dash.progress.place_forget()
        dash.refresh_chips()

    def install_pack(self, pack, local_file=None):
        if self.busy_pack:
            return self.toast("Another modpack is installing...", AMBER)
        self.busy_pack = True
        self.toast(f"Installing {pack['title'] if pack else 'modpack'}...")

        def work():
            try:
                status = lambda s: self.ui(self.toast, s)
                if local_file:
                    inst, skipped = self.packs.import_file(local_file, status, lambda f: None)
                else:
                    inst, skipped = self.packs.install(pack, status, lambda f: None)
                self.cfg.set("selected_instance", inst.name)
                self.log(f"Installed modpack {inst.name}")
                msg = f"✓ {inst.name} installed"
                if skipped:
                    msg += f" ({len(skipped)} files must be downloaded manually from CurseForge)"
                self.ui(self.toast, msg, GREEN if not skipped else AMBER)
                self.ui(self.refresh_all_instances)
            except Exception as e:
                self.log(f"Modpack install failed: {e}")
                self.ui(self.toast, f"Install failed: {e}", RED)
            finally:
                self.busy_pack = False
        self.bg(work)

    def install_addons(self, names):
        """Install catalog addons in parallel (Modrinth first, CurseForge fallback)."""
        if self.busy_addons:
            return self.toast("Addon install already running...", AMBER)
        inst = self.inst
        todo = [n for n in names if not inst.has_addon(n)]
        if not todo:
            return self.toast("✓ Everything is already installed", GREEN)
        self.busy_addons = True
        self.toast(f"Installing {len(todo)} addon(s) in parallel...")

        def work():
            seen, done, last = B.Seen(), [], [0.0]

            def on_done(name, info, err):
                if not info:
                    return
                inst.addons[name] = info
                done.append(name)
                self.ui(self.toast, f"Installed {len(done)}/{len(todo)}: {name}")
                if time.time() - last[0] > 0.7:         # throttle UI refresh
                    last[0] = time.time()
                    self.ui(self.refresh_addon_views)
            jobs = [(n, lambda n=n: self.store.install_addon(n, ADDON_MAP[n][1], inst, seen)) for n in todo]
            results = B.run_parallel(jobs, min(12, int(self.cfg.get("max_connections", 16))), on_done)
            self.mgr.save()
            failed = [n for n, (info, err) in results.items() if not info]
            self.busy_addons = False
            msg = f"✓ {len(names) - len(failed)}/{len(names)} addons ready"
            if failed:
                msg += f" • not available for {inst.mc} {inst.loader.title()}: {', '.join(failed)}"
            self.log(msg)
            self.ui(self.toast, msg, GREEN if not failed else AMBER)
            self.ui(self.refresh_addon_views)
        self.bg(work)

    def install_item(self, item, on_done=None):
        """Install one online search result (mod / resource pack / shader) from Modrinth or CurseForge."""
        inst = self.inst
        self.toast(f"Installing {item['title']}...")

        def work():
            try:
                info = self.store.install(item, inst, lambda s: None, B.Seen())
                if info:
                    inst.addons[item["title"]] = info
                    self.mgr.save()
                    self.log(f"Installed {item['title']} ({item['source']})")
                    self.ui(self.toast, f"✓ {item['title']} installed", GREEN)
                else:
                    self.ui(self.toast, f"No compatible file of {item['title']} for {inst.mc}", AMBER)
            except B.ManualDownload:
                self.ui(self.toast, f"{item['title']}: the author blocks third-party downloads - opening its page", AMBER)
                webbrowser.open(item.get("url", "https://www.curseforge.com/minecraft"))
            except Exception as e:
                self.log(f"Install failed: {e}")
                self.ui(self.toast, f"Install failed: {e}", RED)
            self.ui(self.refresh_addon_views)
            if on_done:
                self.ui(on_done)
        self.bg(work)

    def run_action(self, action):
        if action == "scan":
            self.run_scan()
        elif action == "essentials":
            self.install_addons(ESSENTIALS)

    def run_diagnostics(self):
        self.show("Agent (AI)")
        self.run_scan()

    def run_scan(self):
        self.say_all("Scanning your instance...")

        def work():
            results = self.agent.scan(self.inst)
            icons = {"ok": "✓", "fix": "🛠", "warn": "⚠"}
            text = "\n".join(f"{icons[lvl]} {msg}" for lvl, msg in results)
            fixed = sum(lvl == "fix" for lvl, _ in results)
            self.log(f"Scan finished: {fixed} issue(s) fixed")
            self.ui(self.say_all, text)
            self.ui(self.refresh_addon_views)
        self.bg(work)


if __name__ == "__main__":
    App().mainloop()
