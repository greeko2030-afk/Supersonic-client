import os
import sys
import json
import time
import threading
import subprocess
import traceback
from uuid import uuid1
import tkinter as tk

# Ensure required libraries are installed
try:
    import requests
    import customtkinter as ctk
    import minecraft_launcher_lib
except ImportError:
    print("Missing libraries. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "customtkinter", "minecraft-launcher-lib", "pillow"])
    import requests
    import customtkinter as ctk
    import minecraft_launcher_lib

# --- CONFIGURATION & CONSTANTS ---
VERSION = "2.5.0"
UPDATE_URL = "https://supersonic-client--greeko2030.replit.app/api/version"
MC_DIR = minecraft_launcher_lib.utils.get_minecraft_directory().replace("minecraft", "supersonic")
MODS_DIR = os.path.join(MC_DIR, "mods")

# Custom Color Palette
BG_COLOR = "#040914"
SIDEBAR_COLOR = "#0B1120"
CARD_COLOR = "#111827"
CARD_HOVER = "#1F2937"
ACCENT_BLUE = "#3B82F6"
ACCENT_BLUE_HOVER = "#2563EB"
ACCENT_GREEN = "#10B981"
TEXT_PRIMARY = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
BORDER_COLOR = "#1E293B"

class SupersonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"SUPERSONIC CLIENT v{VERSION}")
        self.geometry("1440x900")
        self.minsize(1280, 720)
        self.configure(fg_color=BG_COLOR)
        ctk.set_appearance_mode("dark")

        self.account_data = self.load_account()
        self.settings = self.load_settings()
        self.setup_directories()

        threading.Thread(target=self.check_for_updates, daemon=True).start()
        self.build_ui()

    def setup_directories(self):
        os.makedirs(MC_DIR, exist_ok=True)
        os.makedirs(MODS_DIR, exist_ok=True)

    def load_account(self):
        default = {"logged_in": True, "account_type": "Offline", "username": "Raffiee_playssMC", "uuid": str(uuid1()), "token": ""}
        if os.path.exists("auth.json"):
            try:
                with open("auth.json", "r") as f:
                    return json.load(f)
            except: pass
        return default

    def save_account(self):
        with open("auth.json", "w") as f:
            json.dump(self.account_data, f, indent=4)

    def load_settings(self):
        default = {
            "ram": 8192, 
            "advanced_jvm": "-XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M",
            "d3d12_wrapper": True, 
            "close_on_launch": True,
            "mc_version": "1.21.4",
            "mod_loader": "fabric"
        }
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    data = json.load(f)
                    default.update(data)
                    return default
            except: pass
        return default

    def save_settings(self):
        with open("settings.json", "w") as f:
            json.dump(self.settings, f, indent=4)

    def check_for_updates(self):
        try:
            res = requests.get(UPDATE_URL, timeout=5)
            if res.status_code == 200:
                print("Auto-update check successful.")
        except: pass

    def thread_safe_update(self, widget, **kwargs):
        self.after(0, lambda: widget.configure(**kwargs))

    def build_ui(self):
        # TOP BAR
        self.top_bar = ctk.CTkFrame(self, height=55, fg_color=BG_COLOR, corner_radius=0)
        self.top_bar.pack(side="top", fill="x")
        self.top_bar.pack_propagate(False)
        
        logo_f = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        logo_f.pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(logo_f, text="⚡", font=("Segoe UI", 24), text_color=ACCENT_BLUE).pack(side="left")
        ctk.CTkLabel(logo_f, text="SUPERSONIC", font=("Segoe UI", 20, "bold", "italic"), text_color=TEXT_PRIMARY).pack(side="left", padx=(10, 5))
        ctk.CTkLabel(logo_f, text=f"v{VERSION}", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(side="left", pady=(5,0))
        ctk.CTkLabel(self.top_bar, text="THE NEXT GENERATION MINECRAFT LAUNCHER", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(side="left", expand=True)
        
        # Window controls simulation
        win_ctrl = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        win_ctrl.pack(side="right", padx=15)
        for icon in ["—", "□", "✕"]:
            ctk.CTkLabel(win_ctrl, text=icon, font=("Segoe UI", 14), text_color=TEXT_MUTED).pack(side="left", padx=8)

        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=SIDEBAR_COLOR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "🏠"), ("Modpacks", "📦"), ("Addons", "🧩"), 
            ("Instances", "📂"), ("Servers", "🌐"), ("Resource Packs", "🎨"), 
            ("Worlds", "🌍"), ("Settings", "⚙️"), ("Agent (AI)", "🤖")
        ]
        
        nav_f = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_f.pack(fill="x", pady=10)
        
        for name, icon in nav_items:
            btn = ctk.CTkButton(
                nav_f, text=f"   {icon}    {name}", anchor="w", fg_color="transparent", 
                hover_color=CARD_HOVER, text_color=TEXT_PRIMARY, font=("Segoe UI", 14, "bold"), 
                height=45, corner_radius=8, command=lambda k=name.lower(): self.switch_tab(k)
            )
            btn.pack(fill="x", padx=15, pady=2)
            self.nav_buttons[name.lower()] = btn
            
            if name == "Addons":
                btn.configure(text=f"   {icon}    {name}               NEW")
            if name == "Agent (AI)":
                btn.configure(text=f"   {icon}    {name}                 AI")

        # ACCOUNT SECTION (Bottom Sidebar)
        acc_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        acc_frame.pack(side="bottom", fill="x", pady=20)
        
        links_f = ctk.CTkFrame(acc_frame, fg_color="transparent")
        links_f.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(links_f, text="🌐 Website", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(links_f, text="💬 Discord", font=("Segoe UI", 11), text_color=ACCENT_BLUE).pack(side="right")
        
        user_card = ctk.CTkFrame(acc_frame, fg_color=CARD_COLOR, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        user_card.pack(fill="x", padx=15)
        ctk.CTkLabel(user_card, text="Account", font=("Segoe UI", 10), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 0))
        self.lbl_acc_name = ctk.CTkLabel(user_card, text=self.account_data["username"], font=("Segoe UI", 14, "bold"), text_color=TEXT_PRIMARY)
        self.lbl_acc_name.pack(anchor="w", padx=15)
        ctk.CTkLabel(user_card, text=f"👑 Premium", font=("Segoe UI", 11, "bold"), text_color="#FBBF24").pack(anchor="w", padx=15, pady=(0, 10))

        # MAIN CONTENT
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(side="left", fill="both", expand=True, padx=20, pady=(0, 20))

        # RIGHT PANEL (Agent AI Sidebar for Dashboard)
        self.right_panel = ctk.CTkFrame(self, width=300, fg_color=SIDEBAR_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        
        self.switch_tab("dashboard")

    def switch_tab(self, tab_key):
        tab_key = tab_key.replace(" (ai)", "")
        for key, btn in self.nav_buttons.items():
            if key.replace(" (ai)", "") == tab_key:
                btn.configure(fg_color=CARD_HOVER, text_color=ACCENT_BLUE)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_PRIMARY)

        for widget in self.main_content.winfo_children(): widget.destroy()

        if tab_key == "dashboard":
            self.render_dashboard()
            self.right_panel.pack(side="right", fill="y", padx=(0, 20), pady=(0, 20))
            self.right_panel.pack_propagate(False)
            self.build_agent_sidebar()
        else:
            self.right_panel.pack_forget()
            if tab_key == "addons": self.render_addons()
            elif tab_key == "modpacks": self.render_modpacks()
            elif tab_key == "settings": self.render_settings()
            elif tab_key == "agent": self.render_agent_dashboard()
            else: self.render_placeholder(tab_key.title())

    def render_placeholder(self, title):
        ctk.CTkLabel(self.main_content, text=title, font=("Segoe UI", 28, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(self.main_content, text="Module currently under development.", font=("Segoe UI", 14), text_color=TEXT_MUTED).pack(anchor="w", pady=10)

    # ================= 1. DASHBOARD UI =================
    def render_dashboard(self):
        # HERO BANNER
        hero = ctk.CTkFrame(self.main_content, fg_color=CARD_COLOR, corner_radius=15, height=160, border_width=1, border_color=BORDER_COLOR)
        hero.pack(fill="x", pady=(0, 20))
        hero.pack_propagate(False)

        info_f = ctk.CTkFrame(hero, fg_color="transparent")
        info_f.pack(side="left", padx=30, pady=25, fill="y")
        ctk.CTkLabel(info_f, text="SUPERSONIC CLIENT", font=("Segoe UI", 28, "bold", "italic"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(info_f, text="Hyper optimized. Ultra fast. Future ready.", font=("Segoe UI", 14), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 10))
        
        tags_f = ctk.CTkFrame(info_f, fg_color="transparent")
        tags_f.pack(anchor="w")
        ctk.CTkLabel(tags_f, text="📦 Minecraft 1.21.4", font=("Segoe UI", 11, "bold"), text_color=TEXT_PRIMARY, fg_color=BG_COLOR, corner_radius=5).pack(side="left", padx=(0, 10), ipadx=8, ipady=4)
        ctk.CTkLabel(tags_f, text="🚀 Performance: Ultra", font=("Segoe UI", 11, "bold"), text_color=ACCENT_GREEN, fg_color=BG_COLOR, corner_radius=5).pack(side="left", padx=(0, 10), ipadx=8, ipady=4)
        ctk.CTkLabel(tags_f, text="📅 Last Played: Today", font=("Segoe UI", 11, "bold"), text_color="#A78BFA", fg_color=BG_COLOR, corner_radius=5).pack(side="left", ipadx=8, ipady=4)

        play_f = ctk.CTkFrame(hero, fg_color="transparent")
        play_f.pack(side="right", padx=30, pady=25)
        self.play_btn = ctk.CTkButton(play_f, text="▶ PLAY", font=("Segoe UI", 24, "bold"), fg_color=ACCENT_BLUE, hover_color=ACCENT_BLUE_HOVER, width=180, height=60, corner_radius=10, command=self.start_game_launch)
        self.play_btn.pack()
        self.launch_status = ctk.CTkLabel(play_f, text="Latest Release (1.21.4)", font=("Segoe UI", 11), text_color=TEXT_MUTED)
        self.launch_status.pack(pady=(5, 0))
        self.launch_progress = ctk.CTkProgressBar(play_f, width=180, height=5, progress_color=ACCENT_GREEN)
        self.launch_progress.set(0)

        # SECTIONS
        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ADDONS PREVIEW
        add_head = ctk.CTkFrame(scroll, fg_color="transparent")
        add_head.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(add_head, text="⚡", font=("Segoe UI", 20)).pack(side="left", padx=(0,10))
        ctk.CTkLabel(add_head, text="ALL ADDONS - ONE CLICK INSTALL\nAll essential addons. One click. Done.", font=("Segoe UI", 14, "bold"), justify="left").pack(side="left")
        ctk.CTkButton(add_head, text="📥 Install All", fg_color="transparent", border_width=1, border_color=BORDER_COLOR, text_color=TEXT_PRIMARY, width=100).pack(side="right")

        addons_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        addons_grid.pack(fill="x", pady=(0, 20))
        
        preview_mods = [("Sodium", "Boosts FPS", "🟢"), ("Iris Shaders", "Shaders Mod", "🌈"), ("Lithium", "Performance", "🔥"), 
                        ("Indium", "Better Mod Compat", "🔀"), ("Phosphor", "Lighting Engine", "☀️"), ("FerriteCore", "Memory Usage", "📦")]
        for i, (name, desc, icon) in enumerate(preview_mods):
            card = ctk.CTkFrame(addons_grid, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="nsew")
            addons_grid.grid_columnconfigure(i%3, weight=1)
            ctk.CTkLabel(card, text=icon, font=("Segoe UI", 24)).pack(side="left", padx=15, pady=15)
            tf = ctk.CTkFrame(card, fg_color="transparent")
            tf.pack(side="left", fill="both", expand=True, pady=10)
            ctk.CTkLabel(tf, text=name, font=("Segoe UI", 13, "bold")).pack(anchor="w")
            ctk.CTkLabel(tf, text=desc, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")
            ctk.CTkLabel(tf, text="✓ Installed", font=("Segoe UI", 10, "bold"), text_color=ACCENT_GREEN).pack(anchor="w")

        # MODPACKS PREVIEW
        mp_head = ctk.CTkFrame(scroll, fg_color="transparent")
        mp_head.pack(fill="x", pady=(10, 10))
        ctk.CTkLabel(mp_head, text="📦 MODPACKS", font=("Segoe UI", 16, "bold")).pack(side="left")
        ctk.CTkButton(mp_head, text="Browse All", fg_color="transparent", border_width=1, text_color=TEXT_PRIMARY, width=100).pack(side="right")

        mp_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        mp_grid.pack(fill="x")
        mp_list = [("Fabulously Optimized", "1.21.4", "Optimized for FPS"), ("Better MC", "1.21.4", "Vanilla+ Experience"), ("RLCraft", "1.20.1", "Hardcore Survival")]
        for i, (name, ver, tag) in enumerate(mp_list):
            card = ctk.CTkFrame(mp_grid, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            mp_grid.grid_columnconfigure(i, weight=1)
            img = ctk.CTkFrame(card, height=100, fg_color="#1E293B", corner_radius=8)
            img.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15)
            ctk.CTkLabel(card, text=ver, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=15)
            ctk.CTkButton(card, text="📥 Install", fg_color=ACCENT_BLUE, height=30).pack(fill="x", padx=15, pady=(10,5))
            ctk.CTkLabel(card, text=f"⚡ {tag}", font=("Segoe UI", 10), text_color="#FBBF24").pack(pady=(0,10))

        # BOTTOM METRICS
        bot_bar = ctk.CTkFrame(self.main_content, height=60, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        bot_bar.pack(side="bottom", fill="x", pady=(10, 0))
        bot_bar.pack_propagate(False)
        for label, val, p_val, color in [("RAM Usage", "3.2 GB / 8 GB", 0.4, ACCENT_BLUE), ("FPS Boost", "+120%", 0.8, ACCENT_GREEN), ("Ping", "24ms", 0.2, "#8B5CF6")]:
            f = ctk.CTkFrame(bot_bar, fg_color="transparent")
            f.pack(side="left", expand=True, fill="both", padx=20, pady=10)
            hf = ctk.CTkFrame(f, fg_color="transparent")
            hf.pack(fill="x")
            ctk.CTkLabel(hf, text=label, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(hf, text=val, font=("Segoe UI", 11, "bold")).pack(side="right")
            pb = ctk.CTkProgressBar(f, height=6, progress_color=color, fg_color=BG_COLOR)
            pb.pack(fill="x", pady=5)
            pb.set(p_val)

    def build_agent_sidebar(self):
        for w in self.right_panel.winfo_children(): w.destroy()
        
        head = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(head, text="AGENT (AI)", font=("Segoe UI", 14, "bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkLabel(head, text="BETA", fg_color=ACCENT_BLUE, font=("Segoe UI", 9, "bold"), corner_radius=4).pack(side="left", padx=5, ipadx=4)
        
        ctk.CTkLabel(self.right_panel, text="🤖", font=("Segoe UI", 80)).pack(pady=10)
        ctk.CTkLabel(self.right_panel, text="🟢 Agent Online", font=("Segoe UI", 12, "bold"), text_color=ACCENT_GREEN).pack()

        info = ctk.CTkFrame(self.right_panel, fg_color=BG_COLOR, corner_radius=10)
        info.pack(fill="x", padx=20, pady=20, ipady=10)
        ctk.CTkLabel(info, text=f"Hello {self.account_data['username']}! 👋\nI am your Supersonic Agent.", font=("Segoe UI", 13, "bold"), justify="left").pack(anchor="w", padx=15, pady=(10, 5))
        for feat in ["✓ Auto fix errors", "✓ Optimize performance", "✓ Detect crashes"]:
            ctk.CTkLabel(info, text=feat, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=15)

        ctk.CTkLabel(self.right_panel, text="Auto Fix (One Click)", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20)
        ctk.CTkLabel(self.right_panel, text="Detect and fix common issues", font=("Segoe UI", 10), text_color=TEXT_MUTED).pack(anchor="w", padx=20)
        ctk.CTkButton(self.right_panel, text="🛠️ Scan & Fix", fg_color="#4F46E5", hover_color="#4338CA", height=40).pack(fill="x", padx=20, pady=10)

        logs = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        logs.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(logs, text="Recent Logs", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        for l in ["[12:48] Fixed Java path issue ✓", "[12:46] Cleared cache ✓", "[12:43] Optimized RAM ✓"]:
            ctk.CTkLabel(logs, text=l, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")

        ctk.CTkEntry(self.right_panel, placeholder_text="Ask the Agent...", height=40, fg_color=BG_COLOR).pack(fill="x", side="bottom", padx=20, pady=20)

    # ================= 2. MODPACKS UI =================
    def render_modpacks(self):
        head = ctk.CTkFrame(self.main_content, fg_color="transparent")
        head.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(head, text="MODPACKS", font=("Segoe UI", 28, "bold", "italic")).pack(anchor="w")
        ctk.CTkLabel(head, text="Choose. Download. Play.", font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w")
        
        tabs = ctk.CTkFrame(self.main_content, fg_color="transparent")
        tabs.pack(fill="x", pady=(0, 15))
        for t in ["All Modpacks", "Popular", "New Releases", "Adventure", "Tech", "Magic"]:
            ctk.CTkLabel(tabs, text=t, font=("Segoe UI", 13, "bold"), text_color=ACCENT_BLUE if t=="All Modpacks" else TEXT_MUTED).pack(side="left", padx=(0, 20))
        
        split = ctk.CTkFrame(self.main_content, fg_color="transparent")
        split.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(split, fg_color="transparent")
        scroll.pack(side="left", fill="both", expand=True, padx=(0, 15))

        packs = [("Fabulously Optimized", "1.21.4", "12.4M", "4.8"), ("Better MC [FABRIC]", "1.21.4", "8.7M", "4.7"), 
                 ("RLCRAFT", "1.20.1", "6.2M", "4.4"), ("All the Mods 9", "1.20.1", "5.9M", "4.6"),
                 ("SkyFactory 5", "1.20.1", "5.1M", "4.6"), ("Prominence II RPG", "1.20.1", "4.3M", "4.5")]
        
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        for i, (name, ver, dl, rt) in enumerate(packs):
            card = ctk.CTkFrame(grid, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=i//3, column=i%3, padx=8, pady=8, sticky="nsew")
            grid.grid_columnconfigure(i%3, weight=1)
            img = ctk.CTkFrame(card, height=120, fg_color="#1E293B", corner_radius=10)
            img.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=15)
            ctk.CTkLabel(card, text=f"{ver} • by Creator", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=15)
            
            sf = ctk.CTkFrame(card, fg_color="transparent")
            sf.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(sf, text=f"↓ {dl}", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(sf, text=f"★ {rt}", font=("Segoe UI", 11), text_color="#FBBF24").pack(side="left", padx=10)
            ctk.CTkButton(card, text="📥 Install", fg_color="transparent", border_width=1, text_color=TEXT_PRIMARY).pack(fill="x", padx=15, pady=10)

        # Right Filters
        right = ctk.CTkFrame(split, width=260, fg_color="transparent")
        right.pack(side="right", fill="y")
        ctk.CTkEntry(right, placeholder_text="Search modpacks...", fg_color=CARD_COLOR, height=40).pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(right, text="FILTERS", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w")
        for lbl in ["Minecraft Version", "Mod Loader", "Categories"]:
            ctk.CTkLabel(right, text=lbl, font=("Segoe UI", 12)).pack(anchor="w", pady=(10, 2))
            ctk.CTkOptionMenu(right, values=["All Versions/Loaders"], fg_color=CARD_COLOR).pack(fill="x")

        # Bottom Bar
        bot = ctk.CTkFrame(self.main_content, height=60, fg_color=CARD_COLOR, corner_radius=10)
        bot.pack(side="bottom", fill="x", pady=10)
        bot.pack_propagate(False)
        for val in ["Total: 1,248", "Installed: 12", "Storage: 18.4 GB"]:
            ctk.CTkLabel(bot, text=val, font=("Segoe UI", 12, "bold")).pack(side="left", expand=True)

    # ================= 3. ADDONS UI (Modrinth Impl) =================
    def render_addons(self):
        head = ctk.CTkFrame(self.main_content, fg_color="transparent")
        head.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(head, text="ADDONS", font=("Segoe UI", 28, "bold", "italic")).pack(anchor="w")
        ctk.CTkLabel(head, text="All essential addons. One click install.", font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w")
        
        tabs = ctk.CTkFrame(self.main_content, fg_color="transparent")
        tabs.pack(fill="x", pady=(0, 15))
        for t in ["All Addons", "Performance", "Visuals", "Gameplay", "Utility", "World Gen", "Libraries"]:
            ctk.CTkLabel(tabs, text=t, font=("Segoe UI", 13, "bold"), text_color=ACCENT_BLUE if t=="All Addons" else TEXT_MUTED).pack(side="left", padx=(0, 15))

        split = ctk.CTkFrame(self.main_content, fg_color="transparent")
        split.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(split, fg_color="transparent")
        scroll.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Real Modrinth Slugs for fetching
        real_mods = [
            ("sodium", "Sodium", "Boosts FPS and reduces lag.", "🟢"),
            ("iris", "Iris Shaders", "Shaders mod for stunning visuals.", "🌈"),
            ("lithium", "Lithium", "Improves game performance.", "🔥"),
            ("indium", "Indium", "Better Mod Compatibility.", "🔀"),
            ("phosphor", "Phosphor", "Lighting engine improvements.", "☀️"),
            ("ferrite-core", "FerriteCore", "Reduces memory usage.", "📦"),
            ("entityculling", "Entity Culling", "Optimizes entity rendering.", "🎯"),
            ("immediatelyfast", "ImmediatelyFast", "Reduces CPU overhead.", "⚡")
        ]

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        self.addon_btns = {}
        for i, (slug, name, desc, icon) in enumerate(real_mods):
            card = ctk.CTkFrame(grid, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="nsew")
            grid.grid_columnconfigure(i%2, weight=1)
            
            ctk.CTkLabel(card, text=icon, font=("Segoe UI", 36)).pack(side="left", padx=15, pady=15)
            inf = ctk.CTkFrame(card, fg_color="transparent")
            inf.pack(side="left", fill="both", expand=True, pady=15)
            ctk.CTkLabel(inf, text=name, font=("Segoe UI", 15, "bold")).pack(anchor="w")
            ctk.CTkLabel(inf, text=desc, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")
            
            btn = ctk.CTkButton(card, text="Install", width=80, fg_color="transparent", border_width=1, border_color=ACCENT_BLUE, text_color=ACCENT_BLUE)
            btn.configure(command=lambda s=slug, b=btn: self.install_modrinth(s, b))
            btn.pack(side="right", padx=15)
            self.addon_btns[slug] = btn

        # Right Panel - Stats
        right = ctk.CTkFrame(split, width=260, fg_color="transparent")
        right.pack(side="right", fill="y")
        
        stat = ctk.CTkFrame(right, fg_color=CARD_COLOR, corner_radius=10, border_color=ACCENT_GREEN, border_width=1)
        stat.pack(fill="x", pady=(0, 15), ipady=10)
        ctk.CTkLabel(stat, text="All addons are up to date!", font=("Segoe UI", 12, "bold"), text_color=ACCENT_GREEN).pack(pady=(10,0))
        ctk.CTkLabel(stat, text="Your client is fully optimized.", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack()

        ctk.CTkEntry(right, placeholder_text="Search addons...", fg_color=CARD_COLOR).pack(fill="x", pady=15)
        
        cat_f = ctk.CTkFrame(right, fg_color="transparent")
        cat_f.pack(fill="x")
        ctk.CTkLabel(cat_f, text="Categories", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        for cat, num in [("All Categories", 32), ("Performance", 11), ("Visuals", 6), ("Gameplay", 6), ("Utility", 5)]:
            f = ctk.CTkFrame(cat_f, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=cat, font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(f, text=str(num), font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(side="right")

        # Bottom Performance Summary (Simulated Graphs)
        perf_f = ctk.CTkFrame(self.main_content, height=100, fg_color=CARD_COLOR, corner_radius=10)
        perf_f.pack(side="bottom", fill="x", pady=10)
        perf_f.pack_propagate(False)
        ctk.CTkLabel(perf_f, text="Performance Summary", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(10,0))
        bars = ctk.CTkFrame(perf_f, fg_color="transparent")
        bars.pack(fill="x", padx=20, pady=5)
        for val, lbl, c in [("+120%", "FPS Boost", ACCENT_BLUE), ("-35%", "RAM Usage", "#8B5CF6"), ("-28%", "CPU Usage", ACCENT_GREEN)]:
            bf = ctk.CTkFrame(bars, fg_color="transparent")
            bf.pack(side="left", expand=True, fill="both", padx=10)
            ctk.CTkLabel(bf, text=lbl, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")
            ctk.CTkLabel(bf, text=val, font=("Segoe UI", 20, "bold"), text_color=c).pack(anchor="w")

    def install_modrinth(self, slug, btn):
        btn.configure(state="disabled", text="Installing...")
        def task():
            try:
                ver = self.settings.get("mc_version", "1.21.4")
                url = f"https://api.modrinth.com/v2/project/{slug}/version"
                params = {'game_versions': f'["{ver}"]', 'loaders': '["fabric"]'}
                res = requests.get(url, params=params, timeout=10)
                if res.status_code == 200 and res.json():
                    file_data = res.json()[0]['files'][0]
                    file_url, filename = file_data['url'], file_data['filename']
                    
                    dl = requests.get(file_url, stream=True)
                    filepath = os.path.join(MODS_DIR, filename)
                    with open(filepath, 'wb') as f:
                        for chunk in dl.iter_content(8192): f.write(chunk)
                    self.thread_safe_update(btn, text="✓ Installed", text_color=ACCENT_GREEN, border_color=ACCENT_GREEN)
                else:
                    self.thread_safe_update(btn, text="Failed", text_color="red", state="normal")
            except Exception as e:
                print(f"Modrinth error: {e}")
                self.thread_safe_update(btn, text="Error", state="normal")
        threading.Thread(target=task, daemon=True).start()

    # ================= 4. SETTINGS UI =================
    def render_settings(self):
        head = ctk.CTkFrame(self.main_content, fg_color="transparent")
        head.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(head, text="SETTINGS", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        ctk.CTkButton(head, text="🔄 Reset to Default", fg_color="transparent", border_width=1, width=120).pack(side="right")
        
        tabs = ctk.CTkFrame(self.main_content, fg_color="transparent")
        tabs.pack(fill="x", pady=(0, 15))
        for t in ["General", "Performance", "Minecraft", "Launcher", "Updates", "Privacy", "Advanced"]:
            ctk.CTkLabel(tabs, text=t, font=("Segoe UI", 13, "bold"), text_color=ACCENT_BLUE if t=="General" else TEXT_MUTED).pack(side="left", padx=(0, 20))

        split = ctk.CTkFrame(self.main_content, fg_color="transparent")
        split.pack(fill="both", expand=True)
        scroll = ctk.CTkScrollableFrame(split, fg_color="transparent")
        scroll.pack(side="left", fill="both", expand=True, padx=(0, 15))

        def create_card(parent, title):
            c = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            c.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            ctk.CTkLabel(c, text=title, font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
            return c

        def add_item(parent, title, desc, widget_type="switch", options=None):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", padx=15, pady=8)
            tf = ctk.CTkFrame(f, fg_color="transparent")
            tf.pack(side="left")
            ctk.CTkLabel(tf, text=title, font=("Segoe UI", 12, "bold")).pack(anchor="w")
            ctk.CTkLabel(tf, text=desc, font=("Segoe UI", 10), text_color=TEXT_MUTED).pack(anchor="w")
            
            if widget_type == "switch":
                s = ctk.CTkSwitch(f, text="", progress_color=ACCENT_BLUE)
                s.select() # mock state
                s.pack(side="right")
            elif widget_type == "dropdown":
                ctk.CTkOptionMenu(f, values=options, fg_color=BG_COLOR, width=120).pack(side="right")
            elif widget_type == "button":
                ctk.CTkButton(f, text=options, fg_color="transparent", border_width=1, width=100).pack(side="right")

        # Row 1
        r1 = ctk.CTkFrame(scroll, fg_color="transparent")
        r1.pack(fill="x")
        c1 = create_card(r1, "GENERAL SETTINGS")
        add_item(c1, "Language", "Choose preferred language.", "dropdown", ["English"])
        add_item(c1, "Theme", "Choose preferred theme.", "dropdown", ["Dark (Default)"])
        add_item(c1, "Start with Windows", "Launch on system startup.", "switch")
        add_item(c1, "Minimize to Tray", "Close button minimizes app.", "switch")
        
        c2 = create_card(r1, "PERFORMANCE SETTINGS")
        add_item(c2, "Performance Mode", "Optimize launcher.", "dropdown", ["Ultra (Recommended)"])
        add_item(c2, "RAM Allocation", "Set default RAM.", "dropdown", ["8192 MB"])
        add_item(c2, "Preload Assets", "Preload games in background.", "switch")
        add_item(c2, "Smart Memory", "Clean memory when needed.", "switch")

        c3 = create_card(r1, "MINECRAFT SETTINGS")
        add_item(c3, "Default Java", "Select Java runtime.", "dropdown", ["Java 21"])
        add_item(c3, "Minecraft Folder", "Change .minecraft dir.", "button", "Open Folder")
        add_item(c3, "Auto Install Java", "Install recommended Java.", "switch")
        add_item(c3, "Use Native Libs", "For better performance.", "switch")

        # Row 2 (Auth + JVM)
        r2 = ctk.CTkFrame(scroll, fg_color="transparent")
        r2.pack(fill="x", pady=10)
        c4 = create_card(r2, "AUTHENTICATION")
        auth_f = ctk.CTkFrame(c4, fg_color="transparent")
        auth_f.pack(fill="x", padx=15, pady=10)
        self.off_user = ctk.CTkEntry(auth_f, placeholder_text="Offline Username", fg_color=BG_COLOR)
        self.off_user.insert(0, self.account_data["username"])
        self.off_user.pack(side="left", padx=(0, 10), fill="x", expand=True)
        ctk.CTkButton(auth_f, text="Set Offline", command=self.save_off_account, fg_color=CARD_HOVER, border_width=1).pack(side="left", padx=(0, 10))
        ctk.CTkButton(auth_f, text="Login Microsoft", fg_color=ACCENT_GREEN, hover_color="#059669", command=self.ms_login_mock).pack(side="left")

        c5 = create_card(r2, "ADVANCED JVM ARGUMENTS")
        self.jvm_text = ctk.CTkTextbox(c5, height=70, font=("Consolas", 12), fg_color=BG_COLOR)
        self.jvm_text.insert("1.0", self.settings.get("advanced_jvm", ""))
        self.jvm_text.pack(fill="x", padx=15, pady=(0, 15))

        # Right System Info
        right = ctk.CTkFrame(split, width=280, fg_color="transparent")
        right.pack(side="right", fill="y")
        sc = ctk.CTkFrame(right, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        sc.pack(fill="x", pady=(0,15))
        ctk.CTkLabel(sc, text="SYSTEM OVERVIEW", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 5))
        for k, v in [("OS", "Windows 11"), ("CPU", "Intel i5-12400F"), ("RAM", "16.0 GB"), ("GPU", "GTX 1650"), ("Storage", "512 GB SSD")]:
            f = ctk.CTkFrame(sc, fg_color="transparent")
            f.pack(fill="x", padx=15, pady=3)
            ctk.CTkLabel(f, text=k, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(f, text=v, font=("Segoe UI", 11, "bold")).pack(side="right")
        ctk.CTkButton(sc, text="〽 Run Diagnostics", fg_color="transparent", border_width=1, border_color=ACCENT_BLUE).pack(fill="x", padx=15, pady=15)

    def save_off_account(self):
        self.account_data["username"] = self.off_user.get() or "Player"
        self.save_account()
        self.lbl_acc_name.configure(text=self.account_data["username"])

    def ms_login_mock(self):
        # A mock implementation showing how you would trigger OAuth
        print("Initiating Microsoft OAuth Flow...")
        self.lbl_acc_name.configure(text="Microsoft User")

    # ================= 5. AGENT AI UI =================
    def render_agent_dashboard(self):
        head = ctk.CTkFrame(self.main_content, fg_color="transparent")
        head.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(head, text="AGENT (AI)", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        ctk.CTkLabel(head, text="BETA", fg_color=ACCENT_BLUE, font=("Segoe UI", 10, "bold"), corner_radius=5).pack(side="left", padx=10, ipadx=5)
        
        # Top Banner
        ban = ctk.CTkFrame(self.main_content, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        ban.pack(fill="x", pady=(0, 15), ipady=15)
        ctk.CTkLabel(ban, text="🤖", font=("Segoe UI", 80)).pack(side="left", padx=30)
        bf = ctk.CTkFrame(ban, fg_color="transparent")
        bf.pack(side="left", fill="y", pady=10)
        ctk.CTkLabel(bf, text=f"Hello {self.account_data['username']}! 👋", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ctk.CTkLabel(bf, text="I'm your Supersonic Agent.\nI can help you optimize, fix, and enhance your Minecraft experience.", font=("Segoe UI", 13), text_color=TEXT_MUTED, justify="left").pack(anchor="w", pady=(5,0))

        # Quick Actions Grid
        qa_f = ctk.CTkFrame(ban, fg_color="transparent")
        qa_f.pack(side="right", padx=30)
        ctk.CTkLabel(qa_f, text="QUICK ACTIONS", font=("Segoe UI", 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w")
        qa_grid = ctk.CTkFrame(qa_f, fg_color="transparent")
        qa_grid.pack()
        for i, (txt, icon) in enumerate([("Auto Fix Errors", "🛠️"), ("Optimize Perf", "🚀"), ("Clean Junk", "🧹"), ("Diagnose", "📊")]):
            b = ctk.CTkButton(qa_grid, text=f"{icon} {txt}", fg_color=BG_COLOR, hover_color=CARD_HOVER, border_width=1, border_color=BORDER_COLOR, width=140, height=40)
            b.grid(row=i//2, column=i%2, padx=5, pady=5)

        split = ctk.CTkFrame(self.main_content, fg_color="transparent")
        split.pack(fill="both", expand=True)

        left = ctk.CTkFrame(split, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Health Card
        hc = ctk.CTkFrame(left, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        hc.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(hc, text="SYSTEM HEALTH", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 0))
        h_split = ctk.CTkFrame(hc, fg_color="transparent")
        h_split.pack(fill="x", padx=15, pady=15)
        
        # Circular progress simulation
        circle = ctk.CTkFrame(h_split, width=100, height=100, fg_color="transparent", border_width=4, border_color=ACCENT_BLUE, corner_radius=50)
        circle.pack(side="left", padx=10)
        circle.pack_propagate(False)
        ctk.CTkLabel(circle, text="98%\nExcellent", font=("Segoe UI", 14, "bold"), text_color=ACCENT_BLUE).pack(expand=True)
        
        list_f = ctk.CTkFrame(h_split, fg_color="transparent")
        list_f.pack(side="left", padx=30)
        for t in ["Minecraft Files: Healthy", "Mods & Addons: Healthy", "Performance: Excellent", "Internet: Stable"]:
            ctk.CTkLabel(list_f, text=f"✓ {t}", font=("Segoe UI", 12, "bold"), text_color=ACCENT_GREEN).pack(anchor="w", pady=2)

        # Active Tasks
        at_card = ctk.CTkFrame(left, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        at_card.pack(fill="both", expand=True)
        ctk.CTkLabel(at_card, text="ACTIVE TASKS", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        for task, p in [("Scanning for Issues", 0.75), ("Optimizing Performance", 0.6), ("Cleaning Junk", 0.3)]:
            tf = ctk.CTkFrame(at_card, fg_color="transparent")
            tf.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(tf, text=task, font=("Segoe UI", 12, "bold")).pack(side="left")
            ctk.CTkProgressBar(tf, width=150, height=6, progress_color=ACCENT_BLUE).pack(side="right").set(p)

        # Right Chat
        chat = ctk.CTkFrame(split, width=350, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        chat.pack(side="right", fill="y")
        chat.pack_propagate(False)
        ctk.CTkLabel(chat, text="CHAT WITH AGENT", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(chat, text="Why is my game crashing?", fg_color=ACCENT_BLUE, corner_radius=10, padx=15, pady=10).pack(anchor="e", padx=15, pady=5)
        ans = "I've analyzed the crash report.\nProblem: Outdated mod 'Entity Culling'\nSolution: Update to v1.6.2"
        ctk.CTkLabel(chat, text=ans, fg_color=BG_COLOR, corner_radius=10, justify="left", padx=15, pady=10).pack(anchor="w", padx=15, pady=5)
        ctk.CTkButton(chat, text="🛠️ Apply Fix", fg_color="#4F46E5").pack(anchor="w", padx=15, pady=5)
        
        ctk.CTkEntry(chat, placeholder_text="Ask me anything...", height=40, fg_color=BG_COLOR).pack(side="bottom", fill="x", padx=15, pady=15)

    # ================= GAME LAUNCH ENGINE =================
    def start_game_launch(self):
        self.play_btn.configure(state="disabled", text="INSTALLING...")
        self.launch_progress.set(0)
        threading.Thread(target=self.game_launch_thread, daemon=True).start()

    def game_launch_thread(self):
        ver = self.settings.get("mc_version", "1.21.4")
        self.thread_safe_update(self.launch_status, text="Installing Assets & Libraries...")
        
        def update_prog(max_val, cur_val):
            val = cur_val / max_val if max_val > 0 else 0
            self.thread_safe_update(self.launch_progress, set=val)
            
        callback = {
            "setStatus": lambda s: self.thread_safe_update(self.launch_status, text=s),
            "setProgress": update_prog, "setMax": lambda m: None
        }
        
        try:
            # Install base vanilla version robustly
            minecraft_launcher_lib.install.install_minecraft_version(ver, MC_DIR, callback=callback)
        except Exception as e:
            err_msg = str(e)[:40] + "..." if len(str(e)) > 40 else str(e)
            print(f"Install failed:\n{traceback.format_exc()}")
            self.thread_safe_update(self.launch_status, text=f"Install Error: {err_msg}", text_color="red")
            self.thread_safe_update(self.play_btn, state="normal", text="▶ PLAY")
            return

        self.thread_safe_update(self.launch_status, text="Generating Launch Command...", text_color=TEXT_MUTED)
        options = {
            "username": self.account_data["username"],
            "uuid": self.account_data["uuid"],
            "token": self.account_data["token"]
        }
        
        # Proper JVM setup
        ram_mb = str(self.settings.get("ram", "8192"))
        jvm = [f"-Xmx{ram_mb}M", "-Xms2048M"]
        if hasattr(self, 'jvm_text'):
            jvm.extend(self.jvm_text.get("1.0", "end-1c").strip().split())
        else:
            jvm.extend(self.settings.get("advanced_jvm", "").split())
            
        if self.settings.get("d3d12_wrapper", True):
            jvm.append("-Dorg.lwjgl.opengl.libname=opengl32.dll")
            
        options["jvmArguments"] = jvm

        try:
            cmd = minecraft_launcher_lib.command.get_minecraft_command(ver, MC_DIR, options)
            self.thread_safe_update(self.launch_status, text="Launching Game...")
            
            # Hide launcher if configured
            if self.settings.get("close_on_launch", True):
                self.after(0, self.withdraw)

            if sys.platform == "win32":
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(cmd)
                
            self.after(0, self.reset_launch_ui)
        except Exception as e:
            print(f"Launch failed:\n{traceback.format_exc()}")
            self.thread_safe_update(self.launch_status, text="Launch Failed! Check Logs.", text_color="red")
            self.thread_safe_update(self.play_btn, state="normal", text="▶ PLAY")

    def reset_launch_ui(self):
        self.play_btn.configure(state="normal", text="▶ PLAY")
        self.launch_status.configure(text=f"Latest Release ({self.settings.get('mc_version', '1.21.4')})", text_color=TEXT_MUTED)
        self.launch_progress.set(0)

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
