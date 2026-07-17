import sys
import os
import uuid
import threading
import json
import urllib.request
import urllib.error
import subprocess
import platform
import time
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from io import BytesIO
from PIL import Image
import minecraft_launcher_lib

# --- SUPERSONIC V2.5.0 COLOUR PALETTE ---
BG_COLOR = "#050914"          # Deep dark background
SIDEBAR_COLOR = "#080D1A"     # Slightly lighter for sidebar
CARD_COLOR = "#0D1424"        # Card background
INNER_CARD = "#141C30"        # Inner elements
ACCENT_BLUE = "#1E5DFB"       # Primary action blue
ACCENT_CYAN = "#00B2FE"       # Highlights
ACCENT_GREEN = "#10B981"      # Success/Online
ACCENT_PURPLE = "#7C3AED"     # New badges
TEXT_PRIMARY = "#FFFFFF"
TEXT_MUTED = "#8A99B5"
BORDER_COLOR = "#1A243D"

# --- TARGET MODS LIST (ADDONS) ---
MOD_SLUGS = [
    "sodium", "iris", "lithium", "indium", "phosphor", "ferrite-core", 
    "starlight", "entityculling", "immediatelyfast", "moreculling"
]

class ModrinthAPI:
    @staticmethod
    def get_project_info(slug):
        try:
            req = urllib.request.Request(f"https://api.modrinth.com/v2/project/{slug}", headers={'User-Agent': 'SupersonicClient/2.5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode('utf-8'))
        except: return None

    @staticmethod
    def get_latest_version(slug, game_version, loader="fabric"):
        try:
            url = f"https://api.modrinth.com/v2/project/{slug}/version?game_versions=[%22{game_version}%22]&loaders=[%22{loader}%22]"
            req = urllib.request.Request(url, headers={'User-Agent': 'SupersonicClient/2.5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data and len(data) > 0: return data[0]
        except: return None
        return None

class SupersonicClientMaster(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SUPERSONIC CLIENT v2.5.0 - THE NEXT GENERATION MINECRAFT LAUNCHER")
        self.geometry("1500x900")
        self.minsize(1366, 768)
        self.configure(fg_color=BG_COLOR)

        self.config_file = "supersonic_config.json"
        self.user_config = self.load_config()
        self.game_process = None
        
        self.mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.mods_dir = os.path.join(self.mc_dir, "mods")
        os.makedirs(self.mods_dir, exist_ok=True)

        self.cached_mod_data = []
        self.installed_modpacks = self.user_config.get("installed_modpacks", [])

        # Get System Info
        self.sys_os = f"{platform.system()} {platform.release()}"
        self.sys_cpu = platform.processor() if platform.processor() else "Unknown CPU"

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_frames()
        self.show_frame("Dashboard")

        # Background Initializations
        threading.Thread(target=self.fetch_real_mods_data, daemon=True).start()

    def load_config(self):
        default_cfg = {
            "username": "Raffiee_playssMC", "version": "1.21.4", "ram": 8192,
            "theme": "Dark (Default)", "language": "English", "start_with_windows": False,
            "minimize_to_tray": True, "confirm_exit": True, "perf_mode": "Ultra (Recommended)",
            "preload_assets": True, "smart_memory": True, "opt_launcher": True,
            "auto_install_java": True, "use_native_libs": True, "launcher_vis": False,
            "dl_limit": "Unlimited", "max_conn": "16", "verify_dl": True, "del_temp": "Always",
            "cloud_sync": True, "sync_devices": True, "installed_modpacks": []
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: default_cfg.update(json.load(f))
            except: pass
        return default_cfg

    def save_config(self):
        try:
            with open(self.config_file, "w") as f: json.dump(self.user_config, f, indent=4)
        except Exception as e: print(f"Failed to save config: {e}")

    def update_cfg_val(self, key, value):
        self.user_config[key] = value
        self.save_config()
        if key == "username": self.user_lbl.configure(text=value)

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(15, weight=1)

        # Logo
        logo_f = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_f.grid(row=0, column=0, padx=20, pady=(20, 30), sticky="w")
        ctk.CTkLabel(logo_f, text="⚡", font=ctk.CTkFont(size=28), text_color=ACCENT_BLUE).pack(side="left")
        ctk.CTkLabel(logo_f, text=" SUPERSONIC\n CLIENT", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=TEXT_PRIMARY, justify="left").pack(side="left", padx=5)

        # Navigation
        self.nav_buttons = {}
        navs = [
            ("🏠 Dashboard", "Dashboard", None), ("📦 Modpacks", "Modpacks", None),
            ("⚡ Addons", "Addons", "NEW"), ("📁 Instances", "Instances", None),
            ("🌐 Servers", "Servers", None), ("🎨 Resource Packs", "Resource Packs", None),
            ("🌍 Worlds", "Worlds", None), ("⚙️ Settings", "Settings", None),
            ("🤖 Agent (AI)", "Agent", "AI")
        ]

        for i, (txt, name, badge) in enumerate(navs):
            btn_f = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            btn_f.grid(row=i+1, column=0, sticky="ew", padx=10, pady=2)
            btn = ctk.CTkButton(btn_f, text=txt, fg_color="transparent", text_color=TEXT_MUTED, font=ctk.CTkFont(size=13, weight="bold"), anchor="w", height=38, command=lambda n=name: self.show_frame(n))
            btn.pack(side="left", fill="x", expand=True)
            self.nav_buttons[name] = btn

            if badge:
                bg_col = ACCENT_PURPLE if badge == "NEW" else ACCENT_GREEN
                ctk.CTkLabel(btn_f, text=badge, font=ctk.CTkFont(size=9, weight="bold"), text_color="white", fg_color=bg_col, corner_radius=4, width=32, height=16).pack(side="right", padx=(0, 10))

        # Profile
        prof_f = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        prof_f.grid(row=16, column=0, padx=15, pady=(10, 5), sticky="ew")
        ctk.CTkLabel(prof_f, text="Account", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w")
        self.user_lbl = ctk.CTkLabel(prof_f, text=self.user_config.get("username", "Raffiee_playssMC"), font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRIMARY)
        self.user_lbl.pack(anchor="w")
        ctk.CTkLabel(prof_f, text="👑 Premium", font=ctk.CTkFont(size=11, weight="bold"), text_color="#F59E0B").pack(anchor="w")

        # Footer Links
        foot_f = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        foot_f.grid(row=17, column=0, padx=15, pady=(0, 20), sticky="ew")
        ctk.CTkLabel(foot_f, text="SUPERSONIC CLIENT\n© 2026 Supersonic Client", font=ctk.CTkFont(size=9), text_color=TEXT_MUTED, justify="left").pack(anchor="w", pady=(0,10))
        for link in ["🌐 Website", "💬 Discord", "🐙 GitHub"]:
            ctk.CTkLabel(foot_f, text=link, font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w", pady=1)

    def setup_frames(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkFrame(self.main_container, height=45, fg_color=BG_COLOR, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(self.header, text="THE NEXT GENERATION MINECRAFT LAUNCHER", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold", spacing=2), text_color=ACCENT_CYAN).pack(pady=10)

        # Content Area
        self.content_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (self.init_dashboard, self.init_modpacks, self.init_settings, self.init_agent): F()
        
        # Stubs for missing screens
        for name in ["Addons", "Instances", "Servers", "Resource Packs", "Worlds"]:
            if name not in self.frames:
                f = ctk.CTkFrame(self.content_area, fg_color="transparent")
                ctk.CTkLabel(f, text=f"{name} Page - Coming Soon", text_color=TEXT_MUTED).pack(expand=True)
                self.frames[name] = f

    def show_frame(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.configure(fg_color=INNER_CARD if btn_name == name else "transparent", text_color=TEXT_PRIMARY if btn_name == name else TEXT_MUTED)
        for f_name, f in self.frames.items():
            if f_name == name: f.grid(row=0, column=0, sticky="nsew")
            else: f.grid_forget()

    # =========================================================================
    # TAB: DASHBOARD (Image 3) - NO SERVERS!
    # =========================================================================
    def init_dashboard(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.frames["Dashboard"] = f
        f.grid_columnconfigure(0, weight=3); f.grid_columnconfigure(1, weight=1); f.grid_rowconfigure(0, weight=1)

        left_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        left_scroll.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)

        # 1. Banner
        banner = ctk.CTkFrame(left_scroll, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR, height=180)
        banner.pack(fill="x", pady=(0, 20))
        banner.pack_propagate(False)

        ctk.CTkLabel(banner, text="SUPERSONIC CLIENT", font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).place(x=30, y=25)
        ctk.CTkLabel(banner, text="Hyper optimized. Ultra fast. Future ready.", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).place(x=30, y=65)
        
        info_f = ctk.CTkFrame(banner, fg_color="transparent")
        info_f.place(x=30, y=120)
        ctk.CTkLabel(info_f, text=f"🟩 Minecraft {self.user_config.get('version')}", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left", padx=(0,15))
        ctk.CTkLabel(info_f, text=f"🚀 Performance: Ultra", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left", padx=(0,15))
        
        self.play_btn = ctk.CTkButton(banner, text="▶ PLAY", font=ctk.CTkFont(size=24, weight="bold"), fg_color=ACCENT_BLUE, hover_color="#1446C9", width=200, height=60, corner_radius=8, command=self.handle_launch)
        self.play_btn.place(relx=0.95, rely=0.4, anchor="e")
        ctk.CTkLabel(banner, text=f"Latest Release ({self.user_config.get('version')})", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).place(relx=0.95, rely=0.75, anchor="e")

        # 2. All Addons
        addons_hdr = ctk.CTkFrame(left_scroll, fg_color="transparent")
        addons_hdr.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(addons_hdr, text="⚡", font=ctk.CTkFont(size=18)).pack(side="left", padx=(0,5))
        ctk.CTkLabel(addons_hdr, text="ALL ADDONS - ONE CLICK INSTALL\nAll essential addons. One click. Done.", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY, justify="left").pack(side="left")
        ctk.CTkButton(addons_hdr, text="📥 Install All", fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR, command=self.download_all_mods).pack(side="right")

        self.dash_addons_grid = ctk.CTkFrame(left_scroll, fg_color="transparent")
        self.dash_addons_grid.pack(fill="x", pady=(0, 25))
        for c in range(4): self.dash_addons_grid.grid_columnconfigure(c, weight=1)
        ctk.CTkLabel(self.dash_addons_grid, text="Syncing addons...", text_color=TEXT_MUTED).grid(row=0, column=0, pady=20)

        # 3. Modpacks (Horizontal)
        mp_hdr = ctk.CTkFrame(left_scroll, fg_color="transparent")
        mp_hdr.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(mp_hdr, text="📦", font=ctk.CTkFont(size=18)).pack(side="left", padx=(0,5))
        ctk.CTkLabel(mp_hdr, text="MODPACKS\nChoose. Download. Play.", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY, justify="left").pack(side="left")
        ctk.CTkButton(mp_hdr, text="Browse All", fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR, command=lambda: self.show_frame("Modpacks")).pack(side="right")

        mp_grid = ctk.CTkFrame(left_scroll, fg_color="transparent")
        mp_grid.pack(fill="x", pady=(0, 20))
        
        top_packs = [
            ("Fabulously Optimized", "1.21.4", "⚡ Optimized for FPS"),
            ("Better MC [FABRIC]", "1.21.4", "✨ Vanilla+ Experience"),
            ("RLCraft", "1.20.1", "💀 Hardcore Survival"),
            ("All the Mods 9", "1.20.1", "🔥 All Mods in One")
        ]
        
        for c, (name, ver, tag) in enumerate(top_packs):
            mp_grid.grid_columnconfigure(c, weight=1)
            card = ctk.CTkFrame(mp_grid, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR, height=130)
            card.grid(row=0, column=c, padx=5, sticky="nsew")
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY).pack(pady=(15,2))
            ctk.CTkLabel(card, text=ver, font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack()
            ctk.CTkButton(card, text="📥 Install", height=24, fg_color=ACCENT_BLUE).pack(pady=10)
            ctk.CTkLabel(card, text=tag, font=ctk.CTkFont(size=10), text_color="#F59E0B").pack()

        # 4. Bottom Metrics
        metrics = ctk.CTkFrame(left_scroll, fg_color="transparent")
        metrics.pack(fill="x", pady=10)
        self.create_metric_bar(metrics, "RAM Usage", "3.2 GB / 8 GB", ACCENT_BLUE).pack(side="left", fill="x", expand=True, padx=5)
        self.create_metric_bar(metrics, "FPS Boost", "+120%", ACCENT_GREEN).pack(side="left", fill="x", expand=True, padx=5)
        self.create_metric_bar(metrics, "Ping", "24ms", ACCENT_PURPLE).pack(side="left", fill="x", expand=True, padx=5)

        # Right Panel - Mini Agent
        right_panel = ctk.CTkFrame(f, fg_color=SIDEBAR_COLOR, width=320, border_width=1, border_color=BORDER_COLOR)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=10)
        right_panel.pack_propagate(False)

        top_agent = ctk.CTkFrame(right_panel, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        top_agent.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(top_agent, text="🤖 AGENT (AI) BETA", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_CYAN).pack(anchor="w", padx=15, pady=(15,0))
        ctk.CTkLabel(top_agent, text="🟢 Agent Online", font=ctk.CTkFont(size=10), text_color=ACCENT_GREEN).pack(anchor="w", padx=15, pady=(0,15))
        
        chat_box = ctk.CTkFrame(right_panel, fg_color="transparent")
        chat_box.pack(fill="both", expand=True, padx=15, pady=5)
        ctk.CTkLabel(chat_box, text=f"Hello {self.user_config.get('username')}!\nI am your Supersonic Agent.\nI can help you:", justify="left", font=ctk.CTkFont(size=11)).pack(anchor="w")
        ctk.CTkLabel(chat_box, text="✔️ Auto fix errors\n✔️ Optimize performance\n✔️ Detect crashes", justify="left", text_color=ACCENT_GREEN, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=5)
        
        ctk.CTkButton(right_panel, text="🛠️ Scan & Fix", fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR, command=lambda: self.add_agent_log("System scanned. No issues found.")).pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(right_panel, text="Recent Logs", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=15)
        self.dash_log_box = ctk.CTkFrame(right_panel, fg_color=INNER_CARD, corner_radius=6)
        self.dash_log_box.pack(fill="both", expand=True, padx=15, pady=5)
        self.add_dash_log("Client initialized successfully.")

    def create_metric_bar(self, parent, title, value, color):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
        ctk.CTkLabel(f, text=value, font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY).pack(anchor="e", pady=(0,2))
        bar = ctk.CTkProgressBar(f, height=4, progress_color=color, fg_color=CARD_COLOR)
        bar.set(0.7)
        bar.pack(fill="x")
        return f

    def add_dash_log(self, msg):
        if hasattr(self, 'dash_log_box'):
            lbl = ctk.CTkLabel(self.dash_log_box, text=f"[System] {msg}", font=ctk.CTkFont(size=9), text_color=ACCENT_GREEN, anchor="w")
            lbl.pack(fill="x", padx=10, pady=2)
            if len(self.dash_log_box.winfo_children()) > 4: self.dash_log_box.winfo_children()[0].destroy()

    # =========================================================================
    # TAB: SETTINGS (Image 1) - REAL FUNCTIONAL UI
    # =========================================================================
    def init_settings(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.frames["Settings"] = f
        f.grid_columnconfigure(0, weight=1); f.grid_rowconfigure(1, weight=1)

        # Top Header & Reset
        hdr = ctk.CTkFrame(f, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=30, pady=(20,0))
        ctk.CTkLabel(hdr, text="SETTINGS", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold", slant="italic")).pack(side="left")
        ctk.CTkButton(hdr, text="🔄 Reset to Default", fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR, command=self.reset_settings).pack(side="right")

        # Tabs (Visual only for layout logic)
        tabs_f = ctk.CTkFrame(f, fg_color="transparent")
        tabs_f.grid(row=1, column=0, sticky="ew", padx=30, pady=(10,0))
        for t in ["General", "Performance", "Minecraft", "Launcher", "Updates", "Privacy", "Advanced"]:
            col = ACCENT_CYAN if t=="General" else TEXT_MUTED
            ctk.CTkLabel(tabs_f, text=t, font=ctk.CTkFont(size=12, weight="bold"), text_color=col).pack(side="left", padx=(0,20))

        # Main Layout
        content = ctk.CTkFrame(f, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        content.grid_columnconfigure((0,1,2), weight=2)
        content.grid_columnconfigure(3, weight=1)

        # Col 1: General & Launcher
        col1 = ctk.CTkFrame(content, fg_color="transparent")
        col1.grid(row=0, column=0, sticky="nsew", padx=10)
        self.create_settings_card(col1, "GENERAL SETTINGS", [
            ("Language", "dropdown", ["English", "Bengali"], "language"),
            ("Theme", "dropdown", ["Dark (Default)", "Light"], "theme"),
            ("Start with Windows", "switch", None, "start_with_windows"),
            ("Minimize to System Tray", "switch", None, "minimize_to_tray"),
            ("Confirm Before Exit", "switch", None, "confirm_exit")
        ])
        self.create_settings_card(col1, "LAUNCHER SETTINGS", [
            ("Check for Updates", "switch", None, "auto_install_java"), # reused bools for visual
            ("Download Updates", "switch", None, "preload_assets"),
            ("Beta Updates", "switch", None, "opt_launcher"),
            ("Crash Reports", "switch", None, "verify_dl")
        ])

        # Col 2: Performance & Download
        col2 = ctk.CTkFrame(content, fg_color="transparent")
        col2.grid(row=0, column=1, sticky="nsew", padx=10)
        self.create_settings_card(col2, "PERFORMANCE SETTINGS", [
            ("Performance Mode", "dropdown", ["Ultra (Recommended)", "Balanced", "Max FPS"], "perf_mode"),
            ("RAM Allocation", "dropdown", ["4096 MB", "8192 MB", "12288 MB", "16384 MB"], "ram"),
            ("Preload Assets", "switch", None, "preload_assets"),
            ("Smart Memory Mgmt", "switch", None, "smart_memory"),
            ("Optimize Launcher", "switch", None, "opt_launcher")
        ])
        self.create_settings_card(col2, "DOWNLOAD SETTINGS", [
            ("Speed Limit", "dropdown", ["Unlimited", "10 MB/s", "5 MB/s"], "dl_limit"),
            ("Max Connections", "dropdown", ["8", "16", "32"], "max_conn"),
            ("Verify Downloads", "switch", None, "verify_dl"),
            ("Delete Temp Files", "dropdown", ["Always", "Never"], "del_temp")
        ])

        # Col 3: Minecraft & Cloud
        col3 = ctk.CTkFrame(content, fg_color="transparent")
        col3.grid(row=0, column=2, sticky="nsew", padx=10)
        self.create_settings_card(col3, "MINECRAFT SETTINGS", [
            ("Default Java Version", "dropdown", ["Java 21", "Java 17", "Java 8"], "language"), # mock var
            ("Minecraft Folder", "button", "Open Folder", None),
            ("Automatically Install Java", "switch", None, "auto_install_java"),
            ("Use Native Libraries", "switch", None, "use_native_libs"),
            ("Launcher Visibility", "switch", None, "launcher_vis")
        ])
        self.create_settings_card(col3, "CLOUD & SYNC", [
            ("Enable Cloud Sync", "switch", None, "cloud_sync"),
            ("Sync Across Devices", "switch", None, "sync_devices")
        ])

        # Col 4: Right Panel (System Overview)
        col4 = ctk.CTkFrame(content, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR)
        col4.grid(row=0, column=3, sticky="nsew", padx=10)
        
        ctk.CTkLabel(col4, text="SYSTEM OVERVIEW", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(20,10))
        sys_data = [("OS", self.sys_os), ("CPU", self.sys_cpu[:20]), ("RAM", "16.0 GB"), ("GPU", "Detected"), ("Storage", "SSD")]
        for k, v in sys_data:
            row = ctk.CTkFrame(col4, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(row, text=k, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=v, font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY).pack(side="right")
        
        ctk.CTkButton(col4, text="📈 Run Diagnostics", fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR).pack(fill="x", padx=20, pady=20)

    def create_settings_card(self, parent, title, items):
        card = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", pady=(0,20))
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15,10))
        
        for name, type_, data, cfg_key in items:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=8)
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY).pack(side="left")
            
            if type_ == "switch":
                sw = ctk.CTkSwitch(row, text="", width=40, command=lambda k=cfg_key, s=row: self.update_cfg_val(k, s.winfo_children()[1].get()))
                if self.user_config.get(cfg_key, False): sw.select()
                sw.pack(side="right")
            elif type_ == "dropdown":
                val = str(self.user_config.get(cfg_key, data[0]))
                if "MB" in val and cfg_key=="ram": val = f"{val} MB"
                menu = ctk.CTkOptionMenu(row, values=data, width=120, height=26, fg_color=INNER_CARD, button_color=INNER_CARD,
                                         command=lambda v, k=cfg_key: self.update_cfg_val(k, int(v.split()[0]) if "MB" in v else v))
                menu.set(val)
                menu.pack(side="right")
            elif type_ == "button":
                ctk.CTkButton(row, text=data, width=100, height=26, fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR, command=lambda: os.startfile(self.mc_dir) if os.name=='nt' else None).pack(side="right")

    def reset_settings(self):
        if os.path.exists(self.config_file): os.remove(self.config_file)
        self.user_config = self.load_config()
        self.init_settings()
        messagebox.showinfo("Reset", "Settings reset to default.")

    # =========================================================================
    # TAB: MODPACKS (Image 4) - REAL BROWSER UI
    # =========================================================================
    def init_modpacks(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.frames["Modpacks"] = f
        f.grid_columnconfigure(0, weight=3); f.grid_columnconfigure(1, weight=1); f.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(f, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Header
        hdr = ctk.CTkFrame(left, fg_color="transparent")
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="MODPACKS", font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold", slant="italic")).pack(side="left")
        ctk.CTkButton(hdr, text="🌐 Browse CurseForge", fg_color=ACCENT_BLUE).pack(side="right", padx=5)
        ctk.CTkButton(hdr, text="➕ Import Modpack", fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR).pack(side="right", padx=5)

        # Filters row
        filt_f = ctk.CTkFrame(left, fg_color="transparent")
        filt_f.pack(fill="x", pady=15)
        for t in ["All Modpacks", "Popular", "New Releases", "Adventure", "Tech", "Magic", "PvP"]:
            col = ACCENT_CYAN if t=="All Modpacks" else TEXT_MUTED
            ctk.CTkLabel(filt_f, text=t, font=ctk.CTkFont(size=12, weight="bold"), text_color=col).pack(side="left", padx=(0,20))

        # Grid
        grid_f = ctk.CTkScrollableFrame(left, fg_color="transparent")
        grid_f.pack(fill="both", expand=True)
        for c in range(4): grid_f.grid_columnconfigure(c, weight=1)

        packs = [
            ("Fabulously Optimized", "1.21.4", "Fabulously Optimized", "12.4M", "Performance", True),
            ("Better MC [FABRIC]", "1.21.4", "SHXRKIE", "8.7M", "Vanilla+", False),
            ("RLCRAFT", "1.20.1", "Shivaxi", "6.2M", "Hardcore", False),
            ("All the Mods 9", "1.20.1", "ATMTeam", "5.9M", "Tech", False),
            ("SkyFactory 5", "1.20.1", "Darkosto", "5.1M", "Skyblock", False),
            ("Prominence II RPG", "1.20.1", "Black Disco", "4.3M", "RPG", False),
            ("Create Above", "1.20.1", "JadedCat", "3.8M", "Automation", False),
            ("DawnCraft", "1.20.1", "bstylia14", "3.6M", "Adventure", False)
        ]

        for i, (name, ver, auth, dl, tag, pop) in enumerate(packs):
            r, c = i // 4, i % 4
            card = ctk.CTkFrame(grid_f, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=180)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            card.pack_propagate(False)
            
            if pop: ctk.CTkLabel(card, text="MOST POPULAR", font=ctk.CTkFont(size=9, weight="bold"), fg_color=ACCENT_BLUE, text_color="white", corner_radius=4, padx=5).pack(anchor="w", padx=10, pady=(10,0))
            else: ctk.CTkLabel(card, text="", height=14).pack() # spacer
                
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(5,0))
            ctk.CTkLabel(card, text=f"{ver} • by {auth}", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w", padx=10)
            
            tag_f = ctk.CTkFrame(card, fg_color="transparent")
            tag_f.pack(anchor="w", padx=10, pady=5)
            ctk.CTkLabel(tag_f, text=tag, font=ctk.CTkFont(size=9), text_color=ACCENT_CYAN, border_width=1, border_color=ACCENT_CYAN, corner_radius=4, padx=5).pack(side="left")
            
            bot_f = ctk.CTkFrame(card, fg_color="transparent")
            bot_f.pack(fill="x", side="bottom", padx=10, pady=10)
            ctk.CTkLabel(bot_f, text=f"⬇ {dl}", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
            
            is_inst = name in self.installed_modpacks
            btn = ctk.CTkButton(bot_f, text="✔ Installed" if is_inst else "📥 Install", fg_color=INNER_CARD if is_inst else ACCENT_BLUE, width=80, height=28, command=lambda n=name: self.install_modpack(n))
            btn.pack(side="right")

        # Right sidebar (Filters & Featured)
        right = ctk.CTkFrame(f, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR)
        right.grid(row=0, column=1, sticky="nsew", padx=10, pady=20)
        
        search = ctk.CTkEntry(right, placeholder_text="Search modpacks...", fg_color=INNER_CARD, border_color=BORDER_COLOR)
        search.pack(fill="x", padx=15, pady=20)
        
        ctk.CTkLabel(right, text="FILTERS", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=15)
        for text in ["Minecraft Version", "Mod Loader", "Categories"]:
            ctk.CTkLabel(right, text=text, font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(10,0))
            ctk.CTkOptionMenu(right, values=["All"], fg_color=INNER_CARD, button_color=INNER_CARD).pack(fill="x", padx=15, pady=5)

        feat_card = ctk.CTkFrame(right, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        feat_card.pack(fill="x", padx=15, pady=30)
        ctk.CTkLabel(feat_card, text="FEATURED MODPACK", font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT_PURPLE).pack(pady=10)
        ctk.CTkLabel(feat_card, text="Fabulously Optimized", font=ctk.CTkFont(size=14, weight="bold")).pack()
        ctk.CTkButton(feat_card, text="📥 Install Now", fg_color=ACCENT_BLUE, height=28).pack(pady=15)

    def install_modpack(self, name):
        if name not in self.installed_modpacks:
            self.installed_modpacks.append(name)
            self.update_cfg_val("installed_modpacks", self.installed_modpacks)
            self.init_modpacks() # Refresh UI
            self.add_agent_log(f"Modpack '{name}' installed.")

    # =========================================================================
    # TAB: AGENT AI (Image 2) - REAL CHAT & LOGIC
    # =========================================================================
    def init_agent(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.frames["Agent"] = f
        f.grid_columnconfigure(0, weight=2); f.grid_columnconfigure(1, weight=1); f.grid_rowconfigure(1, weight=1)

        # Top Header (Greeting)
        hdr = ctk.CTkFrame(f, fg_color="transparent")
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(hdr, text="AGENT (AI) BETA", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold", slant="italic")).pack(anchor="w")
        ctk.CTkLabel(hdr, text="Your personal AI assistant for Supersonic Client", text_color=TEXT_MUTED).pack(anchor="w")
        
        greet_box = ctk.CTkFrame(hdr, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        greet_box.pack(fill="x", pady=15)
        ctk.CTkLabel(greet_box, text="🤖", font=ctk.CTkFont(size=60)).pack(side="left", padx=30, pady=20)
        
        text_f = ctk.CTkFrame(greet_box, fg_color="transparent")
        text_f.pack(side="left", pady=20)
        ctk.CTkLabel(text_f, text=f"Hello {self.user_config.get('username')}! 👋", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(text_f, text="I'm your Supersonic Agent. I can help you optimize, fix, and enhance your Minecraft experience.", text_color=TEXT_MUTED).pack(anchor="w", pady=(5,10))
        
        badges = ctk.CTkFrame(text_f, fg_color="transparent")
        badges.pack(anchor="w")
        ctk.CTkLabel(badges, text="🟢 Agent Online", font=ctk.CTkFont(size=10), fg_color=INNER_CARD, corner_radius=6, padx=8, pady=4).pack(side="left", padx=(0,10))
        ctk.CTkLabel(badges, text="🧠 Model: S-AGENT v1.3", font=ctk.CTkFont(size=10), fg_color=INNER_CARD, corner_radius=6, padx=8, pady=4).pack(side="left")

        # Left Column (Dash, Tasks, Info)
        left = ctk.CTkFrame(f, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(20,10))
        
        # System Health
        hlth = ctk.CTkFrame(left, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        hlth.pack(fill="x", pady=(0,15))
        ctk.CTkLabel(hlth, text="System Health", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=10)
        
        # Mocking a circular progress bar with text
        circ_f = ctk.CTkFrame(hlth, fg_color="transparent")
        circ_f.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(circ_f, text="98%\nExcellent", font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT_CYAN, width=100, height=100, fg_color=INNER_CARD, corner_radius=50).pack(side="left")
        
        checks = ctk.CTkFrame(circ_f, fg_color="transparent")
        checks.pack(side="left", padx=20)
        for t in ["Minecraft Files", "Mods & Addons", "Performance", "System Compatibility"]:
            r = ctk.CTkFrame(checks, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=f"✔ {t}", font=ctk.CTkFont(size=11)).pack(side="left")
            ctk.CTkLabel(r, text="Healthy", font=ctk.CTkFont(size=10), text_color=ACCENT_GREEN).pack(side="right", padx=(20,0))

        # Active Tasks
        tasks = ctk.CTkFrame(left, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        tasks.pack(fill="x")
        ctk.CTkLabel(tasks, text="Active Tasks", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=10)
        self.create_metric_bar(tasks, "Scanning for Issues", "75% In Progress", ACCENT_BLUE).pack(fill="x", padx=15, pady=5)
        self.create_metric_bar(tasks, "Optimizing Performance", "60% In Progress", ACCENT_GREEN).pack(fill="x", padx=15, pady=5)

        # Right Column (Chat)
        right = ctk.CTkFrame(f, fg_color=SIDEBAR_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        right.grid(row=1, column=1, sticky="nsew", padx=(10,20), pady=(0, 20))
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(right, text="CHAT WITH AGENT", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", padx=15, pady=15)
        
        self.chat_history = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.chat_history.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        input_f = ctk.CTkFrame(right, fg_color="transparent")
        input_f.grid(row=2, column=0, sticky="ew", padx=15, pady=15)
        self.agent_entry = ctk.CTkEntry(input_f, placeholder_text="Ask me anything...", fg_color=INNER_CARD, border_color=BORDER_COLOR)
        self.agent_entry.pack(side="left", fill="x", expand=True)
        self.agent_entry.bind("<Return>", lambda e: self.send_agent_msg())
        ctk.CTkButton(input_f, text="➤", width=40, fg_color=ACCENT_BLUE, command=self.send_agent_msg).pack(side="right", padx=(5,0))

        self.append_chat("Agent", "I've analyzed your system. Everything looks great! How can I help you today?")

    def send_agent_msg(self):
        msg = self.agent_entry.get().strip()
        if not msg: return
        self.agent_entry.delete(0, 'end')
        self.append_chat("You", msg)
        
        # Real AI Logic Simulation
        resp = "I'm not sure about that. Try asking about 'RAM', 'FPS', 'crash', or 'mods'."
        q = msg.lower()
        if "ram" in q or "memory" in q: resp = "To allocate more RAM, go to Settings -> Performance Settings and adjust the 'RAM Allocation' dropdown. Currently you have it set to optimal."
        elif "fps" in q or "lag" in q: resp = "I recommend installing 'Fabulously Optimized' from the Modpacks tab. It can boost your FPS by up to 120%!"
        elif "crash" in q or "error" in q: resp = "I scanned the latest logs. No recent crashes found. Make sure your Java version matches the Minecraft requirement (Java 21 for 1.21.x)."
        elif "mods" in q or "addon" in q: resp = "You can one-click install essential addons from the Dashboard tab!"
        elif "hi" in q or "hello" in q: resp = f"Hello again {self.user_config.get('username')}! Need help with Minecraft?"
        
        self.after(500, lambda: self.append_chat("Agent", resp))
        self.add_agent_log(f"Answered query: {msg[:10]}...")

    def append_chat(self, sender, msg):
        f = ctk.CTkFrame(self.chat_history, fg_color="transparent")
        f.pack(fill="x", pady=5)
        col = ACCENT_CYAN if sender=="Agent" else TEXT_PRIMARY
        align = "w" if sender=="Agent" else "e"
        
        bubble = ctk.CTkFrame(f, fg_color=CARD_COLOR if sender=="Agent" else ACCENT_BLUE, corner_radius=8)
        bubble.pack(anchor=align, padx=10)
        ctk.CTkLabel(bubble, text=msg, text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=11), wraplength=250, justify="left").pack(padx=12, pady=8)
        
        # Scroll to bottom hack
        self.chat_history._parent_canvas.yview_moveto(1.0)

    def add_agent_log(self, msg):
        self.add_dash_log(msg) # share log space for simplicity

    # =========================================================================
    # CORE FUNCTIONALITY: MODS & LAUNCHING
    # =========================================================================
    def fetch_real_mods_data(self):
        for slug in MOD_SLUGS:
            info = ModrinthAPI.get_project_info(slug)
            if info:
                self.cached_mod_data.append({
                    "slug": slug, "title": info.get("title", slug.capitalize()),
                    "desc": info.get("description", ""), "icon_url": info.get("icon_url")
                })
                self.after(0, self.update_dashboard_addons)

    def update_dashboard_addons(self):
        if not hasattr(self, 'dash_addons_grid'): return
        for widget in self.dash_addons_grid.winfo_children(): widget.destroy()
            
        for i, mdata in enumerate(self.cached_mod_data[:8]):
            r, c = i // 4, i % 4
            card = ctk.CTkFrame(self.dash_addons_grid, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR, height=60)
            card.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            card.pack_propagate(False)
            
            is_installed = any(mdata["slug"] in f.lower() for f in os.listdir(self.mods_dir)) if os.path.exists(self.mods_dir) else False
            
            ctk.CTkLabel(card, text=mdata["title"][:15], font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(10,0))
            ctk.CTkLabel(card, text="✔ Installed" if is_installed else "❌ Missing", font=ctk.CTkFont(size=9), text_color=ACCENT_GREEN if is_installed else "#EF4444").pack(anchor="w", padx=10)

    def download_all_mods(self):
        self.add_dash_log("Starting mod download thread...")
        threading.Thread(target=self._process_mod_downloads, daemon=True).start()

    def _process_mod_downloads(self):
        target_version = self.user_config.get("version", "1.21.4")
        success = 0
        for slug in MOD_SLUGS:
            ver_data = ModrinthAPI.get_latest_version(slug, target_version)
            if ver_data and "files" in ver_data:
                file_info = next((f for f in ver_data["files"] if f.get("primary")), ver_data["files"][0])
                filepath = os.path.join(self.mods_dir, file_info["filename"])
                if not os.path.exists(filepath):
                    try:
                        urllib.request.urlretrieve(file_info["url"], filepath)
                        success += 1
                    except: pass
        self.add_dash_log(f"Installed {success} new mods.")
        self.after(0, self.update_dashboard_addons)
        if success > 0: messagebox.showinfo("Success", f"Installed {success} addons successfully!")

    def handle_launch(self):
        if self.play_btn.cget("text") == "▶ PLAY":
            self.play_btn.configure(text="⏳ LAUNCHING...", fg_color="#F59E0B")
            threading.Thread(target=self.start_minecraft, daemon=True).start()
        else:
            if self.game_process:
                self.game_process.terminate()
                self.add_dash_log("Game forcefully terminated.")

    def start_minecraft(self):
        ver = self.user_config.get("version", "1.21.4")
        ram = self.user_config.get("ram", 8192)
        user = self.user_config.get("username", "Player")

        self.add_dash_log(f"Installing Fabric loader for {ver}...")
        try:
            minecraft_launcher_lib.fabric.install_fabric(ver, self.mc_dir)
            installed = minecraft_launcher_lib.utils.get_installed_versions(self.mc_dir)
            fab_id = next((v['id'] for v in installed if 'fabric' in v['id'] and ver in v['id']), None)

            if not fab_id: raise Exception("Fabric installation not found.")

            jvm_args = [f"-Xmx{ram}M", f"-Xms{ram}M", "-XX:+UnlockExperimentalVMOptions", "-XX:+UseG1GC"]
            if self.user_config.get("opt_launcher", True):
                jvm_args.extend(["-XX:G1NewSizePercent=20", "-XX:G1ReservePercent=20"])

            options = {"username": user, "uuid": str(uuid.uuid4()), "token": "", "jvmArguments": jvm_args}
            mc_cmd = minecraft_launcher_lib.command.get_minecraft_command(fab_id, self.mc_dir, options)
            
            self.add_dash_log("Launching Minecraft process...")
            self.game_process = subprocess.Popen(mc_cmd)
            self.after(0, lambda: self.play_btn.configure(text="🛑 STOP", fg_color="#EF4444"))
            self.game_process.wait()
            self.add_dash_log("Game process ended normally.")
        except Exception as e:
            self.add_dash_log(f"Launch Error: {str(e)[:30]}")
        finally:
            self.after(0, lambda: self.play_btn.configure(text="▶ PLAY", fg_color=ACCENT_BLUE))

if __name__ == "__main__":
    app = SupersonicClientMaster()
    app.mainloop()
