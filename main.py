import sys
import os
import uuid
import threading
import json
import shutil
import requests
import subprocess
import webbrowser
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw
import minecraft_launcher_lib

# --- ULTRA-MODERN DARK COLOUR PALETTE (Exactly from Screenshots) ---
BG_COLOR = "#080A10"          # Darkest deep navy background
SIDEBAR_COLOR = "#0D111A"     # Sidebar background
CARD_COLOR = "#111622"        # Main card backgrounds
INNER_CARD = "#171E2E"        # Inner widgets and sub-panels
ACCENT_BLUE = "#1E5DFB"       # Primary electric blue
ACCENT_CYAN = "#00B2FE"       # Cyan accent
ACCENT_GREEN = "#10B981"      # Green success accent
ACCENT_PURPLE = "#7C3AED"     # Purple premium/alt accent
TEXT_PRIMARY = "#FFFFFF"      # Pure white text
TEXT_MUTED = "#5D6B88"        # Soft gray/blue muted text
BORDER_COLOR = "#1B2234"      # Thin border highlights

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class SupersonicClientMaster(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SUPERSONIC CLIENT v2.5.0")
        self.geometry("1450 dropped_resizable")
        self.geometry("1440x900")
        self.minsize(1366, 768)
        self.configure(fg_color=BG_COLOR)

        self.config_file = "supersonic_config.json"
        self.user_config = self.load_config()
        self.game_process = None
        self.hardcoded_api_key = "AQ.Ab8RN6IZzVVGS9dP9RnVtJTGvlYtl8UfW9uUb8FD7G-62moFDQ"
        self.appdata_dir = os.path.join(os.getenv('APPDATA'), 'SupersonicClient', 'bin')
        os.makedirs(self.appdata_dir, exist_ok=True)

        # Layout grids
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_header()
        self.setup_frames()
        self.show_frame("Dashboard")

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: return json.load(f)
            except: pass
        return {"ram": 8192, "username": "Raffiee_playssMC", "version": "1.21.4", "alt_accounts": ["Raffiee_playssMC"]}

    def save_config(self):
        try:
            with open(self.config_file, "w") as f: json.dump(self.user_config, f, indent=4)
        except: pass

    # ==================== HEADER SYSTEM ====================
    def setup_header(self):
        # Top title overlay matches "THE NEXT GENERATION MINECRAFT LAUNCHER"
        self.header_frame = ctk.CTkFrame(self, height=45, fg_color=BG_COLOR, corner_radius=0)
        self.header_frame.grid(row=0, column=1, sticky="ew")
        self.header_frame.pack_propagate(False)
        
        lbl = ctk.CTkLabel(self.header_frame, text="THE NEXT GENERATION MINECRAFT LAUNCHER", 
                             font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold", spacing=2), text_color=ACCENT_CYAN)
        lbl.pack(pady=10)

    # ==================== SIDEBAR SYSTEM ====================
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(12, weight=1)

        # Brand Logo area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(20, 25), sticky="w")
        
        try:
            logo_img = ctk.CTkImage(light_image=Image.open(resource_path("1000117781.png")), 
                                    dark_image=Image.open(resource_path("1000117781.png")), size=(40, 40))
            ctk.CTkLabel(logo_frame, image=logo_img, text="").pack(side="left")
        except:
            ctk.CTkLabel(logo_frame, text="⚡", font=ctk.CTkFont(size=28), text_color=ACCENT_BLUE).pack(side="left")
            
        ctk.CTkLabel(logo_frame, text=" SUPERSONIC\n CLIENT", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), 
                     text_color=TEXT_PRIMARY, justify="left").pack(side="left", padx=10)

        # Nav Buttons list matching screenshots
        self.nav_buttons = {}
        nav_items = [
            ("🏠  Dashboard", "Dashboard", None),
            ("📦  Modpacks", "Modpacks", None),
            ("🧩  Addons", "Addons", "NEW"),
            ("🗃️  Instances", "Instances", None),
            ("🌐  Servers", "Servers", None),
            ("🎨  Resource Packs", "ResourcePacks", None),
            ("🗺️  Worlds", "Worlds", None),
            ("⚙️  Settings", "Settings", None),
            ("🤖  Agent (AI)", "Agent", "AI")
        ]

        for i, (text, name, badge) in enumerate(nav_items):
            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            btn_frame.grid(row=i+1, column=0, sticky="ew", padx=10, pady=2)
            
            btn = ctk.CTkButton(btn_frame, text=text, fg_color="transparent", text_color=TEXT_MUTED, 
                                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), anchor="w", height=38, 
                                command=lambda n=name: self.show_frame(n))
            btn.pack(side="left", fill="x", expand=True)
            self.nav_buttons[name] = btn

            if badge:
                bg_col = ACCENT_PURPLE if badge == "NEW" else ACCENT_GREEN
                badge_lbl = ctk.CTkLabel(btn_frame, text=badge, font=ctk.CTkFont(size=9, weight="bold"), 
                                         text_color="black" if badge == "AI" else "white", fg_color=bg_col, 
                                         corner_radius=4, width=32, height=16)
                badge_lbl.pack(side="right", padx=(0, 10))

        # Bottom Account info
        self.profile_frame = ctk.CTkFrame(self.sidebar, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        self.profile_frame.grid(row=13, column=0, padx=15, pady=(10, 15), sticky="ew")
        
        # User details display
        lbl_acc = ctk.CTkLabel(self.profile_frame, text="Account", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED)
        lbl_acc.pack(anchor="w", padx=12, pady=(8, 0))
        
        self.user_lbl = ctk.CTkLabel(self.profile_frame, text=self.user_config.get("username", "Raffiee_playssMC"), 
                                     font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=TEXT_PRIMARY)
        self.user_lbl.pack(anchor="w", padx=12)
        
        premium_lbl = ctk.CTkLabel(self.profile_frame, text="👑 Premium", font=ctk.CTkFont(size=11, weight="bold"), text_color="#F59E0B")
        premium_lbl.pack(anchor="w", padx=12, pady=(0, 8))

        # Discord & Links
        link_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        link_frame.grid(row=14, column=0, padx=15, pady=(0, 15), sticky="ew")
        ctk.CTkButton(link_frame, text="🌐 Website", fg_color="transparent", text_color=TEXT_MUTED, width=80, height=20, font=ctk.CTkFont(size=11), command=lambda: webbrowser.open("https://supersonicclient.com")).pack(side="left")
        ctk.CTkButton(link_frame, text="💬 Discord", fg_color="transparent", text_color=TEXT_MUTED, width=80, height=20, font=ctk.CTkFont(size=11), command=lambda: webbrowser.open("https://discord.gg/supersonic")).pack(side="right")

    # ==================== MAIN FRAMES ROUTER ====================
    def setup_frames(self):
        self.frames_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.frames_container.grid(row=1, column=1, sticky="nsew")
        self.frames_container.grid_rowconfigure(0, weight=1)
        self.frames_container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.init_dashboard()
        self.init_modpacks()
        self.init_addons()
        self.init_settings()
        self.init_agent()

        # Placeholders for empty views
        for f_name in ["Instances", "Servers", "ResourcePacks", "Worlds"]:
            frame = ctk.CTkFrame(self.frames_container, fg_color="transparent")
            self.frames[f_name] = frame
            ctk.CTkLabel(frame, text=f"{f_name} View - Coming soon in v2.5.0", font=ctk.CTkFont(size=20), text_color=TEXT_MUTED).pack(expand=True)

    def show_frame(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.configure(fg_color=INNER_CARD if btn_name == name else "transparent", 
                          text_color=TEXT_PRIMARY if btn_name == name else TEXT_MUTED)
        for f_name, f in self.frames.items():
            if f_name == name:
                f.grid(row=0, column=0, sticky="nsew")
            else:
                f.grid_forget()

    # ==================== FRAME 1: DASHBOARD ====================
    def init_dashboard(self):
        f = ctk.CTkFrame(self.frames_container, fg_color="transparent")
        self.frames["Dashboard"] = f
        
        # Configure layout inside dashboard
        f.grid_columnconfigure(0, weight=3)
        f.grid_columnconfigure(1, weight=1)
        f.grid_rowconfigure(0, weight=1)

        left_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        left_scroll.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)

        # --- Sub-widget 1: Header Banner with Play button ---
        banner = ctk.CTkFrame(left_scroll, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR, height=180)
        banner.pack(fill="x", pady=(0, 20))
        banner.pack_propagate(False)

        ctk.CTkLabel(banner, text="SUPERSONIC CLIENT", font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).place(x=30, y=25)
        ctk.CTkLabel(banner, text="Hyper optimized. Ultra fast. Future ready.", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED).place(x=30, y=65)

        spec_lbl = ctk.CTkLabel(banner, text="🟢 Minecraft 1.21.4    ⚡ Performance: Ultra    📅 Last Played: Today", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        spec_lbl.place(x=30, y=120)

        self.play_btn = ctk.CTkButton(banner, text="▶  PLAY", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), 
                                      fg_color=ACCENT_BLUE, hover_color="#1446C9", width=180, height=55, corner_radius=10, command=self.handle_launch)
        self.play_btn.place(relx=0.95, rely=0.5, anchor="e")

        # --- Sub-widget 2: All Addons (One Click) ---
        addons_header = ctk.CTkFrame(left_scroll, fg_color="transparent")
        addons_header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(addons_header, text="ALL ADDONS - ONE CLICK INSTALL", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(addons_header, text="📥 Install All", fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR, width=110, height=28, corner_radius=6, text_color=TEXT_PRIMARY).pack(side="right")

        addons_grid = ctk.CTkFrame(left_scroll, fg_color="transparent")
        addons_grid.pack(fill="x", pady=(0, 25))
        for col in range(5): addons_grid.grid_columnconfigure(col, weight=1)

        default_addons = [
            ("Sodium", "Boosts FPS"), ("Iris Shaders", "Shaders Mod"), ("Lithium", "Performance"), 
            ("Indium", "Better Compat"), ("Phosphor", "Lighting Engine"), ("FerriteCore", "Memory Usage"), 
            ("Starlight", "Optimization"), ("Entity Culling", "Optimized Entities"), ("ImmediatelyFast", "Speed Boost"), 
            ("More Culling", "Extra Culling")
        ]

        for i, (name, desc) in enumerate(default_addons):
            row = i // 5
            col = i % 5
            card = ctk.CTkFrame(addons_grid, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR, height=75)
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=10, pady=(10, 2))
            ctk.CTkLabel(card, text="✔️ Installed", font=ctk.CTkFont(size=9), text_color=ACCENT_GREEN).pack(anchor="w", padx=10)

        # --- Sub-widget 3: Server Card ---
        server_header = ctk.CTkFrame(left_scroll, fg_color="transparent")
        server_header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(server_header, text="FEATURED SERVERS", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")

        server_card = ctk.CTkFrame(left_scroll, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR, height=90)
        server_card.pack(fill="x", pady=(0, 25))
        server_card.pack_propagate(False)
        ctk.CTkLabel(server_card, text="NarratorMC Server", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_PRIMARY).place(x=25, y=18)
        ctk.CTkLabel(server_card, text="IP: www.NarratorMC.net", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).place(x=25, y=48)
        ctk.CTkLabel(server_card, text="ONLINE", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#064E3B", text_color=ACCENT_GREEN, corner_radius=6, padx=12, pady=5).place(relx=0.95, rely=0.5, anchor="e")

        # --- Sub-widget 4: Dashboard Footer Status Gauges ---
        status_bar = ctk.CTkFrame(left_scroll, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR, height=80)
        status_bar.pack(fill="x")
        status_bar.grid_rowconfigure(0, weight=1)
        for col in range(3): status_bar.grid_columnconfigure(col, weight=1)

        # Progress bar 1
        pb1_f = ctk.CTkFrame(status_bar, fg_color="transparent")
        pb1_f.grid(row=0, column=0, padx=20, sticky="ew")
        ctk.CTkLabel(pb1_f, text="RAM Usage", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
        p1 = ctk.CTkProgressBar(pb1_f, fg_color=INNER_CARD, progress_color=ACCENT_BLUE, height=8)
        p1.set(0.4)
        p1.pack(fill="x", pady=5)
        ctk.CTkLabel(pb1_f, text="3.2 GB / 8 GB", font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY).pack(anchor="e")

        # Progress bar 2
        pb2_f = ctk.CTkFrame(status_bar, fg_color="transparent")
        pb2_f.grid(row=0, column=1, padx=20, sticky="ew")
        ctk.CTkLabel(pb2_f, text="FPS Boost", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
        p2 = ctk.CTkProgressBar(pb2_f, fg_color=INNER_CARD, progress_color=ACCENT_GREEN, height=8)
        p2.set(0.8)
        p2.pack(fill="x", pady=5)
        ctk.CTkLabel(pb2_f, text="+120%", font=ctk.CTkFont(size=11), text_color=ACCENT_GREEN).pack(anchor="e")

        # Progress bar 3
        pb3_f = ctk.CTkFrame(status_bar, fg_color="transparent")
        pb3_f.grid(row=0, column=2, padx=20, sticky="ew")
        ctk.CTkLabel(pb3_f, text="Ping latency", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w")
        p3 = ctk.CTkProgressBar(pb3_f, fg_color=INNER_CARD, progress_color=ACCENT_PURPLE, height=8)
        p3.set(0.2)
        p3.pack(fill="x", pady=5)
        ctk.CTkLabel(pb3_f, text="24ms", font=ctk.CTkFont(size=11), text_color=ACCENT_PURPLE).pack(anchor="e")

        # --- Right Panel Dashboard (Agent Quickview) ---
        right_panel = ctk.CTkFrame(f, fg_color=SIDEBAR_COLOR, width=320, border_width=1, border_color=BORDER_COLOR)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=10)
        right_panel.pack_propagate(False)

        ctk.CTkLabel(right_panel, text="AGENT (AI) BETA", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(right_panel, text="Your personal AI assistant", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(0, 20))

        # Mini Agent Terminal Panel
        agent_term = ctk.CTkFrame(right_panel, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=180)
        agent_term.pack(fill="x", padx=15, pady=5)
        agent_term.pack_propagate(False)
        
        ctk.CTkLabel(agent_term, text="💬 Supersonic Agent:", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_CYAN).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(agent_term, text="I can help you auto-fix crashes,\noptimize performance specs,\nand automatically download\nrequired client files.", 
                     font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY, justify="left").pack(anchor="w", padx=15)

        # Quick fix panel
        fix_panel = ctk.CTkFrame(right_panel, fg_color=INNER_CARD, corner_radius=10, height=100)
        fix_panel.pack(fill="x", padx=15, pady=15)
        fix_panel.pack_propagate(False)
        ctk.CTkLabel(fix_panel, text="Auto Fix (One Click)", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(10, 5))
        ctk.CTkButton(fix_panel, text="🔧 Scan & Fix", fg_color=ACCENT_BLUE, height=30).pack(fill="x", padx=15)

        # Logs terminal mock
        ctk.CTkLabel(right_panel, text="Recent System Actions", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(15, 5))
        logs_box = ctk.CTkFrame(right_panel, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        logs_box.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        mock_logs = [
            "[12:48] Java Path synced ✔",
            "[12:46] Corrupted cache cleared ✔",
            "[12:43] Optimized heap memory ✔",
            "[12:41] No conflicting mods found ✔"
        ]
        for log in mock_logs:
            ctk.CTkLabel(logs_box, text=log, font=ctk.CTkFont(family="Courier New", size=11), text_color=ACCENT_GREEN).pack(anchor="w", padx=15, pady=6)

    # ==================== FRAME 2: MODPACKS ====================
    def init_modpacks(self):
        f = ctk.CTkFrame(self.frames_container, fg_color="transparent")
        self.frames["Modpacks"] = f
        
        f.grid_columnconfigure(0, weight=3)
        f.grid_columnconfigure(1, weight=1)
        f.grid_rowconfigure(0, weight=1)

        left_area = ctk.CTkFrame(f, fg_color="transparent")
        left_area.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)

        # Header Search Modpack title
        hdr = ctk.CTkFrame(left_area, fg_color="transparent")
        hdr.pack(fill="x", pady=(10, 15))
        ctk.CTkLabel(hdr, text="MODPACKS", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(hdr, text="+ Import Modpack", fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR).pack(side="right", padx=10)
        ctk.CTkButton(hdr, text="Browse CurseForge ↗", fg_color=ACCENT_BLUE).pack(side="right")

        # Scrollable Packs Grid
        grid_scroll = ctk.CTkScrollableFrame(left_area, fg_color="transparent")
        grid_scroll.pack(fill="both", expand=True)
        
        # Two columns grid inside scroll
        grid_scroll.grid_columnconfigure(0, weight=1)
        grid_scroll.grid_columnconfigure(1, weight=1)

        modpacks_list = [
            ("Fabulously Optimized", "1.21.4", "Optimized for FPS", "Vanilla+ experience with high performance."),
            ("Better MC [FABRIC]", "1.21.4", "Vanilla+ Plus", "Next-gen enhancements & custom quests."),
            ("RLCraft", "1.20.1", "Hardcore Survival", "Unforgiving gameplay with customized realisms."),
            ("All the Mods 9", "1.20.1", "Kitchen Sink", "Massive modpack aggregating engineering & magic."),
            ("SkyFactory 5", "1.20.1", "Skyblock Setup", "Automated progression on a solitary tree floating."),
            ("Prominence II RPG", "1.20.1", "RPG & Adventure", "Beautiful dungeons, bosses and complete skill trees.")
        ]

        for idx, (name, ver, tag, desc) in enumerate(modpacks_list):
            row = idx // 2
            col = idx % 2
            
            card = ctk.CTkFrame(grid_scroll, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR, height=180)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            card.pack_propagate(False)

            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(15, 2))
            ctk.CTkLabel(card, text=f"Version: {ver}  •  {tag}", font=ctk.CTkFont(size=11), text_color=ACCENT_CYAN).pack(anchor="w", padx=15)
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=12), text_color=TEXT_MUTED, justify="left").pack(anchor="w", padx=15, pady=8)

            btn_f = ctk.CTkFrame(card, fg_color="transparent")
            btn_f.pack(fill="x", side="bottom", pady=10, padx=15)
            ctk.CTkButton(btn_f, text="📥 Install Now", fg_color=ACCENT_BLUE, height=28).pack(side="right")

        # Right sidebar (filters/metadata)
        r_panel = ctk.CTkFrame(f, fg_color=SIDEBAR_COLOR, width=320, border_width=1, border_color=BORDER_COLOR)
        r_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=10)
        r_panel.pack_propagate(False)

        ctk.CTkLabel(r_panel, text="SEARCH & FILTER", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(20, 10))
        
        search_ent = ctk.CTkEntry(r_panel, placeholder_text="Search modpack items...", fg_color=INNER_CARD, border_color=BORDER_COLOR, height=35)
        search_ent.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(r_panel, text="Minecraft Version", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=20)
        v_drop = ctk.CTkOptionMenu(r_panel, values=["All Versions", "1.21.4", "1.20.1", "1.19.2"], fg_color=INNER_CARD)
        v_drop.pack(fill="x", padx=15, pady=(5, 15))

        # Bottom stats
        ctk.CTkLabel(r_panel, text="Client Statistics", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(10, 5))
        stats_box = ctk.CTkFrame(r_panel, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        stats_box.pack(fill="x", padx=15, pady=5)
        
        stats_data = [("Total Modpacks", "1,248"), ("Installed Local", "12"), ("Storage Used", "18.4 GB")]
        for k, v in stats_data:
            df = ctk.CTkFrame(stats_box, fg_color="transparent")
            df.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(df, text=k, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(df, text=v, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY).pack(side="right")

    # ==================== FRAME 3: ADDONS ====================
    def init_addons(self):
        f = ctk.CTkFrame(self.frames_container, fg_color="transparent")
        self.frames["Addons"] = f
        
        f.grid_columnconfigure(0, weight=3)
        f.grid_columnconfigure(1, weight=1)
        f.grid_rowconfigure(0, weight=1)

        left_area = ctk.CTkFrame(f, fg_color="transparent")
        left_area.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)

        # Header Title
        hdr = ctk.CTkFrame(left_area, fg_color="transparent")
        hdr.pack(fill="x", pady=(10, 15))
        ctk.CTkLabel(hdr, text="ADDONS MANAGER", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(hdr, text="+ Import Local .jar", fg_color=ACCENT_PURPLE, command=self.import_local_jar).pack(side="right")

        # Scrollable Addons Grid
        grid_scroll = ctk.CTkScrollableFrame(left_area, fg_color="transparent")
        grid_scroll.pack(fill="both", expand=True)

        grid_scroll.grid_columnconfigure(0, weight=1)
        grid_scroll.grid_columnconfigure(1, weight=1)
        grid_scroll.grid_columnconfigure(2, weight=1)

        mods_list = [
            ("Sodium", "Boosts frame rates and reduces lag spikes."),
            ("Iris Shaders", "Adds shader pack support with optimized engine."),
            ("Lithium", "Improves physics and chunk loading performance."),
            ("Indium", "Better rendering compatibility interface."),
            ("Phosphor", "Lighting rendering optimizer."),
            ("FerriteCore", "Significantly reduces RAM heap usage."),
            ("Starlight", "Rewrites the lighting engine for extreme speed."),
            ("Entity Culling", "Do not render out-of-sight entities."),
            ("ImmediatelyFast", "Optimizes GUI and font rendering speed."),
        ]

        for idx, (name, desc) in enumerate(mods_list):
            row = idx // 3
            col = idx % 3
            card = ctk.CTkFrame(grid_scroll, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=110)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            card.pack_propagate(False)

            ctk.CTkLabel(card, text=name, font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=12, pady=(10, 2))
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, justify="left", wraplength=130).pack(anchor="w", padx=12)
            
            status_f = ctk.CTkFrame(card, fg_color="transparent")
            status_f.pack(fill="x", side="bottom", padx=12, pady=8)
            ctk.CTkLabel(status_f, text="✔️ Installed", font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT_GREEN).pack(side="left")

        # Bottom Performance Charts Section (Matches Screenshot 3)
        perf_f = ctk.CTkFrame(left_area, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR, height=120)
        perf_f.pack(fill="x", pady=(15, 0))
        perf_f.pack_propagate(False)

        ctk.CTkLabel(perf_f, text="Performance Improvements (Live)", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY).place(x=15, y=8)

        # FPS Graph mock
        c1 = tk.Canvas(perf_f, bg=INNER_CARD, highlightthickness=0, width=130, height=50)
        c1.place(x=15, y=35)
        c1.create_line(0, 40, 30, 35, 60, 20, 90, 10, 130, 5, fill=ACCENT_CYAN, width=2)
        ctk.CTkLabel(perf_f, text="FPS Boost (+120%)", font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT_CYAN).place(x=15, y=90)

        # RAM Graph mock
        c2 = tk.Canvas(perf_f, bg=INNER_CARD, highlightthickness=0, width=130, height=50)
        c2.place(x=175, y=35)
        c2.create_line(0, 10, 30, 25, 60, 30, 90, 42, 130, 45, fill=ACCENT_PURPLE, width=2)
        ctk.CTkLabel(perf_f, text="RAM Usage (-35%)", font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT_PURPLE).place(x=175, y=90)

        # CPU Graph mock
        c3 = tk.Canvas(perf_f, bg=INNER_CARD, highlightthickness=0, width=130, height=50)
        c3.place(x=335, y=35)
        c3.create_line(0, 15, 40, 25, 80, 35, 130, 45, fill=ACCENT_GREEN, width=2)
        ctk.CTkLabel(perf_f, text="CPU Usage (-28%)", font=ctk.CTkFont(size=10, weight="bold"), text_color=ACCENT_GREEN).place(x=335, y=90)

        # Right Panel
        r_panel = ctk.CTkFrame(f, fg_color=SIDEBAR_COLOR, width=320, border_width=1, border_color=BORDER_COLOR)
        r_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=10)
        r_panel.pack_propagate(False)

        status_card = ctk.CTkFrame(r_panel, fg_color=INNER_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=110)
        status_card.pack(fill="x", padx=15, pady=15)
        status_card.pack_propagate(False)
        ctk.CTkLabel(status_card, text="✔️ Client fully optimized!", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_GREEN).pack(pady=(25, 5))
        ctk.CTkLabel(status_card, text="All addons up to date.", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack()

        # Addon Info panel
        info_f = ctk.CTkFrame(r_panel, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        info_f.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        ctk.CTkLabel(info_f, text="Addon Metadata", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=15)
        
        meta_items = [("Selected Mod", "Sodium"), ("Installed version", "v0.5.8"), ("Game target", "1.21.4"), ("Author", "JellySquid")]
        for k, v in meta_items:
            cf = ctk.CTkFrame(info_f, fg_color="transparent")
            cf.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(cf, text=k, text_color=TEXT_MUTED, font=ctk.CTkFont(size=11)).pack(side="left")
            ctk.CTkLabel(cf, text=v, text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=11, weight="bold")).pack(side="right")

    def import_local_jar(self):
        file_path = filedialog.askopenfilename(filetypes=[("JAR files", "*.jar")])
        if file_path:
            try:
                target_dir = os.path.join(minecraft_launcher_lib.utils.get_minecraft_directory(), "mods")
                os.makedirs(target_dir, exist_ok=True)
                shutil.copy2(file_path, os.path.join(target_dir, os.path.basename(file_path)))
                messagebox.showinfo("Success", f"Imported {os.path.basename(file_path)} directly to mods!")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ==================== FRAME 4: SETTINGS ====================
    def init_settings(self):
        f = ctk.CTkFrame(self.frames_container, fg_color="transparent")
        self.frames["Settings"] = f
        
        f.grid_columnconfigure(0, weight=3)
        f.grid_columnconfigure(1, weight=1)
        f.grid_rowconfigure(0, weight=1)

        left_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        left_scroll.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)

        # Settings main header matching screen
        hdr = ctk.CTkFrame(left_scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(hdr, text="SETTINGS", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(hdr, text="Reset to Default", fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR, width=120).pack(side="right")

        # 3 Columns structure matching Screenshot 4
        settings_grid = ctk.CTkFrame(left_scroll, fg_color="transparent")
        settings_grid.pack(fill="both", expand=True)
        settings_grid.grid_columnconfigure(0, weight=1)
        settings_grid.grid_columnconfigure(1, weight=1)
        settings_grid.grid_columnconfigure(2, weight=1)

        # --- Column 1: General & Launcher Settings ---
        col1 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        col1.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        # General Settings Box
        box_gen = ctk.CTkFrame(col1, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box_gen.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(box_gen, text="GENERAL SETTINGS", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        self.create_dropdown(box_gen, "Language", ["English", "Spanish", "Bengali"])
        self.create_dropdown(box_gen, "Theme", ["Dark (Default)", "AMOLED Black"])
        self.create_toggle(box_gen, "Start with Windows", True)
        self.create_toggle(box_gen, "Minimize to System Tray", True)
        self.create_toggle(box_gen, "Confirm Before Exit", True)

        # Launcher Settings Box
        box_launch = ctk.CTkFrame(col1, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box_launch.pack(fill="x")
        ctk.CTkLabel(box_launch, text="LAUNCHER SETTINGS", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        self.create_toggle(box_launch, "Check for Updates", True)
        self.create_toggle(box_launch, "Download Updates", True)
        self.create_toggle(box_launch, "Beta Updates", False)

        # --- Column 2: Performance & Download Settings ---
        col2 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        col2.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        # Performance Settings Box
        box_perf = ctk.CTkFrame(col2, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box_perf.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(box_perf, text="PERFORMANCE SETTINGS", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        self.create_dropdown(box_perf, "Performance Mode", ["Ultra (Recommended)", "Standard"])
        
        # Custom RAM Selector dropdown matching screen
        ctk.CTkLabel(box_perf, text="RAM Allocation (Default)", font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(5, 2))
        self.ram_menu = ctk.CTkOptionMenu(box_perf, values=["2048 MB", "4096 MB", "8192 MB", "12288 MB", "16384 MB"], fg_color=INNER_CARD, button_color=ACCENT_BLUE, command=self.update_ram_cfg)
        self.ram_menu.set(f"{self.user_config.get('ram', 8192)} MB")
        self.ram_menu.pack(fill="x", padx=15, pady=(0, 10))

        self.create_toggle(box_perf, "Preload Assets", True)
        self.create_toggle(box_perf, "Smart Memory Mgmt", True)

        # Download Settings Box
        box_dl = ctk.CTkFrame(col2, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box_dl.pack(fill="x")
        ctk.CTkLabel(box_dl, text="DOWNLOAD SETTINGS", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        self.create_dropdown(box_dl, "Download Speed Limit", ["Unlimited", "10 MB/s", "5 MB/s"])
        self.create_dropdown(box_dl, "Max Connections", ["16", "8", "4"])

        # --- Column 3: Minecraft & Cloud & Sync ---
        col3 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        col3.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")

        # Minecraft Settings Box
        box_mc = ctk.CTkFrame(col3, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box_mc.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(box_mc, text="MINECRAFT SETTINGS", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        self.create_dropdown(box_mc, "Default Java Version", ["Java 21 (Recommended)", "Java 17"])
        
        # Game version selector
        ctk.CTkLabel(box_mc, text="Game Launch Version", font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(5, 2))
        self.ver_menu = ctk.CTkOptionMenu(box_mc, values=["1.21.4", "1.21.1", "1.20.1", "1.19.2"], fg_color=INNER_CARD, button_color=ACCENT_BLUE, command=self.update_ver_cfg)
        self.ver_menu.set(self.user_config.get("version", "1.21.4"))
        self.ver_menu.pack(fill="x", padx=15, pady=(0, 10))

        self.create_toggle(box_mc, "Automatically Install Java", True)
        self.create_toggle(box_mc, "Use Native Libraries", True)

        # Cloud & Sync Box
        box_sync = ctk.CTkFrame(col3, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box_sync.pack(fill="x")
        ctk.CTkLabel(box_sync, text="CLOUD & SYNC", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        self.create_toggle(box_sync, "Enable Cloud Sync", True)
        self.create_toggle(box_sync, "Sync Across Devices", True)

        # Cloud storage usage slider widget
        cf = ctk.CTkFrame(box_sync, fg_color="transparent")
        cf.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(cf, text="Cloud Storage", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(cf, text="2.4 GB / 10 GB", font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY).pack(side="right")
        sl = ctk.CTkProgressBar(box_sync, fg_color=INNER_CARD, progress_color=ACCENT_BLUE, height=6)
        sl.set(0.24)
        sl.pack(fill="x", padx=15, pady=(0, 15))

        # --- Settings Right Panel System Overview ---
        r_panel = ctk.CTkFrame(f, fg_color=SIDEBAR_COLOR, width=320, border_width=1, border_color=BORDER_COLOR)
        r_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=10)
        r_panel.pack_propagate(False)

        ctk.CTkLabel(r_panel, text="SYSTEM OVERVIEW", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(20, 10))
        
        sys_box = ctk.CTkFrame(r_panel, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        sys_box.pack(fill="x", padx=15, pady=5)

        sys_specs = [
            ("OS", "Windows 11 64-bit"),
            ("CPU", "Intel Core i5-12400F"),
            ("RAM", "16.0 GB"),
            ("GPU", "NVIDIA GTX 1650"),
            ("Storage", "512 GB SSD")
        ]
        for k, v in sys_specs:
            f_s = ctk.CTkFrame(sys_box, fg_color="transparent")
            f_s.pack(fill="x", padx=15, pady=6)
            ctk.CTkLabel(f_s, text=k, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(f_s, text=v, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY).pack(side="right")

        ctk.CTkButton(r_panel, text="Run System Diagnostics", fg_color=ACCENT_BLUE).pack(fill="x", padx=15, pady=15)

    def create_dropdown(self, parent, label, options):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(5, 2))
        dp = ctk.CTkOptionMenu(parent, values=options, fg_color=INNER_CARD, button_color=BORDER_COLOR)
        dp.set(options[0])
        dp.pack(fill="x", padx=15, pady=(0, 10))

    def create_toggle(self, parent, label, default_on):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=6)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY).pack(side="left")
        sw = ctk.CTkSwitch(f, text="", progress_color=ACCENT_BLUE)
        if default_on: sw.select()
        sw.pack(side="right")

    def update_ram_cfg(self, val):
        self.user_config["ram"] = int(val.split()[0])
        self.save_config()

    def update_ver_cfg(self, val):
        self.user_config["version"] = val
        self.save_config()

    # ==================== FRAME 5: AGENT (AI) ====================
    def init_agent(self):
        f = ctk.CTkFrame(self.frames_container, fg_color="transparent")
        self.frames["Agent"] = f
        
        f.grid_columnconfigure(0, weight=3)
        f.grid_columnconfigure(1, weight=1)
        f.grid_rowconfigure(0, weight=1)

        left_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        left_scroll.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)

        # Banner Header matching Screenshot 5
        hdr = ctk.CTkFrame(left_scroll, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR, height=130)
        hdr.pack(fill="x", pady=(0, 20))
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="AGENT (AI) BETA", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=TEXT_PRIMARY).place(x=30, y=25)
        ctk.CTkLabel(hdr, text="Autonomous optimization & crash detection engine in real-time.", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).place(x=30, y=60)
        ctk.CTkLabel(hdr, text="🟢 Agent Engine Synchronized", font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT_GREEN).place(x=30, y=95)

        # System Status Dial and Actions Row
        row1 = ctk.CTkFrame(left_scroll, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 20))
        row1.grid_columnconfigure(0, weight=2)
        row1.grid_columnconfigure(1, weight=3)

        # Glowing dial system health box
        health_box = ctk.CTkFrame(row1, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR, height=180)
        health_box.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        health_box.pack_propagate(False)
        ctk.CTkLabel(health_box, text="System Health Overview", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=10)
        
        # Circular Canvas arc drawing
        dial_c = tk.Canvas(health_box, bg=CARD_COLOR, highlightthickness=0, width=110, height=110)
        dial_c.pack(side="left", padx=15)
        # draw arc for 98%
        dial_c.create_arc(10, 10, 100, 100, start=90, extent=-352, outline=ACCENT_BLUE, width=8, style="arc")
        dial_c.create_text(55, 55, text="98%", fill=TEXT_PRIMARY, font=("Segoe UI", 16, "bold"))

        det_f = ctk.CTkFrame(health_box, fg_color="transparent")
        det_f.pack(side="right", fill="both", expand=True, pady=15)
        ctk.CTkLabel(det_f, text="✔ Mod Files: Healthy", font=ctk.CTkFont(size=10), text_color=ACCENT_GREEN).pack(anchor="w")
        ctk.CTkLabel(det_f, text="✔ Java Version: Ok", font=ctk.CTkFont(size=10), text_color=ACCENT_GREEN).pack(anchor="w")
        ctk.CTkLabel(det_f, text="✔ Performance: Max", font=ctk.CTkFont(size=10), text_color=ACCENT_GREEN).pack(anchor="w")

        # Recommended Fixes Box
        rec_box = ctk.CTkFrame(row1, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR, height=180)
        rec_box.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        rec_box.pack_propagate(False)
        ctk.CTkLabel(rec_box, text="AI Recommendations", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=10)
        
        recs = [("Enable Sodium Extra", "Boosts FPS up to 15%"), ("Allocate More RAM", "Smoother rendering loads")]
        for title, sub in recs:
            rf = ctk.CTkFrame(rec_box, fg_color=INNER_CARD, corner_radius=8, height=45)
            rf.pack(fill="x", padx=15, pady=4)
            rf.pack_propagate(False)
            ctk.CTkLabel(rf, text=f"{title}\n{sub}", font=ctk.CTkFont(size=10), text_color=TEXT_PRIMARY, justify="left").pack(side="left", padx=10)
            ctk.CTkButton(rf, text="Apply", fg_color=ACCENT_BLUE, width=60, height=24, corner_radius=4).pack(side="right", padx=10)

        # Bottom Active Tasks Panel
        tasks_f = ctk.CTkFrame(left_scroll, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        tasks_f.pack(fill="x")
        ctk.CTkLabel(tasks_f, text="Active Background Tasks", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=15)

        tasks = [("Scanning game resources...", 0.75, ACCENT_BLUE, "75%"), ("Optimizing JVM heap settings...", 0.60, ACCENT_GREEN, "60%")]
        for desc, pct, col, pct_t in tasks:
            tf = ctk.CTkFrame(tasks_f, fg_color="transparent")
            tf.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(tf, text=desc, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(tf, text=pct_t, font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY).pack(side="right")
            
            pb = ctk.CTkProgressBar(tasks_f, fg_color=INNER_CARD, progress_color=col, height=6)
            pb.set(pct)
            pb.pack(fill="x", padx=15, pady=(2, 10))

        # Right Panel Chat Widget
        r_panel = ctk.CTkFrame(f, fg_color=SIDEBAR_COLOR, width=320, border_width=1, border_color=BORDER_COLOR)
        r_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=10)
        r_panel.pack_propagate(False)

        ctk.CTkLabel(r_panel, text="CHAT WITH AGENT", font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.chat_history = ctk.CTkTextbox(r_panel, fg_color=INNER_CARD, text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=12), border_width=1, border_color=BORDER_COLOR)
        self.chat_history.pack(fill="both", expand=True, padx=15, pady=10)
        self.chat_history.insert("end", "🤖 SupersonicAI: Connected. Paste your crash logs or ask any diagnostic questions here.\n\n")
        self.chat_history.configure(state="disabled")

        input_f = ctk.CTkFrame(r_panel, fg_color=INNER_CARD, height=45, corner_radius=6, border_width=1, border_color=BORDER_COLOR)
        input_f.pack(fill="x", padx=15, pady=(0, 15))
        input_f.pack_propagate(False)

        self.chat_entry = ctk.CTkEntry(input_f, placeholder_text="Ask me anything...", fg_color="transparent", border_width=0)
        self.chat_entry.pack(side="left", fill="both", expand=True, padx=10)
        ctk.CTkButton(input_f, text="Send", fg_color=ACCENT_BLUE, width=50, command=self.send_ai_message).pack(side="right", padx=5)

    def send_ai_message(self):
        msg = self.chat_entry.get().strip()
        if not msg: return
        self.chat_entry.delete(0, 'end')

        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"👤 You: {msg}\n\n")
        self.chat_history.configure(state="disabled")

        threading.Thread(target=self.query_gemini_api, args=(msg,), daemon=True).start()

    def query_gemini_api(self, prompt):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={self.hardcoded_api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req) as response:
                res = json.loads(response.read().decode('utf-8'))
            reply = res['candidates'][0]['content']['parts'][0]['text'].strip()

            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", f"🤖 Agent: {reply}\n\n")
            self.chat_history.see("end")
            self.chat_history.configure(state="disabled")
        except:
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", "🤖 Agent: Crash analysis pipeline failed. Please verify API configuration and network.\n\n")
            self.chat_history.configure(state="disabled")

    # ==================== CORE MC LAUNCH & MESA SYSTEM ====================
    def handle_launch(self):
        if self.game_process and self.game_process.poll() is None:
            try:
                self.game_process.terminate()
                self.play_btn.configure(text="▶  PLAY", fg_color=ACCENT_BLUE)
            except: pass
        else:
            self.play_btn.configure(state="disabled", text="RUNNING...")
            threading.Thread(target=self.launch_sequence, daemon=True).start()

    def setup_mesa_drivers(self):
        # Fallback offline dynamic link setup for D3D12 boost
        files = {
            "glslangValidator.exe": "https://github.com/vulkan-sdk-mirror/glslangValidator.exe",
            "opengl32.dll": "https://github.com/pal1000/mesa-dist-win/releases/download/23.1.3/opengl32.dll"
        }
        for fn, url in files.items():
            target = os.path.join(self.appdata_dir, fn)
            bundled = resource_path(fn)
            if os.path.exists(bundled) and not os.path.isdir(bundled):
                if not os.path.exists(target) or os.path.getsize(target) != os.path.getsize(bundled):
                    try: shutil.copy2(bundled, target)
                    except: pass
            else:
                if not os.path.exists(target) or os.path.getsize(target) < 500000:
                    try:
                        res = requests.get(url, timeout=10)
                        if res.status_code == 200:
                            with open(target, "wb") as f: f.write(res.content)
                    except: pass

    def launch_sequence(self):
        try:
            self.setup_mesa_drivers()
            mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
            version = self.user_config.get("version", "1.21.4")

            minecraft_launcher_lib.install.install_minecraft_version(version, mc_dir)
            fabric_ver = minecraft_launcher_lib.fabric.get_latest_loader_version()
            minecraft_launcher_lib.fabric.install_fabric(version, mc_dir, loader_version=fabric_ver)

            username = self.user_config.get("username", "Raffiee_playssMC")
            opts = {
                "username": username,
                "uuid": str(uuid.uuid3(uuid.NAMESPACE_DNS, username)),
                "token": "",
                "jvmArguments": [f"-Xmx{int(self.user_config.get('ram', 8192) / 1024)}G"]
            }
            cmd = minecraft_launcher_lib.command.get_minecraft_command(f"fabric-loader-{fabric_ver}-{version}", mc_dir, opts)

            # Custom rendering engine overrides
            custom_env = os.environ.copy()
            custom_env["PATH"] = self.appdata_dir + os.pathsep + custom_env.get("PATH", "")
            custom_env["MESA_GL_VERSION_OVERRIDE"] = "4.6"
            custom_env["MESA_GLSL_VERSION_OVERRIDE"] = "460"
            custom_env["GALLIUM_DRIVER"] = "d3d12"

            self.play_btn.configure(state="normal", text="🛑 STOP", fg_color="#DC2626", hover_color="#991B1B")
            self.game_process = subprocess.Popen(cmd, env=custom_env)
            self.game_process.wait()

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.play_btn.configure(state="normal", text="▶  PLAY", fg_color=ACCENT_BLUE, hover_color="#1446C9")

if __name__ == "__main__":
    app = SupersonicClientMaster()
    app.mainloop()
