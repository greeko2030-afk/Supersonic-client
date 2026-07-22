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

        # ACCOUNT SECTION
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

        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

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
        ctk.CTkButton(self.right_panel, text="🛠️ Scan & Fix", fg_color="#4F46E5", hover_color="#4338CA", height=40).pack(fill="x", padx=20, pady=10)
        ctk.CTkEntry(self.right_panel, placeholder_text="Ask the Agent...", height=40, fg_color=BG_COLOR).pack(fill="x", side="bottom", padx=20, pady=20)

    # ================= 2. MODPACKS UI =================
    def render_modpacks(self):
        head = ctk.CTkFrame(self.main_content, fg_color="transparent")
        head.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(head, text="MODPACKS", font=("Segoe UI", 28, "bold", "italic")).pack(anchor="w")
        ctk.CTkLabel(head, text="Choose. Download. Play.", font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w")
        
        split = ctk.CTkFrame(self.main_content, fg_color="transparent")
        split.pack(fill="both", expand=True)
        scroll = ctk.CTkScrollableFrame(split, fg_color="transparent")
        scroll.pack(side="left", fill="both", expand=True, padx=(0, 15))

        packs = [("Fabulously Optimized", "1.21.4", "12.4M", "4.8"), ("Better MC [FABRIC]", "1.21.4", "8.7M", "4.7"), 
                 ("RLCRAFT", "1.20.1", "6.2M", "4.4"), ("All the Mods 9", "1.20.1", "5.9M", "4.6")]
        
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
        for i, (name, ver, dl, rt) in enumerate(packs):
            card = ctk.CTkFrame(grid, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=i//2, column=i%2, padx=8, pady=8, sticky="nsew")
            grid.grid_columnconfigure(i%2, weight=1)
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=15, pady=15)
            ctk.CTkButton(card, text="📥 Install", fg_color=ACCENT_BLUE).pack(fill="x", padx=15, pady=10)

    # ================= 3. ADDONS UI (Modrinth Impl) =================
    def render_addons(self):
        head = ctk.CTkFrame(self.main_content, fg_color="transparent")
        head.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(head, text="ADDONS", font=("Segoe UI", 28, "bold", "italic")).pack(anchor="w")
        ctk.CTkLabel(head, text="All essential addons. One click install.", font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w")
        
        split = ctk.CTkFrame(self.main_content, fg_color="transparent")
        split.pack(fill="both", expand=True)
        scroll = ctk.CTkScrollableFrame(split, fg_color="transparent")
        scroll.pack(side="left", fill="both", expand=True, padx=(0, 15))

        real_mods = [
            ("sodium", "Sodium", "Boosts FPS and reduces lag.", "🟢"),
            ("iris", "Iris Shaders", "Shaders mod for stunning visuals.", "🌈"),
            ("lithium", "Lithium", "Improves game performance.", "🔥"),
            ("indium", "Indium", "Better Mod Compatibility.", "🔀")
        ]

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x")
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
        
        split = ctk.CTkFrame(self.main_content, fg_color="transparent")
        split.pack(fill="both", expand=True)
        scroll = ctk.CTkScrollableFrame(split, fg_color="transparent")
        scroll.pack(side="left", fill="both", expand=True, padx=(0, 15))

        c4 = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        c4.pack(fill="x", pady=5)
        ctk.CTkLabel(c4, text="AUTHENTICATION", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        auth_f = ctk.CTkFrame(c4, fg_color="transparent")
        auth_f.pack(fill="x", padx=15, pady=10)
        self.off_user = ctk.CTkEntry(auth_f, placeholder_text="Offline Username", fg_color=BG_COLOR)
        self.off_user.insert(0, self.account_data["username"])
        self.off_user.pack(side="left", padx=(0, 10), fill="x", expand=True)
        ctk.CTkButton(auth_f, text="Set Offline", command=self.save_off_account, fg_color=CARD_HOVER, border_width=1).pack(side="left")

        c5 = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        c5.pack(fill="x", pady=5)
        ctk.CTkLabel(c5, text="ADVANCED JVM ARGUMENTS", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        self.jvm_text = ctk.CTkTextbox(c5, height=70, font=("Consolas", 12), fg_color=BG_COLOR)
        self.jvm_text.insert("1.0", self.settings.get("advanced_jvm", ""))
        self.jvm_text.pack(fill="x", padx=15, pady=(0, 15))

    def save_off_account(self):
        self.account_data["username"] = self.off_user.get() or "Player"
        self.save_account()
        self.lbl_acc_name.configure(text=self.account_data["username"])

    # ================= 5. AGENT AI UI =================
    def render_agent_dashboard(self):
        head = ctk.CTkFrame(self.main_content, fg_color="transparent")
        head.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(head, text="AGENT (AI)", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")

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
            "setProgress": update_prog, 
            "setMax": lambda m: None
        }
        
        try:
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
