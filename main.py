import os
import sys
import json
import time
import threading
import subprocess
import requests
import customtkinter as ctk
import minecraft_launcher_lib
from uuid import uuid1
import traceback

# --- CONFIGURATION & CONSTANTS ---
VERSION = "2.5.0"
UPDATE_URL = "https://supersonic-client--greeko2030.replit.app/api/version"
MC_DIR = minecraft_launcher_lib.utils.get_minecraft_directory().replace("minecraft", "supersonic")
MODS_DIR = os.path.join(MC_DIR, "mods")
CLIENT_ID = "YOUR_MICROSOFT_CLIENT_ID" # Replace with your Azure App ID

# Custom Color Palette (Matching the futuristic dark theme images)
BG_COLOR = "#070B14"
SIDEBAR_COLOR = "#0B111F"
CARD_COLOR = "#121A2F"
CARD_HOVER = "#1A2542"
ACCENT_BLUE = "#1D4ED8"
ACCENT_BLUE_HOVER = "#2563EB"
ACCENT_GREEN = "#10B981"
TEXT_PRIMARY = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
BORDER_COLOR = "#1E293B"

class SupersonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"SUPERSONIC CLIENT v{VERSION} - THE NEXT GENERATION MINECRAFT LAUNCHER")
        self.geometry("1440x900")
        self.minsize(1280, 720)
        self.configure(fg_color=BG_COLOR)

        self.account_data = self.load_account()
        self.settings = self.load_settings()
        self.setup_directories()

        # Background Auto-Update Check
        threading.Thread(target=self.check_for_updates, daemon=True).start()

        # Build UI Structure
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
            except:
                pass
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
            "mod_loader": "fabric",
            "preload_assets": True,
            "smart_memory": True,
            "native_libraries": True,
            "auto_install_java": True
        }
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    data = json.load(f)
                    default.update(data)
                    return default
            except:
                pass
        return default

    def save_settings(self):
        with open("settings.json", "w") as f:
            json.dump(self.settings, f, indent=4)

    def check_for_updates(self):
        try:
            response = requests.get(UPDATE_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("version", VERSION) > VERSION:
                    print(f"Update available: {data.get('version')}")
                    # Could trigger an in-app notification here
        except Exception as e:
            print("Auto-update check failed:", e)

    def thread_safe_update(self, widget, **kwargs):
        """Helper to update UI elements safely from background threads"""
        self.after(0, lambda: widget.configure(**kwargs))

    def build_ui(self):
        # Top Bar (Simulating custom title bar as seen in pics)
        self.top_bar = ctk.CTkFrame(self, height=50, fg_color=BG_COLOR, corner_radius=0)
        self.top_bar.pack(side="top", fill="x")
        self.top_bar.pack_propagate(False)
        
        # Logo in top bar
        ctk.CTkLabel(self.top_bar, text="SUPERSONIC", font=("Segoe UI", 22, "bold", "italic"), text_color=TEXT_PRIMARY).pack(side="left", padx=(20, 5), pady=10)
        ctk.CTkLabel(self.top_bar, text="CLIENT", font=("Segoe UI", 12, "bold"), text_color=ACCENT_BLUE).pack(side="left", pady=15)
        ctk.CTkLabel(self.top_bar, text=f"v{VERSION}", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(side="left", padx=15, pady=15)
        
        ctk.CTkLabel(self.top_bar, text="THE NEXT GENERATION MINECRAFT LAUNCHER", font=("Segoe UI", 12, "italic"), text_color=TEXT_MUTED).pack(side="left", expand=True)

        # 1. Sidebar (Left)
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=SIDEBAR_COLOR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "🏠"), ("Modpacks", "📦"), ("Addons", "⚡"), 
            ("Instances", "📂"), ("Servers", "🌐"), ("Resource Packs", "🎨"), 
            ("Worlds", "🌍"), ("Settings", "⚙️"), ("Agent (AI)", "🤖")
        ]
        
        ctk.CTkFrame(self.sidebar, height=20, fg_color="transparent").pack() # Spacer
        
        for name, icon in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icon}   {name}", anchor="w", fg_color="transparent", 
                hover_color=CARD_HOVER, text_color=TEXT_PRIMARY, font=("Segoe UI", 14), 
                height=45, corner_radius=8, command=lambda k=name.lower(): self.switch_tab(k)
            )
            btn.pack(fill="x", padx=15, pady=3)
            self.nav_buttons[name.lower()] = btn

        # Bottom Sidebar (Account + Links)
        bottom_sidebar = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_sidebar.pack(side="bottom", fill="x", pady=20)

        # Social Links (Discord, Web, Github)
        links_frame = ctk.CTkFrame(bottom_sidebar, fg_color="transparent")
        links_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(links_frame, text="🌐 Website", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(side="left")
        ctk.CTkLabel(links_frame, text="💬 Discord", font=("Segoe UI", 11), text_color=ACCENT_BLUE).pack(side="right")

        # Account Card
        acc_frame = ctk.CTkFrame(bottom_sidebar, fg_color=CARD_COLOR, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        acc_frame.pack(fill="x", padx=15)
        ctk.CTkLabel(acc_frame, text="Account", font=("Segoe UI", 10), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 0))
        self.lbl_acc_name = ctk.CTkLabel(acc_frame, text=self.account_data["username"], font=("Segoe UI", 14, "bold"), text_color=TEXT_PRIMARY)
        self.lbl_acc_name.pack(anchor="w", padx=15)
        ctk.CTkLabel(acc_frame, text=f"👑 Premium ({self.account_data['account_type']})", font=("Segoe UI", 11), text_color="#FBBF24").pack(anchor="w", padx=15, pady=(0, 10))

        # 2. Main Content Area (Center)
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(side="left", fill="both", expand=True, padx=20, pady=(0, 20))

        # 3. Right Panel (Agent AI / Context)
        self.right_panel = ctk.CTkFrame(self, width=320, fg_color=SIDEBAR_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        
        # Initialize Default Tab
        self.switch_tab("dashboard")

    def build_right_panel_agent_compact(self):
        # AI Assistant Sidebar Profile (Dashboard view)
        for w in self.right_panel.winfo_children(): w.destroy()
        
        header = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text="AGENT (AI)", font=("Segoe UI", 14, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(header, text="Your personal AI assistant", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")

        bot_card = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        bot_card.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(bot_card, text="🤖", font=("Segoe UI", 80)).pack()
        ctk.CTkLabel(bot_card, text="🟢 Agent Online", font=("Segoe UI", 12), text_color=ACCENT_GREEN).pack()

        chat_box = ctk.CTkFrame(self.right_panel, fg_color=CARD_COLOR, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        chat_box.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(chat_box, text=f"Hello {self.account_data['username']}! 👋\nI am your Supersonic Agent.", font=("Segoe UI", 13, "bold"), text_color=TEXT_PRIMARY, justify="left").pack(anchor="w", padx=15, pady=(15, 5))
        features = ["✓ Auto fix errors", "✓ Optimize performance", "✓ Detect crashes", "✓ Suggest solutions"]
        for f in features:
            ctk.CTkLabel(chat_box, text=f, justify="left", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(anchor="w", padx=15)

        ctk.CTkLabel(self.right_panel, text="Auto Fix (One Click)", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(10, 0))
        ctk.CTkButton(self.right_panel, text="✨ Scan & Fix", fg_color="#4F46E5", hover_color="#4338CA", height=40).pack(fill="x", padx=20, pady=10)

        # Recent Logs snippet
        log_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        log_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(log_frame, text="Recent Logs", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        logs = ["[12:48] Fixed Java path issue ✓", "[12:46] Cleared corrupted cache ✓", "[12:43] Optimized memory ✓"]
        for l in logs:
            ctk.CTkLabel(log_frame, text=l, font=("Segoe UI", 10), text_color=TEXT_MUTED).pack(anchor="w")

        # Chat Input Area
        chat_in = ctk.CTkEntry(self.right_panel, placeholder_text="Ask the Agent...", height=40, fg_color=CARD_COLOR)
        chat_in.pack(fill="x", padx=20, side="bottom", pady=20)

    def switch_tab(self, tab_key):
        tab_key = tab_key.replace(" (ai)", "") # Handle 'agent' vs 'agent (ai)'
        
        # Update button highlights
        for key, btn in self.nav_buttons.items():
            if key.replace(" (ai)", "") == tab_key:
                btn.configure(fg_color=CARD_COLOR, text_color=ACCENT_BLUE)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_PRIMARY)

        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()

        # Route to rendering functions
        if tab_key == "dashboard":
            self.render_dashboard()
            self.right_panel.pack(side="right", fill="y", padx=(0, 20), pady=(0, 20))
            self.right_panel.pack_propagate(False)
            self.build_right_panel_agent_compact()
        elif tab_key == "addons":
            self.render_addons()
            self.right_panel.pack_forget()
        elif tab_key == "modpacks":
            self.render_modpacks()
            self.right_panel.pack_forget()
        elif tab_key == "settings":
            self.render_settings()
            self.right_panel.pack_forget()
        elif tab_key == "agent":
            self.render_agent_dashboard()
            self.right_panel.pack_forget()
        else:
            self.render_placeholder(tab_key.title())

    def render_placeholder(self, title):
        ctk.CTkLabel(self.main_content, text=title.upper(), font=("Segoe UI", 28, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(self.main_content, text="Module currently under development.", font=("Segoe UI", 14), text_color=TEXT_MUTED).pack(anchor="w", pady=10)

    # ================= DASHBOARD UI =================
    def render_dashboard(self):
        # Hero Banner
        hero = ctk.CTkFrame(self.main_content, fg_color="transparent")
        hero.pack(fill="x", pady=(0, 15))
        
        banner_bg = ctk.CTkFrame(hero, fg_color=CARD_COLOR, corner_radius=15, height=180, border_width=1, border_color=BORDER_COLOR)
        banner_bg.pack(fill="x", expand=True)
        banner_bg.pack_propagate(False)

        info_frame = ctk.CTkFrame(banner_bg, fg_color="transparent")
        info_frame.pack(side="left", padx=30, pady=30, fill="y", expand=True)
        ctk.CTkLabel(info_frame, text="SUPERSONIC CLIENT", font=("Segoe UI", 32, "bold", "italic"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(info_frame, text="Hyper optimized. Ultra fast. Future ready.", font=("Segoe UI", 14), text_color=TEXT_MUTED).pack(anchor="w", pady=(5, 15))
        
        tags = ctk.CTkFrame(info_frame, fg_color="transparent")
        tags.pack(anchor="w")
        ctk.CTkLabel(tags, text="📦 Minecraft 1.21.4", font=("Segoe UI", 12), text_color=TEXT_PRIMARY, fg_color=BG_COLOR, corner_radius=5).pack(side="left", padx=(0, 10), ipadx=8, ipady=4)
        ctk.CTkLabel(tags, text="🚀 Performance: Ultra", font=("Segoe UI", 12), text_color=ACCENT_GREEN, fg_color=BG_COLOR, corner_radius=5).pack(side="left", padx=(0, 10), ipadx=8, ipady=4)
        ctk.CTkLabel(tags, text="📅 Last Played: Today", font=("Segoe UI", 12), text_color="#A78BFA", fg_color=BG_COLOR, corner_radius=5).pack(side="left", ipadx=8, ipady=4)

        # Launch Button Area
        play_frame = ctk.CTkFrame(banner_bg, fg_color="transparent")
        play_frame.pack(side="right", padx=30, pady=30)
        
        self.play_btn = ctk.CTkButton(play_frame, text="▶ LAUNCH", font=("Segoe UI", 20, "bold"), fg_color=ACCENT_BLUE, hover_color=ACCENT_BLUE_HOVER, width=200, height=55, corner_radius=8, command=self.start_game_launch)
        self.play_btn.pack()
        
        self.launch_status = ctk.CTkLabel(play_frame, text="Latest Release (1.21.4)", font=("Segoe UI", 11), text_color=TEXT_MUTED)
        self.launch_status.pack(pady=(5, 0))
        self.launch_progress = ctk.CTkProgressBar(play_frame, width=200, height=5, progress_color=ACCENT_BLUE)
        self.launch_progress.set(0)

        # Quick Addons Frame
        addons_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        addons_frame.pack(fill="x", pady=10)
        
        header_add = ctk.CTkFrame(addons_frame, fg_color="transparent")
        header_add.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header_add, text="⚡ ALL ADDONS - ONE CLICK INSTALL", font=("Segoe UI", 14, "bold")).pack(side="left")
        ctk.CTkButton(header_add, text="📥 Install All", fg_color="transparent", border_width=1, border_color=BORDER_COLOR, text_color=TEXT_PRIMARY, width=100).pack(side="right")

        grid = ctk.CTkFrame(addons_frame, fg_color="transparent")
        grid.pack(fill="x")
        
        mods = [
            ("Sodium", "Boosts FPS", "#10B981"), ("Iris Shaders", "Shaders Mod", "#3B82F6"), 
            ("Lithium", "Performance", "#8B5CF6"), ("Indium", "Better Mod Compat", "#8B5CF6"),
            ("Phosphor", "Lighting Engine", "#F59E0B"), ("FerriteCore", "Memory Usage", "#10B981")
        ]
        
        for i, (name, desc, color) in enumerate(mods):
            row = i // 3
            col = i % 3
            card = ctk.CTkFrame(grid, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            grid.grid_columnconfigure(col, weight=1)
            
            # Simple icon simulation
            ctk.CTkLabel(card, text="⚙️", font=("Segoe UI", 24), text_color=color).pack(side="left", padx=15, pady=15)
            
            text_frame = ctk.CTkFrame(card, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True, pady=15)
            ctk.CTkLabel(text_frame, text=name, font=("Segoe UI", 14, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
            ctk.CTkLabel(text_frame, text=desc, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")
            ctk.CTkLabel(text_frame, text="✓ Installed", font=("Segoe UI", 10), text_color=ACCENT_GREEN).pack(anchor="w", pady=(5,0))

        # Bottom Status Bar (RAM, FPS, Ping)
        status_bar = ctk.CTkFrame(self.main_content, height=60, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        status_bar.pack(side="bottom", fill="x", pady=10)
        status_bar.pack_propagate(False)
        
        metrics = [("RAM Usage", "3.2 GB / 8 GB", "#3B82F6"), ("FPS Boost", "+120%", "#10B981"), ("Ping", "24ms", "#8B5CF6")]
        for i, (label, val, color) in enumerate(metrics):
            frame = ctk.CTkFrame(status_bar, fg_color="transparent")
            frame.pack(side="left", expand=True, fill="both", padx=20, pady=10)
            ctk.CTkLabel(frame, text=label, font=("Segoe UI", 12), text_color=color).pack(side="left", anchor="nw")
            ctk.CTkLabel(frame, text=val, font=("Segoe UI", 12, "bold")).pack(side="right", anchor="ne")

    # ================= ADDONS / MODRINTH DOWNLOADER =================
    def render_addons(self):
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="ADDONS", font=("Segoe UI", 28, "bold", "italic")).pack(anchor="w")
        ctk.CTkLabel(header, text="All essential addons. One click install.", font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w")
        
        # Tabs mock
        tabs_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        tabs_frame.pack(fill="x", pady=(0, 15))
        for t in ["All Addons", "Performance", "Visuals", "Gameplay", "Utility"]:
            color = ACCENT_BLUE if t == "All Addons" else TEXT_MUTED
            ctk.CTkLabel(tabs_frame, text=t, font=("Segoe UI", 14, "bold"), text_color=color).pack(side="left", padx=(0, 20))

        content_split = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content_split.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(content_split, fg_color="transparent")
        scroll.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # Real Modrinth Slugs & Project IDs for functional downloading
        mods_list = [
            ("sodium", "Sodium", "Boosts FPS and reduces lag.", "mcwro6nW"),
            ("iris", "Iris Shaders", "Shaders mod for stunning visuals.", "YL57xq9U"),
            ("lithium", "Lithium", "Improves game performance.", "gvQqBUqZ"),
            ("indium", "Indium", "Better Mod Compatibility.", "Orvt0mRa"),
            ("phosphor", "Phosphor", "Lighting engine improvements.", "hEOCdEQW"),
            ("ferrite-core", "FerriteCore", "Reduces memory usage.", "uXXMubvO")
        ]

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        
        for i, (slug, name, desc, project_id) in enumerate(mods_list):
            row = i // 2
            col = i % 2
            card = ctk.CTkFrame(grid, fg_color=CARD_COLOR, corner_radius=10, height=100, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            card.grid_propagate(False)
            grid.grid_columnconfigure(col, weight=1)
            
            ctk.CTkLabel(card, text="📦", font=("Segoe UI", 30)).pack(side="left", padx=15)
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, pady=10)
            ctk.CTkLabel(info, text=name, font=("Segoe UI", 15, "bold")).pack(anchor="w")
            ctk.CTkLabel(info, text=desc, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")
            
            btn = ctk.CTkButton(card, text="Install", width=70, fg_color="transparent", border_width=1, border_color=ACCENT_BLUE, text_color=ACCENT_BLUE,
                                command=lambda s=slug, p=project_id, b=None: self.download_modrinth_thread(s, p))
            btn.pack(side="right", padx=15)

        # Right sidebar info (Stats & Filters)
        right = ctk.CTkFrame(content_split, width=250, fg_color="transparent")
        right.pack(side="right", fill="y")
        
        stat_box = ctk.CTkFrame(right, fg_color=CARD_COLOR, corner_radius=10, border_color=ACCENT_GREEN, border_width=1)
        stat_box.pack(fill="x", pady=(0, 15), ipady=10)
        ctk.CTkLabel(stat_box, text="All addons are up to date!", font=("Segoe UI", 12, "bold"), text_color=ACCENT_GREEN).pack(pady=(10,0))
        ctk.CTkLabel(stat_box, text="Your client is fully optimized.", font=("Segoe UI", 10), text_color=TEXT_MUTED).pack()

        search = ctk.CTkEntry(right, placeholder_text="Search addons...", fg_color=BG_COLOR)
        search.pack(fill="x", pady=15)

        ctk.CTkLabel(right, text="Categories", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        for cat, cnt in [("All Categories", 32), ("Performance", 11), ("Visuals", 6), ("Gameplay", 6)]:
            f = ctk.CTkFrame(right, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=cat, font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(f, text=str(cnt), font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(side="right")

    def download_modrinth_thread(self, slug, project_id):
        def task():
            try:
                print(f"Fetching Modrinth API for {slug}...")
                version = self.settings.get("mc_version", "1.21.4")
                loader = self.settings.get("mod_loader", "fabric")
                
                # Using requests instead of urllib for better reliability
                url = f"https://api.modrinth.com/v2/project/{project_id}/version"
                params = {'game_versions': f'["{version}"]', 'loaders': f'["{loader}"]'}
                headers = {'User-Agent': 'SupersonicClient/2.5.0 (contact@supersonic.app)'}
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                if response.status_code != 200 or not response.json():
                    print(f"No compatible version found for {slug}")
                    return
                
                data = response.json()
                download_url = data[0]['files'][0]['url']
                filename = data[0]['files'][0]['filename']
                filepath = os.path.join(MODS_DIR, filename)
                
                print(f"Downloading {filename}...")
                dl_res = requests.get(download_url, stream=True)
                with open(filepath, 'wb') as f:
                    for chunk in dl_res.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Successfully installed {filename}!")
                # UI Update can be done here to change button to "Installed"
            except Exception as e:
                print(f"Failed to download {slug}:")
                traceback.print_exc()
        
        threading.Thread(target=task, daemon=True).start()

    # ================= MODPACKS UI =================
    def render_modpacks(self):
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="MODPACKS", font=("Segoe UI", 28, "bold", "italic")).pack(anchor="w")
        
        top_bar = ctk.CTkFrame(self.main_content, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 15))
        tabs = ["All Modpacks", "Popular", "New Releases", "Adventure", "Tech", "Magic"]
        for t in tabs:
            color = ACCENT_BLUE if t == "All Modpacks" else TEXT_MUTED
            ctk.CTkLabel(top_bar, text=t, font=("Segoe UI", 13, "bold"), text_color=color).pack(side="left", padx=(0, 15))
        
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(fill="both", expand=True)

        scroll = ctk.CTkScrollableFrame(content, fg_color="transparent")
        scroll.pack(side="left", fill="both", expand=True)

        packs = [
            ("Fabulously Optimized", "1.21.4", "Performance", "12.4M", "★ 4.8"),
            ("Better MC [FABRIC]", "1.21.4", "Vanilla+", "8.7M", "★ 4.7"),
            ("RLCRAFT", "1.12.2", "Hardcore", "6.2M", "★ 4.4"),
            ("All the Mods 9", "1.20.1", "Tech", "5.9M", "★ 4.6"),
            ("SkyFactory 5", "1.20.1", "Skyblock", "5.1M", "★ 4.6"),
            ("Prominence II RPG", "1.20.1", "RPG", "4.3M", "★ 4.5")
        ]
        
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        
        for i, (name, ver, tag, dl, rating) in enumerate(packs):
            row = i // 3
            col = i % 3
            card = ctk.CTkFrame(grid, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            grid.grid_columnconfigure(col, weight=1)
            
            # Dummy Image placeholder
            img = ctk.CTkFrame(card, height=120, fg_color="#1E293B", corner_radius=10)
            img.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(img, text="🖼️", font=("Segoe UI", 40)).pack(expand=True)
            
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=15)
            ctk.CTkLabel(card, text=f"{ver} • by Author", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=15)
            
            tags_f = ctk.CTkFrame(card, fg_color="transparent")
            tags_f.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(tags_f, text=tag, font=("Segoe UI", 10), fg_color=BG_COLOR, corner_radius=5).pack(side="left", ipadx=5)
            
            stats_f = ctk.CTkFrame(card, fg_color="transparent")
            stats_f.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(stats_f, text=f"↓ {dl}", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(stats_f, text=rating, font=("Segoe UI", 11), text_color="#FBBF24").pack(side="left", padx=10)

            ctk.CTkButton(card, text="📥 Install", fg_color="transparent", border_width=1, border_color=ACCENT_BLUE, text_color=TEXT_PRIMARY).pack(fill="x", padx=15, pady=15)

        # Right Filter Panel
        right = ctk.CTkFrame(content, width=250, fg_color="transparent")
        right.pack(side="right", fill="y", padx=(15, 0))
        
        ctk.CTkEntry(right, placeholder_text="Search modpacks...", fg_color=BG_COLOR).pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(right, text="FILTERS", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w")
        
        for lbl in ["Minecraft Version", "Mod Loader", "Categories"]:
            ctk.CTkLabel(right, text=lbl, font=("Segoe UI", 12)).pack(anchor="w", pady=(10, 2))
            ctk.CTkOptionMenu(right, values=["All", "Fabric", "Forge"], fg_color=CARD_COLOR).pack(fill="x")

        # Bottom Stats Bar
        stats_bottom = ctk.CTkFrame(self.main_content, height=50, fg_color=CARD_COLOR, corner_radius=10)
        stats_bottom.pack(side="bottom", fill="x", pady=10)
        
        for icon, lbl, val in [("📦", "Total Modpacks", "1,248"), ("📥", "Installed", "12"), ("💾", "Storage Used", "18.4 GB")]:
            f = ctk.CTkFrame(stats_bottom, fg_color="transparent")
            f.pack(side="left", expand=True, pady=10)
            ctk.CTkLabel(f, text=icon, font=("Segoe UI", 16)).pack(side="left", padx=5)
            ctk.CTkLabel(f, text=f"{lbl}\n{val}", font=("Segoe UI", 10), justify="left").pack(side="left")

    # ================= SETTINGS =================
    def render_settings(self):
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="SETTINGS", font=("Segoe UI", 28, "bold", "italic")).pack(anchor="w")
        ctk.CTkLabel(header, text="Customize your experience.", font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w")
        
        tabs_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        tabs_frame.pack(fill="x", pady=(0, 15))
        for t in ["General", "Performance", "Minecraft", "Launcher", "Updates", "Privacy", "Advanced"]:
            color = ACCENT_BLUE if t == "General" else TEXT_MUTED
            ctk.CTkLabel(tabs_frame, text=t, font=("Segoe UI", 14, "bold"), text_color=color).pack(side="left", padx=(0, 20))

        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(fill="both", expand=True)
        
        scroll = ctk.CTkScrollableFrame(content, fg_color="transparent")
        scroll.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Helper to create settings blocks
        def create_block(parent, title):
            block = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            block.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            ctk.CTkLabel(block, text=title, font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
            return block
        
        def add_toggle(parent, title, desc, var_name):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", padx=15, pady=8)
            txt = ctk.CTkFrame(f, fg_color="transparent")
            txt.pack(side="left")
            ctk.CTkLabel(txt, text=title, font=("Segoe UI", 13, "bold")).pack(anchor="w")
            ctk.CTkLabel(txt, text=desc, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")
            switch = ctk.CTkSwitch(f, text="")
            if self.settings.get(var_name, False): switch.select()
            switch.pack(side="right")

        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x")
        
        # Block 1: General
        b1 = create_block(row1, "GENERAL SETTINGS")
        add_toggle(b1, "Start with Windows", "Launch on system startup.", "start_windows")
        add_toggle(b1, "Minimize to System Tray", "Close button minimizes app.", "min_tray")

        # Block 2: Performance
        b2 = create_block(row1, "PERFORMANCE SETTINGS")
        
        ram_f = ctk.CTkFrame(b2, fg_color="transparent")
        ram_f.pack(fill="x", padx=15, pady=8)
        self.ram_lbl = ctk.CTkLabel(ram_f, text=f"RAM Allocation: {self.settings['ram']} MB", font=("Segoe UI", 13, "bold"))
        self.ram_lbl.pack(anchor="w")
        self.ram_slider = ctk.CTkSlider(b2, from_=2048, to=16384, number_of_steps=14, command=lambda v: self.ram_lbl.configure(text=f"RAM Allocation: {int(v)} MB"))
        self.ram_slider.set(int(self.settings.get("ram", 8192)))
        self.ram_slider.pack(fill="x", padx=15, pady=5)

        add_toggle(b2, "Direct3D12 Translation Wrapper", "Boosts FPS significantly.", "d3d12_wrapper")
        add_toggle(b2, "Smart Memory Management", "Clean memory when needed.", "smart_memory")

        # Block 3: Minecraft
        b3 = create_block(row1, "MINECRAFT SETTINGS")
        add_toggle(b3, "Automatically Install Java", "Install recommended Java.", "auto_install_java")
        add_toggle(b3, "Use Native Libraries", "For better performance.", "native_libraries")
        
        # Advanced JVM Arguments (Full span row)
        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", pady=10)
        jvm_b = create_block(row2, "ADVANCED JVM ARGUMENTS")
        self.jvm_text = ctk.CTkTextbox(jvm_b, height=60, font=("Consolas", 12), fg_color=BG_COLOR)
        self.jvm_text.insert("1.0", self.settings.get("advanced_jvm", ""))
        self.jvm_text.pack(fill="x", padx=15, pady=(0, 15))

        # Authentication Section (Offline + MS)
        auth_b = create_block(row2, "ACCOUNT & AUTHENTICATION")
        auth_f = ctk.CTkFrame(auth_b, fg_color="transparent")
        auth_f.pack(fill="x", padx=15, pady=10)
        
        self.off_user = ctk.CTkEntry(auth_f, placeholder_text="Offline Username", width=200, fg_color=BG_COLOR)
        self.off_user.insert(0, self.account_data["username"] if self.account_data["account_type"]=="Offline" else "")
        self.off_user.pack(side="left", padx=(0, 10))
        ctk.CTkButton(auth_f, text="Set Offline", command=self.set_offline_account, fg_color=CARD_HOVER, border_width=1).pack(side="left", padx=(0, 20))
        
        ctk.CTkButton(auth_f, text="Login with Microsoft", fg_color=ACCENT_GREEN, hover_color="#059669").pack(side="left")

        # Save Button
        ctk.CTkButton(scroll, text="💾 Save All Settings", font=("Segoe UI", 14, "bold"), height=45, command=self.save_all_settings).pack(anchor="w", pady=20, padx=5)

        # Right Panel: System Overview
        right = ctk.CTkFrame(content, width=280, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        
        ctk.CTkLabel(right, text="SYSTEM OVERVIEW", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(20, 10))
        sys_info = [("OS", "Windows 11 64-bit"), ("CPU", "Intel Core i5-12400F"), ("RAM", "16.0 GB"), ("GPU", "NVIDIA GTX 1650"), ("Storage", "512 GB SSD")]
        for lbl, val in sys_info:
            f = ctk.CTkFrame(right, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(f, text=lbl, font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(f, text=val, font=("Segoe UI", 12)).pack(side="right")
            
        ctk.CTkButton(right, text="〽 Run Diagnostics", fg_color="transparent", border_width=1, border_color=ACCENT_BLUE).pack(fill="x", padx=20, pady=20)

    def set_offline_account(self):
        uname = self.off_user.get().strip() or "Player"
        self.account_data.update({"account_type": "Offline", "username": uname})
        self.save_account()
        self.lbl_acc_name.configure(text=uname)
        print("Offline account saved.")

    def save_all_settings(self):
        self.settings["ram"] = int(self.ram_slider.get())
        self.settings["advanced_jvm"] = self.jvm_text.get("1.0", "end-1c").strip()
        self.save_settings()
        print("Settings saved.")

    # ================= AGENT AI =================
    def render_agent_dashboard(self):
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="AGENT (AI)", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        ctk.CTkLabel(header, text="BETA", fg_color=ACCENT_BLUE, corner_radius=5, font=("Segoe UI", 10)).pack(side="left", padx=10, ipadx=5)
        
        top_row = ctk.CTkFrame(self.main_content, fg_color="transparent")
        top_row.pack(fill="x", pady=10)
        
        # Profile & System Health
        prof_card = ctk.CTkFrame(top_row, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        prof_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        f = ctk.CTkFrame(prof_card, fg_color="transparent")
        f.pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(f, text="🤖", font=("Segoe UI", 60)).pack()
        
        f2 = ctk.CTkFrame(prof_card, fg_color="transparent")
        f2.pack(side="left", padx=10, pady=20)
        ctk.CTkLabel(f2, text=f"Hello {self.account_data['username']}! 👋", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ctk.CTkLabel(f2, text="I'm your Supersonic Agent.\nI can help you optimize, fix, and enhance.", font=("Segoe UI", 13), text_color=TEXT_MUTED, justify="left").pack(anchor="w")

        # Active Tasks & Recommendations
        mid_row = ctk.CTkFrame(self.main_content, fg_color="transparent")
        mid_row.pack(fill="x", pady=10)
        
        health_b = ctk.CTkFrame(mid_row, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        health_b.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(health_b, text="SYSTEM HEALTH", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 5))
        
        h_split = ctk.CTkFrame(health_b, fg_color="transparent")
        h_split.pack(fill="both", expand=True, padx=15, pady=5)
        
        circle = ctk.CTkFrame(h_split, width=100, height=100, fg_color="transparent", border_width=4, border_color=ACCENT_BLUE, corner_radius=50)
        circle.pack(side="left", padx=10)
        circle.pack_propagate(False)
        ctk.CTkLabel(circle, text="98%", font=("Segoe UI", 24, "bold"), text_color=ACCENT_BLUE).pack(expand=True)
        
        list_f = ctk.CTkFrame(h_split, fg_color="transparent")
        list_f.pack(side="left", padx=20)
        for t in ["Minecraft Files: Healthy", "Mods & Addons: Healthy", "Performance: Excellent"]:
            ctk.CTkLabel(list_f, text=f"✓ {t}", font=("Segoe UI", 12), text_color=ACCENT_GREEN).pack(anchor="w")

        # Chat interface for Agent
        chat = ctk.CTkFrame(self.main_content, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        chat.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(chat, text="CHAT WITH AGENT", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(20, 10))
        
        msg1 = ctk.CTkLabel(chat, text="Why is my game crashing?", fg_color=ACCENT_BLUE, corner_radius=10, text_color=TEXT_PRIMARY, padx=15, pady=10)
        msg1.pack(anchor="e", padx=20, pady=5)
        
        msg2 = ctk.CTkLabel(chat, text="I've analyzed the crash report.\nProblem: Outdated mod 'Entity Culling'\nSolution: Update to v1.6.2", fg_color=BG_COLOR, corner_radius=10, justify="left", padx=15, pady=10)
        msg2.pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkEntry(chat, placeholder_text="Ask me anything...", height=40, fg_color=BG_COLOR).pack(side="bottom", fill="x", padx=20, pady=20)

    # ================= GAME LAUNCH ENGINE =================
    def start_game_launch(self):
        self.play_btn.configure(state="disabled", text="INSTALLING...")
        self.launch_progress.pack(pady=(5, 0))
        threading.Thread(target=self.game_launch_thread, daemon=True).start()

    def game_launch_thread(self):
        version = self.settings.get("mc_version", "1.21.4")
        
        # 1. INSTALLATION STEP - UI Thread Safe Callbacks
        self.thread_safe_update(self.launch_status, text="Installing Assets & Libraries...")
        
        def set_progress(max_val, cur_val):
            val = cur_val / max_val if max_val > 0 else 0
            self.thread_safe_update(self.launch_progress, set=val)
            
        callback = {
            "setStatus": lambda status: self.thread_safe_update(self.launch_status, text=status),
            "setProgress": set_progress,
            "setMax": lambda max_val: None
        }
        
        try:
            # Install base vanilla version (required even for fabric/forge)
            minecraft_launcher_lib.install.install_minecraft_version(version, MC_DIR, callback=callback)
            
            # If Mod Loader is Fabric, you would typically run fabric installer here
            # Since this is a demo structure, we assume vanilla base is enough or already handled.
        except Exception as e:
            print(f"Install failed: {e}")
            traceback.print_exc()
            self.thread_safe_update(self.launch_status, text="Installation Error")
            self.thread_safe_update(self.play_btn, state="normal", text="▶ LAUNCH")
            return

        # 2. GENERATE COMMAND & LAUNCH
        self.thread_safe_update(self.launch_status, text="Generating Launch Command...")
        options = {
            "username": self.account_data["username"],
            "uuid": self.account_data["uuid"],
            "token": self.account_data["token"]
        }
        
        ram = str(self.settings.get("ram", "8192"))
        jvm_args = [f"-Xmx{ram}M", "-Xms2048M"] + self.settings.get("advanced_jvm", "").split()
        
        if self.settings.get("d3d12_wrapper", True):
            jvm_args.append("-Dorg.lwjgl.opengl.libname=opengl32.dll")
            
        options["jvmArguments"] = jvm_args

        try:
            cmd = minecraft_launcher_lib.command.get_minecraft_command(version, MC_DIR, options)
            self.thread_safe_update(self.launch_status, text="Launching Game...")
            
            if self.settings.get("close_on_launch", True):
                self.after(0, self.withdraw)

            # Start Game Process
            if sys.platform == "win32":
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(cmd)
                
            self.after(0, self.reset_launch_ui)
        except Exception as e:
            print(f"Launch failed: {e}")
            traceback.print_exc()
            self.thread_safe_update(self.launch_status, text="Launch Failed!")
            self.thread_safe_update(self.play_btn, state="normal", text="▶ LAUNCH")

    def reset_launch_ui(self):
        self.play_btn.configure(state="normal", text="▶ LAUNCH")
        self.launch_status.configure(text=f"Latest Release ({self.settings.get('mc_version', '1.21.4')})")
        self.launch_progress.set(0)
        self.launch_progress.pack_forget()

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
