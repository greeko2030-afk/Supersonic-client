"""Supersonic Client v2.5.0 - UI (CustomTkinter). Run: python main.py"""
import hashlib
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

ctk.set_appearance_mode("Dark")
ASSETS = Path(__file__).parent / "assets"   # optional: logo.png, agent.png

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
    ("Krypton", "krypton", "Performance", "Optimizes the network stack."),
    ("C2ME", "c2me-fabric", "Performance", "Faster chunk loading."),
    ("Continuity", "continuity", "Visuals", "Connected textures support."),
    ("LambDynamicLights", "lambdynamiclights", "Visuals", "Dynamic lighting from items."),
    ("Reese's Sodium Options", "reeses-sodium-options", "Visuals", "Better video settings screen."),
    ("JEI (Just Enough Items)", "jei", "Gameplay", "View items and recipes easily."),
    ("JourneyMap", "journeymap", "Gameplay", "Real-time mapping in your world."),
    ("Xaero's Minimap", "xaeros-minimap", "Gameplay", "Minimap with waypoints."),
    ("Xaero's World Map", "xaeros-world-map", "Gameplay", "Full world map screen."),
    ("Mod Menu", "modmenu", "Utility", "Add a mod menu to the game."),
    ("AppleSkin", "appleskin", "Utility", "Food stats HUD improvements."),
    ("Mouse Tweaks", "mouse-tweaks", "Utility", "Inventory management."),
    ("Inventory Profiles Next", "inventory-profiles-next", "Utility", "Sort and organize inventory."),
    ("Terralith", "terralith", "World Gen", "Overhauled terrain generation."),
    ("Tectonic", "tectonic", "World Gen", "Dramatic terrain shapes."),
    ("Cloth Config API", "cloth-config", "Libraries", "Config library for many mods."),
    ("Fabric API", "fabric-api", "Libraries", "Core Fabric modding library."),
    ("Architectury API", "architectury-api", "Libraries", "Cross-loader mod library."),
]
ADDON_MAP = {a[0]: a for a in ADDONS}
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


def make_logo(px):
    path = ASSETS / "logo.png"
    if path.exists():
        return Image.open(path).convert("RGBA").resize((px, px), Image.LANCZOS)
    s = px * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((s * .04, s * .04, s * .96, s * .96), outline=(56, 189, 248, 255), width=max(2, s // 28))
    bolt = [(.56, .10), (.24, .55), (.46, .55), (.38, .90), (.76, .42), (.52, .42)]
    d.polygon([(x * s, y * s) for x, y in bolt], fill=(37, 99, 235, 255), outline=(125, 211, 252, 255))
    return im.resize((px, px), Image.LANCZOS)


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
    button(c, "⬇  Install", lambda: app.install_pack(pack), height=30 if full else 26,
           font=F(12, "bold")).pack(fill="x", padx=10, pady=10, side="bottom")
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
            self.configure(width=310)
            self.pack_propagate(False)
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 0))
        label(head, "AGENT (AI)", 15, "bold").pack(side="left")
        label(head, " BETA ", 9, "bold", "white", fg_color=BLUE, corner_radius=5).pack(side="left", padx=8)
        label(self, "Your personal AI assistant", 11, color=MUTED).pack(anchor="w", padx=16)
        bot = label(self, "🤖", 54, width=120, height=90)
        bot.pack(pady=(4, 0))
        if (ASSETS / "agent.png").exists():
            img = ctk.CTkImage(Image.open(ASSETS / "agent.png"), size=(110, 110))
            bot.configure(image=img, text="")
        label(self, "●  Agent Online", 12, color=GREEN).pack(anchor="w", padx=16, pady=(2, 6))
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
        hero = card(parent, corner_radius=14, height=190)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        label(hero, "SUPERSONIC CLIENT", 34, "bold").place(x=28, y=20)
        hero.winfo_children()[0].configure(font=F(34, "bold", True))
        label(hero, "Hyper optimized. Ultra fast. Future ready.", 15, color=TXT).place(x=30, y=72)
        logo = label(hero, "", image=ctk.CTkImage(make_logo(256), size=(170, 170)))
        logo.place(relx=.62, rely=.5, anchor="center")
        chips = ctk.CTkFrame(hero, fg_color="transparent")
        chips.place(x=28, y=130)
        self.chip_mc = label(chips, "", 12, fg_color=CARD2, corner_radius=8, height=34)
        self.chip_perf = label(chips, "", 12, fg_color=CARD2, corner_radius=8, height=34)
        self.chip_last = label(chips, "", 12, fg_color=CARD2, corner_radius=8, height=34)
        for c in (self.chip_mc, self.chip_perf, self.chip_last):
            c.pack(side="left", padx=(0, 8))
        self.play_btn = button(hero, "▶  PLAY", self.app.launch_game, width=230, height=60, font=F(24, "bold"))
        self.play_btn.place(relx=1, x=-26, y=20, anchor="ne")
        self.inst_var = ctk.StringVar()
        self.inst_menu = menu(hero, [""], self.inst_var, self.select_instance, width=230)
        self.inst_menu.configure(height=34)
        self.inst_menu.place(relx=1, x=-26, y=92, anchor="ne")
        self.status = label(hero, "Ready to launch", 11, "bold", GREEN)
        self.status.place(relx=1, x=-26, y=134, anchor="ne")
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
            label(c, desc.split(".")[0][:22], 10, color=MUTED, anchor="w").place(x=56, y=28)
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
        names = [i.name for i in self.app.mgr.items]
        self.inst_menu.configure(values=names)
        self.inst_var.set(self.app.inst.name)
        self.refresh_chips()
        self.refresh_addons()
        if not self.packs_loaded:
            self.packs_loaded = True
            self.app.bg(self.load_packs)
        self.after(400, self.tick)

    def refresh_instances(self):
        self.on_show()

    def select_instance(self, name):
        self.app.cfg.set("selected_instance", name)
        self.refresh_chips()
        self.app.refresh_addon_views()
        self.app.warm_instance()

    def refresh_chips(self):
        inst = self.app.inst
        self.chip_mc.configure(text=f"  ⛏  Minecraft {inst.mc} • {inst.loader.title()}  ")
        self.chip_perf.configure(text=f"  🚀  Performance: {self.app.cfg.get('perf_mode').split()[0]}  ")
        last = time.strftime("%b %d, %H:%M", time.localtime(inst.last_played)) if inst.last_played else "Never"
        self.chip_last.configure(text=f"  🕒  Last Played: {last}  ")

    def refresh_addons(self):
        inst = self.app.inst
        for name, st in self.mini.items():
            ok = inst.has_addon(name)
            st.configure(text="✓ Installed" if ok else "Click to install", text_color=GREEN if ok else MUTED)

    def set_status(self, text, color=GREEN):
        self.status.configure(text=text[:42], text_color=color)

    def load_packs(self):
        try:
            packs, _ = self.app.mr.search(sort="downloads", limit=6)
        except Exception as e:
            self.app.ui(self.set_status, f"Modrinth offline: {e}", AMBER)
            self.packs_loaded = False
            return
        self.app.ui(self.render_packs, packs)

    def render_packs(self, packs):
        for w in self.pack_row.winfo_children():
            w.destroy()
        for i, p in enumerate(packs):
            self.pack_row.grid_columnconfigure(i, weight=1, uniform="p")
            make_pack_card(self.pack_row, self.app, p, full=False).grid(row=0, column=i, sticky="nsew", padx=4)

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
        self.grid_host = ctk.CTkFrame(main, fg_color="transparent")
        self.grid_host.grid(row=3, column=0, sticky="nsew")
        for c in range(4):
            self.grid_host.grid_columnconfigure(c, weight=1, uniform="c")
        self.pager = ctk.CTkFrame(main, fg_color="transparent")
        self.pager.grid(row=4, column=0, pady=8)
        self.footer = card(main, corner_radius=10)
        self.footer.grid(row=5, column=0, sticky="ew")
        self.foot_labels = []
        for i, title in enumerate(("Total Modpacks", "Installed", "Total Downloads", "Storage Used", "Auto Update")):
            self.footer.grid_columnconfigure(i, weight=1, uniform="f")
            box = ctk.CTkFrame(self.footer, fg_color="transparent")
            box.grid(row=0, column=i, pady=8)
            label(box, title, 11, color=MUTED).pack()
            v = label(box, "-", 14, "bold")
            v.pack()
            self.foot_labels.append(v)
        self.build_side()

    def build_side(self):
        side = ctk.CTkFrame(self, fg_color="transparent", width=290)
        side.grid(row=0, column=1, sticky="ns")
        self.search = ctk.CTkEntry(side, placeholder_text="Search modpacks...", height=38, width=290)
        self.search.pack()
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
        ctk.CTkFrame(f, height=8, fg_color="transparent").pack()
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
        self.up_title = label(self.uptodate, "", 13, "bold", GREEN)
        self.up_title.pack(anchor="w", padx=14, pady=(12, 0))
        self.up_sub = label(self.uptodate, "", 11, color=MUTED)
        self.up_sub.pack(anchor="w", padx=14, pady=(0, 12))
        cats = card(side, width=300)
        cats.pack(fill="x")
        row = ctk.CTkFrame(cats, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=10)
        self.search = ctk.CTkEntry(row, placeholder_text="Search addons... (Enter = search online)", height=34)
        self.search.pack(fill="x")
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
        self.info_desc = label(info, "", 11, color=MUTED, anchor="w", justify="left", wraplength=265)
        self.info_desc.pack(anchor="w", padx=14, pady=6)
        self.info_rows = {}
        for key in ("Status", "Version", "Minecraft", "Author"):
            r = ctk.CTkFrame(info, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=1)
            label(r, key, 11, color=MUTED).pack(side="left")
            v = label(r, "-", 11)
            v.pack(side="left", padx=24)
            self.info_rows[key] = v
        ctk.CTkFrame(info, height=10, fg_color="transparent").pack()
        agent = card(side, width=300, fg_color="#0A1A3A")
        agent.pack(fill="x")
        label(agent, "🤖", 30).pack(side="left", padx=12, pady=10)
        label(agent, "Powered by Supersonic Agent (AI)\nWe automatically select and update the best addons for your system.",
              11, color=CYAN, justify="left", wraplength=210, anchor="w").pack(side="left", pady=10)

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
            self.up_title.configure(text="All addons are installed!", text_color=GREEN)
            self.up_sub.configure(text="Your client is fully optimized.")
        else:
            self.up_title.configure(text=f"{len(ADDONS) - done} addons not installed", text_color=AMBER)
            self.up_sub.configure(text="Press Install All to optimize your client.")
        for w in self.cat_box.winfo_children():
            w.destroy()
        for name in ["All Categories"] + ADDON_TABS[1:]:
            n = len(ADDONS) if name == "All Categories" else sum(a[2] == name for a in ADDONS)
            on = (name == "All Categories" and self.tab == "All Addons") or name == self.tab
            ctk.CTkButton(self.cat_box, text=f"{name}{' ' * 4}{n}", anchor="w", height=28, font=F(12),
                          fg_color="#10234A" if on else "transparent", hover_color=CARD2,
                          text_color=TXT if on else MUTED,
                          command=lambda t=name: self.on_tab("All Addons" if t == "All Categories" else t)).pack(fill="x")
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
        for i, a in enumerate(self.visible()):
            self.make_card(a).grid(row=i // cols, column=i % cols, sticky="ew", padx=4, pady=4)

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
        label(self.perf, "Performance Summary (estimated from installed addons)", 13, "bold").pack(anchor="w", padx=14, pady=(8, 2))
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
    def __init__(self, parent, app):
        super().__init__(parent, app)
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
        TabBar(main, ["General", "Performance", "Minecraft", "Launcher", "Updates", "Privacy", "Advanced"],
               lambda t: None).grid(row=1, column=0, sticky="w", pady=(8, 6))
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
                 ["Auto", "Java 8", "Java 17", "Java 21"], {}),
                ("Minecraft Folder", "Change the .minecraft directory.", "button", "Open Folder",
                 lambda: B.open_path(B.MC_ROOT), {}),
                ("Automatically Install Java", "Install recommended Java if missing.", "switch", "auto_java", None, {}),
                ("Use Native Libraries", "Use native libraries for better performance.", "switch", "native_libs", None, {}),
                ("Keep Launcher Open", "Keep launcher open while Minecraft is running.", "switch", "keep_launcher_open", None, {})]),
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
                ("Metadata Sources", "CurseForge API key.", "button", "Configure", self.cf_key, {}),
                ("Verify Downloads", "Verify files after download.", "switch", "verify_downloads", None, {}),
                ("Delete Temp Files", "Automatically delete temporary files.", "menu", "delete_temp", ["Always", "Never"], {})]),
            ("BACKUP & SYNC", [
                ("Enable Cloud Sync", "Sync instances and settings.", "switch", "cloud_sync", None, {}),
                ("Sync Across Devices", "Keep data synced across devices.", "switch", "sync_devices", None, {}),
                ("Backup Instances", "Backup the selected instance.", "button", "Manage", self.backup, {}),
                ("Restore from Backup", "Restore an instance from a backup zip.", "button", "Restore", self.restore, {})]),
        ]
        for i, (title, rows) in enumerate(sections):
            c = card(scroll)
            c.grid(row=i // 3, column=i % 3, sticky="nsew", padx=5, pady=5)
            label(c, title, 12, "bold").pack(anchor="w", padx=16, pady=(14, 4))
            for r in rows:
                self.row(c, *r)
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
            menu(r, values, var, lambda v: cfg.set(key, conv(v)), 120).pack(side="right")
        elif kind == "switch":
            var = ctk.BooleanVar(value=bool(cfg.get(key)))
            ctk.CTkSwitch(r, text="", width=44, variable=var, progress_color=BLUE,
                          command=lambda: cfg.set(key, var.get())).pack(side="right")
        else:
            button(r, key, values, primary=False, width=90, height=28, font=F(12)).pack(side="right")

    def build_side(self):
        side = ctk.CTkFrame(self, fg_color="transparent", width=300)
        side.grid(row=0, column=1, sticky="ns")
        sysbox = card(side, width=300)
        sysbox.pack(fill="x")
        label(sysbox, "SYSTEM OVERVIEW", 12, "bold").pack(anchor="w", padx=14, pady=(12, 6))
        self.sys_labels = {}
        for key, icon in (("OS", "🪟"), ("CPU", "🧠"), ("RAM", "🧮"), ("GPU", "🎮"), ("Storage", "💾")):
            r = ctk.CTkFrame(sysbox, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=3)
            label(r, f"{icon}  {key}", 12).pack(side="left")
            v = label(r, "...", 11, color=MUTED, wraplength=150, anchor="e", justify="right")
            v.pack(side="right")
            self.sys_labels[key] = v
        button(sysbox, "〰  Run Diagnostics", self.app.run_diagnostics, primary=False).pack(fill="x", padx=14, pady=12)
        quick = card(side, width=300)
        quick.pack(fill="x", pady=8)
        label(quick, "AGENT (AI) QUICK ACTIONS", 12, "bold").pack(anchor="w", padx=14, pady=(12, 6))
        for title, sub, act in (("Auto Fix Errors", "Detect and fix issues.", "scan"),
                                ("Optimize Performance", "Improve FPS & stability.", "essentials"),
                                ("Clean Junk Files", "Free up storage space.", "clean"),
                                ("Reset Configurations", "Reset settings to optimal.", "reset")):
            b = ctk.CTkButton(quick, text=f"{title}\n{sub}", anchor="w", height=46, fg_color=CARD2, hover_color=BORDER,
                              font=F(12), command=lambda a=act: self.quick(a))
            b.pack(fill="x", padx=12, pady=3)
        button(quick, "🤖  Open Agent (AI)", lambda: self.app.show("Agent (AI)"), primary=False, height=40).pack(
            fill="x", padx=12, pady=10)
        about = card(side, width=300)
        about.pack(fill="x")
        label(about, "ABOUT", 12, "bold").pack(anchor="w", padx=14, pady=(12, 4))
        label(about, "Supersonic Client v2.5.0", 13, "bold").pack(anchor="w", padx=14)
        label(about, "The next generation Minecraft launcher.", 11, color=MUTED).pack(anchor="w", padx=14, pady=(0, 14))

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
NAV = [("Dashboard", "🏠"), ("Modpacks", "📦"), ("Addons", "🧩"), ("Instances", "🧊"), ("Servers", "🗄"),
       ("Resource Packs", "🖼"), ("Worlds", "🌍"), ("Settings", "⚙"), ("Agent (AI)", "🤖")]
BADGES = {"Addons": ("NEW", PURPLE), "Agent (AI)": ("AI", GREEN)}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = B.Config()
        self.mgr = B.InstanceManager()
        self.launcher = B.Launcher(self.cfg)
        self.mr, self.cf = B.Modrinth(), B.CurseForge(self.cfg)
        self.packs = B.PackInstaller(self.cfg, self.mgr, self.cf)
        self.store = B.Store(self.mr, self.cf)
        self.agent = B.Agent(self.cfg)
        self.images = ImageStore(self)
        self.logs, self.panels, self.icon_urls, self.icon_waiters = [], [], {}, []
        self.running = self.busy_addons = self.busy_pack = False
        self._toast_id = None
        self.title("Supersonic Client v2.5.0")
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

    # -- threading helpers --
    def ui(self, fn, *args):
        self.after(0, lambda: fn(*args))

    def bg(self, fn, *args):
        threading.Thread(target=fn, args=args, daemon=True).start()

    # -- shell --
    def build_header(self):
        bar = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=64)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        bar.pack_propagate(False)
        logo = ctk.CTkImage(make_logo(128), size=(44, 44))
        label(bar, "", image=logo).pack(side="left", padx=(18, 10))
        label(bar, "SUPERSONIC", 20, "bold").pack(side="left")
        bar.winfo_children()[-1].configure(font=F(20, "bold", True))
        label(bar, "  v2.5.0", 12, color=MUTED).pack(side="left", pady=(6, 0))
        tag = "   ".join(" ".join(w) for w in "THE NEXT GENERATION MINECRAFT LAUNCHER".split())
        label(bar, tag, 12, "bold", CYAN).place(relx=.5, rely=.5, anchor="center")

    def build_sidebar(self):
        side = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, width=240)
        side.grid(row=1, column=0, sticky="ns")
        side.pack_propagate(False)
        self.nav = {}
        for name, icon in NAV:
            row = ctk.CTkFrame(side, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            btn = ctk.CTkButton(row, text=f"  {icon}   {name}", anchor="w", height=42, corner_radius=10,
                                fg_color="transparent", hover_color=CARD2, text_color=MUTED, border_color=BLUE,
                                font=F(14), command=lambda n=name: self.show(n))
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
        label(t, "👑 Premium", 11, "bold", AMBER, anchor="w").pack(anchor="w")
        for w in (acc, self.avatar, t, self.acc_name):
            w.bind("<Button-1>", lambda e: self.edit_username())
        self.update_account()
        links = ctk.CTkFrame(bottom, fg_color="transparent")
        links.pack(pady=(10, 0))
        for text, key in (("🌐 Website", "website_url"), ("💬 Discord", "discord_url"), ("🐙 GitHub", "github_url")):
            ctk.CTkButton(links, text=text, width=60, height=24, fg_color="transparent", hover=False, text_color=MUTED,
                          font=F(11), command=lambda k=key: webbrowser.open(self.cfg.get(k))).pack(side="left")

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
        for key, btn in self.nav.items():
            on = key == name
            btn.configure(fg_color="#0F2349" if on else "transparent", text_color=TXT if on else MUTED,
                          border_width=1 if on else 0)
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
    def launch_game(self, server=None):
        if self.running:
            return
        dash = self.pages["Dashboard"]
        inst = self.inst
        self.running = True
        dash.play_btn.configure(state="disabled", text="LAUNCHING...")
        dash.progress.place(relx=1, x=-26, y=162, anchor="ne")

        def work():
            try:
                proc = self.launcher.launch(inst, lambda s: self.ui(dash.set_status, s, CYAN),
                                            lambda f: self.ui(dash.progress.set, f), server)
                inst.last_played = time.time()
                self.mgr.save()
                self.ui(dash.set_status, "Game is running!", GREEN)
                self.log(f"Launched {inst.name} ({inst.mc})")
                hide = not self.cfg.get("keep_launcher_open")
                if hide:
                    self.ui(self.withdraw)
                started = time.time()
                proc.wait()
                if hide:
                    self.ui(self.deiconify)
                if proc.returncode and time.time() - started < 25:
                    self.launcher.invalidate(inst)      # next PLAY re-verifies game files once
                if proc.returncode:
                    self.log(f"Game exited with code {proc.returncode}")
                    self.ui(self.toast, "Game crashed - open Agent (AI) and press Scan & Fix", AMBER)
            except Exception as e:
                self.ui(dash.set_status, f"Error: {e}", RED)
                self.log(f"Launch failed: {e}")
            finally:
                self.ui(self.launch_done)
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
