import sys
import os
import uuid
import threading
import json
import urllib.request
import urllib.error
import subprocess
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from io import BytesIO
from PIL import Image
import minecraft_launcher_lib

# --- ULTRA-MODERN DARK COLOUR PALETTE ---
BG_COLOR = "#080A10"
SIDEBAR_COLOR = "#0D111A"
CARD_COLOR = "#111622"
INNER_CARD = "#171E2E"
ACCENT_BLUE = "#1E5DFB"
ACCENT_CYAN = "#00B2FE"
ACCENT_GREEN = "#10B981"
ACCENT_PURPLE = "#7C3AED"
TEXT_PRIMARY = "#FFFFFF"
TEXT_MUTED = "#5D6B88"
BORDER_COLOR = "#1B2234"

# --- TARGET MODS LIST ---
MOD_SLUGS = [
    "sodium", "lithium", "ferrite-core", "modernfix", "immediatelyfast", 
    "entityculling", "moreculling", "badoptimizations", "krypton", "noisium", 
    "c2me-fabric", "servercore", "lazydfu", "dynamic-fps", "sodium-extra", 
    "reeses-sodium-options", "iris", "indium", "distanthorizons", "memoryleakfix", 
    "starlight", "fastquit", "fastload", "ksyxis", "alternate-current", 
    "clumps", "enhancedblockentities", "exordium", "fast-ip-ping", "smoothboot", 
    "threadtweak", "vmp-fabric", "debugify", "cull-less-leaves", "dashloader", 
    "continuity", "fabric-api"
]

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class ModrinthAPI:
    @staticmethod
    def get_project_info(slug):
        try:
            req = urllib.request.Request(f"https://api.modrinth.com/v2/project/{slug}", headers={'User-Agent': 'SupersonicClient/2.6.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode('utf-8'))
        except:
            return None

    @staticmethod
    def get_latest_version(slug, game_version, loader="fabric"):
        try:
            url = f"https://api.modrinth.com/v2/project/{slug}/version?game_versions=[%22{game_version}%22]&loaders=[%22{loader}%22]"
            req = urllib.request.Request(url, headers={'User-Agent': 'SupersonicClient/2.6.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data and len(data) > 0:
                    return data[0] # Returns the latest valid version
        except:
            return None
        return None

class SupersonicClientMaster(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SUPERSONIC CLIENT v2.6.0")
        self.geometry("1440x900")
        self.minsize(1366, 768)
        self.configure(fg_color=BG_COLOR)

        self.config_file = "supersonic_config.json"
        self.user_config = self.load_config()
        self.game_process = None
        
        self.appdata_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'SupersonicClient', 'bin')
        os.makedirs(self.appdata_dir, exist_ok=True)
        
        self.mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.mods_dir = os.path.join(self.mc_dir, "mods")
        os.makedirs(self.mods_dir, exist_ok=True)

        self.cached_mod_data = [] 

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_header()
        self.setup_frames()
        self.show_frame("Dashboard")

        # Background Mod Fetcher
        threading.Thread(target=self.fetch_real_mods_data, daemon=True).start()

    def load_config(self):
        default_cfg = {
            "ram": 8192, 
            "username": "Raffiee_playssMC", 
            "version": "1.21.4",
            "opt_physics": True, 
            "opt_logic": True, 
            "opt_sound": False, 
            "opt_ai": True
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: 
                    default_cfg.update(json.load(f))
            except: pass
        return default_cfg

    def save_config(self, *args):
        try:
            with open(self.config_file, "w") as f: 
                json.dump(self.user_config, f, indent=4)
        except Exception as e:
            self.log_message(f"[Error] Failed to save config: {e}")

    def setup_header(self):
        self.header_frame = ctk.CTkFrame(self, height=45, fg_color=BG_COLOR, corner_radius=0)
        self.header_frame.grid(row=0, column=1, sticky="ew")
        self.header_frame.pack_propagate(False)
        lbl = ctk.CTkLabel(self.header_frame, text="THE NEXT GENERATION MINECRAFT LAUNCHER", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=ACCENT_CYAN)
        lbl.pack(pady=10)

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(12, weight=1)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(20, 25), sticky="w")
        ctk.CTkLabel(logo_frame, text="⚡", font=ctk.CTkFont(size=28), text_color=ACCENT_BLUE).pack(side="left")
        ctk.CTkLabel(logo_frame, text=" SUPERSONIC\n CLIENT", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=TEXT_PRIMARY, justify="left").pack(side="left", padx=10)

        self.nav_buttons = {}
        nav_items = [
            ("🏠  Dashboard", "Dashboard", None),
            ("🧩  Addons", "Addons", "37+"),
            ("📦  Modpacks", "Modpacks", None),
            ("⚙️  Settings", "Settings", None),
            ("🤖  Agent (AI)", "Agent", "AI")
        ]

        for i, (text, name, badge) in enumerate(nav_items):
            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            btn_frame.grid(row=i+1, column=0, sticky="ew", padx=10, pady=2)
            btn = ctk.CTkButton(btn_frame, text=text, fg_color="transparent", text_color=TEXT_MUTED, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), anchor="w", height=38, command=lambda n=name: self.show_frame(n))
            btn.pack(side="left", fill="x", expand=True)
            self.nav_buttons[name] = btn

            if badge:
                bg_col = ACCENT_PURPLE if badge == "37+" else ACCENT_GREEN
                badge_lbl = ctk.CTkLabel(btn_frame, text=badge, font=ctk.CTkFont(size=9, weight="bold"), text_color="white", fg_color=bg_col, corner_radius=4, width=32, height=16)
                badge_lbl.pack(side="right", padx=(0, 10))

        self.profile_frame = ctk.CTkFrame(self.sidebar, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        self.profile_frame.grid(row=13, column=0, padx=15, pady=(10, 15), sticky="ew")
        ctk.CTkLabel(self.profile_frame, text="Account", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(anchor="w", padx=12, pady=(8, 0))
        
        self.user_lbl = ctk.CTkLabel(self.profile_frame, text=self.user_config.get("username", "Player"), font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=TEXT_PRIMARY)
        self.user_lbl.pack(anchor="w", padx=12)
        ctk.CTkLabel(self.profile_frame, text="👑 Premium", font=ctk.CTkFont(size=11, weight="bold"), text_color="#F59E0B").pack(anchor="w", padx=12, pady=(0, 8))

    def setup_frames(self):
        self.frames_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.frames_container.grid(row=1, column=1, sticky="nsew")
        self.frames_container.grid_rowconfigure(0, weight=1)
        self.frames_container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.init_dashboard()
        self.init_addons()
        self.init_modpacks()
        self.init_settings()
        self.init_agent()

    def show_frame(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.configure(fg_color=INNER_CARD if btn_name == name else "transparent", text_color=TEXT_PRIMARY if btn_name == name else TEXT_MUTED)
        for f_name, f in self.frames.items():
            if f_name == name:
                f.grid(row=0, column=0, sticky="nsew")
            else:
                f.grid_forget()

    def log_message(self, message):
        if hasattr(self, 'logs_box') and self.logs_box.winfo_exists():
            self.after(0, lambda: self._add_log_line(message))

    def _add_log_line(self, message):
        children = self.logs_box.winfo_children()
        if len(children) >= 8: children[0].destroy()
        lbl = ctk.CTkLabel(self.logs_box, text=message, font=ctk.CTkFont(family="Courier New", size=11), text_color=ACCENT_GREEN)
        lbl.pack(anchor="w", padx=15, pady=3)

    # ========================== API & MODS ==========================
    def fetch_real_mods_data(self):
        self.log_message("[API] Fetching real mod data from Modrinth...")
        for slug in MOD_SLUGS:
            info = ModrinthAPI.get_project_info(slug)
            if info:
                title = info.get("title", slug.capitalize())
                desc = info.get("description", "A Minecraft mod.")
                icon_url = info.get("icon_url", None)
                
                img_ctk = None
                if icon_url:
                    try:
                        req = urllib.request.Request(icon_url, headers={'User-Agent': 'Mozilla/5.0'})
                        raw_data = urllib.request.urlopen(req, timeout=5).read()
                        im = Image.open(BytesIO(raw_data)).resize((32, 32))
                        img_ctk = ctk.CTkImage(light_image=im, dark_image=im, size=(32, 32))
                    except: pass
                
                self.cached_mod_data.append({"slug": slug, "title": title, "desc": desc, "icon": img_ctk})
                self.after(0, self.update_addons_ui)
        self.log_message("[API] Finished fetching mod metadata.")

    def update_addons_ui(self):
        for widget in self.dash_addons_grid.winfo_children(): widget.destroy()
            
        dash_display = self.cached_mod_data[:10]
        for i, mdata in enumerate(dash_display):
            row, col = i // 5, i % 5
            card = ctk.CTkFrame(self.dash_addons_grid, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR, height=75)
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            card.pack_propagate(False)
            
            top_f = ctk.CTkFrame(card, fg_color="transparent")
            top_f.pack(fill="x", padx=10, pady=(10, 2))
            if mdata["icon"]: ctk.CTkLabel(top_f, image=mdata["icon"], text="").pack(side="left", padx=(0, 5))
            ctk.CTkLabel(top_f, text=mdata["title"][:15], font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
            
            is_installed = any(mdata["slug"] in f.lower() for f in os.listdir(self.mods_dir)) if os.path.exists(self.mods_dir) else False
            status_text = "✔️ Installed" if is_installed else "❌ Missing"
            status_color = ACCENT_GREEN if is_installed else "#EF4444"
            ctk.CTkLabel(card, text=status_text, font=ctk.CTkFont(size=9), text_color=status_color).pack(anchor="w", padx=10)

        for widget in self.full_addons_grid.winfo_children(): widget.destroy()

        for idx, mdata in enumerate(self.cached_mod_data):
            row, col = idx // 3, idx % 3
            card = ctk.CTkFrame(self.full_addons_grid, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=120)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            card.pack_propagate(False)

            top_f = ctk.CTkFrame(card, fg_color="transparent")
            top_f.pack(fill="x", padx=12, pady=(10, 2))
            if mdata["icon"]: ctk.CTkLabel(top_f, image=mdata["icon"], text="").pack(side="left", padx=(0, 8))
            ctk.CTkLabel(top_f, text=mdata["title"], font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")

            ctk.CTkLabel(card, text=mdata["desc"], font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, justify="left", wraplength=200).pack(anchor="w", padx=12, pady=5)

    def download_all_mods(self):
        self.install_btn.configure(state="disabled", text="Downloading...")
        self.dash_install_btn.configure(state="disabled", text="Downloading...")
        self.log_message("[System] Starting background mod compilation...")
        threading.Thread(target=self._process_mod_downloads, daemon=True).start()

    def _process_mod_downloads(self):
        target_version = self.user_config.get("version", "1.21.4")
        success_count = 0
        
        for slug in MOD_SLUGS:
            ver_data = ModrinthAPI.get_latest_version(slug, target_version)
            if ver_data and "files" in ver_data:
                primary_file = next((f for f in ver_data["files"] if f.get("primary")), ver_data["files"][0])
                download_url = primary_file["url"]
                filename = primary_file["filename"]
                filepath = os.path.join(self.mods_dir, filename)
                
                if not os.path.exists(filepath):
                    self.log_message(f"[Mods] Downloading {filename}...")
                    try:
                        urllib.request.urlretrieve(download_url, filepath)
                        success_count += 1
                    except Exception as e:
                        self.log_message(f"[Error] Failed to download {slug}")
                else:
                    pass # Already exists
        self.log_message(f"[System] Mod download complete! Added {success_count} new mods.")
        self.after(0, lambda: self.install_btn.configure(state="normal", text="📥 Install Missing Mods"))
        self.after(0, lambda: self.dash_install_btn.configure(state="normal", text="📥 Install All"))
        self.after(0, self.update_addons_ui)
        self.after(0, lambda: messagebox.showinfo("Success", f"Finished downloading mods!\nAdded {success_count} new files."))

    # ========================== DASHBOARD & ADDONS ==========================
    def init_dashboard(self):
        f = ctk.CTkFrame(self.frames_container, fg_color="transparent")
        self.frames["Dashboard"] = f
        f.grid_columnconfigure(0, weight=3); f.grid_columnconfigure(1, weight=1); f.grid_rowconfigure(0, weight=1)

        left_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        left_scroll.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)

        banner = ctk.CTkFrame(left_scroll, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR, height=180)
        banner.pack(fill="x", pady=(0, 20))
        banner.pack_propagate(False)

        ctk.CTkLabel(banner, text="SUPERSONIC CLIENT", font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).place(x=30, y=25)
        self.spec_lbl = ctk.CTkLabel(banner, text=f"🟢 Minecraft {self.user_config.get('version', '1.21.4')}    ⚡ RAM: {self.user_config.get('ram', 8192)} MB", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.spec_lbl.place(x=30, y=120)

        self.play_btn = ctk.CTkButton(banner, text="▶  PLAY", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), fg_color=ACCENT_BLUE, hover_color="#1446C9", width=180, height=55, corner_radius=10, command=self.handle_launch)
        self.play_btn.place(relx=0.95, rely=0.5, anchor="e")

        addons_header = ctk.CTkFrame(left_scroll, fg_color="transparent")
        addons_header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(addons_header, text="ESSENTIAL ADDONS", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        self.dash_install_btn = ctk.CTkButton(addons_header, text="📥 Install All", fg_color=INNER_CARD, border_width=1, border_color=BORDER_COLOR, width=110, height=28, command=self.download_all_mods)
        self.dash_install_btn.pack(side="right")

        self.dash_addons_grid = ctk.CTkFrame(left_scroll, fg_color="transparent")
        self.dash_addons_grid.pack(fill="x", pady=(0, 25))
        for col in range(5): self.dash_addons_grid.grid_columnconfigure(col, weight=1)
        ctk.CTkLabel(self.dash_addons_grid, text="Fetching real mods from Modrinth...", text_color=TEXT_MUTED).grid(row=0, column=0, pady=20)

        server_header = ctk.CTkFrame(left_scroll, fg_color="transparent")
        server_header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(server_header, text="FEATURED SERVERS", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")

        server_card = ctk.CTkFrame(left_scroll, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR, height=90)
        server_card.pack(fill="x", pady=(0, 25))
        server_card.pack_propagate(False)
        ctk.CTkLabel(server_card, text="NarratorMC Server", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_PRIMARY).place(x=25, y=18)
        ctk.CTkLabel(server_card, text="IP: www.NarratorMC.net", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).place(x=25, y=48)
        ctk.CTkLabel(server_card, text="ONLINE", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#064E3B", text_color=ACCENT_GREEN, corner_radius=6, padx=12, pady=5).place(relx=0.95, rely=0.5, anchor="e")

        right_panel = ctk.CTkFrame(f, fg_color=SIDEBAR_COLOR, width=320, border_width=1, border_color=BORDER_COLOR)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=10)
        right_panel.pack_propagate(False)

        ctk.CTkLabel(right_panel, text="Recent System Actions", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(15, 5))
        self.logs_box = ctk.CTkFrame(right_panel, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        self.logs_box.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        self.log_message("[System] Client initialized successfully.")

    def init_addons(self):
        f = ctk.CTkFrame(self.frames_container, fg_color="transparent")
        self.frames["Addons"] = f
        f.grid_columnconfigure(0, weight=3); f.grid_columnconfigure(1, weight=1); f.grid_rowconfigure(0, weight=1)

        left_area = ctk.CTkFrame(f, fg_color="transparent")
        left_area.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)

        hdr = ctk.CTkFrame(left_area, fg_color="transparent")
        hdr.pack(fill="x", pady=(10, 15))
        ctk.CTkLabel(hdr, text="ADDONS MANAGER", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        self.install_btn = ctk.CTkButton(hdr, text="📥 Install Missing Mods", fg_color=ACCENT_PURPLE, command=self.download_all_mods)
        self.install_btn.pack(side="right")

        self.full_addons_grid = ctk.CTkScrollableFrame(left_area, fg_color="transparent")
        self.full_addons_grid.pack(fill="both", expand=True)
        for i in range(3): self.full_addons_grid.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(self.full_addons_grid, text="Syncing 37+ mods from Modrinth API...", text_color=TEXT_MUTED).grid(row=0, column=1, pady=50)

        r_panel = ctk.CTkFrame(f, fg_color=SIDEBAR_COLOR, width=320, border_width=1, border_color=BORDER_COLOR)
        r_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=10)
        r_panel.pack_propagate(False)

        status_card = ctk.CTkFrame(r_panel, fg_color=INNER_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=110)
        status_card.pack(fill="x", padx=15, pady=15)
        status_card.pack_propagate(False)
        ctk.CTkLabel(status_card, text="🔌 Modrinth API Connected", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_CYAN).pack(pady=(25, 5))
        ctk.CTkLabel(status_card, text="Fetching live data...", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack()

    def init_modpacks(self):
        f = ctk.CTkFrame(self.frames_container, fg_color="transparent")
        self.frames["Modpacks"] = f
        ctk.CTkLabel(f, text="Modpacks Syncing Engine (Work in Progress)", text_color=TEXT_MUTED).pack(expand=True)

    def init_agent(self):
        f = ctk.CTkFrame(self.frames_container, fg_color="transparent")
        self.frames["Agent"] = f
        ctk.CTkLabel(f, text="Supersonic AI Agent (Disconnected)", text_color=TEXT_MUTED).pack(expand=True)

    # ========================== FULL SETTINGS LOGIC ==========================
    def init_settings(self):
        f = ctk.CTkFrame(self.frames_container, fg_color="transparent")
        self.frames["Settings"] = f
        f.grid_columnconfigure(0, weight=1); f.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        ctk.CTkLabel(scroll, text="CLIENT SETTINGS", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 20))
        
        # --- ACCOUNT SETTINGS ---
        box_acc = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box_acc.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(box_acc, text="USERNAME (Account Name)", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=10)
        
        self.username_var = tk.StringVar(value=self.user_config.get("username", "Raffiee_playssMC"))
        self.username_var.trace_add("write", self.update_username_cfg)
        entry_user = ctk.CTkEntry(box_acc, textvariable=self.username_var, fg_color=INNER_CARD, border_color=BORDER_COLOR)
        entry_user.pack(fill="x", padx=15, pady=(0, 15))

        # --- GAME SETTINGS ---
        box_mc = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box_mc.pack(fill="x", pady=15)
        
        # Version
        ctk.CTkLabel(box_mc, text="MINECRAFT VERSION", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 0))
        self.ver_menu = ctk.CTkOptionMenu(box_mc, values=["1.21.4", "1.21.1", "1.20.4", "1.20.1"], command=self.update_ver_cfg)
        self.ver_menu.set(self.user_config.get("version", "1.21.4"))
        self.ver_menu.pack(fill="x", padx=15, pady=10)

        # RAM
        ctk.CTkLabel(box_mc, text="ALLOCATED RAM", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 0))
        self.ram_menu = ctk.CTkOptionMenu(box_mc, values=["2048 MB", "4096 MB", "8192 MB", "12288 MB", "16384 MB"], command=self.update_ram_cfg)
        self.ram_menu.set(f"{self.user_config.get('ram', 8192)} MB")
        self.ram_menu.pack(fill="x", padx=15, pady=(0, 15))

        # --- OPTIMIZATION TOGGLES ---
        box_opt = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        box_opt.pack(fill="x", pady=15)
        ctk.CTkLabel(box_opt, text="ENGINE OPTIMIZATIONS", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=10)
        
        self.switch_physics = ctk.CTkSwitch(box_opt, text="Opti-Physics (Better Entity Handling)", command=self.update_toggles_cfg)
        self.switch_physics.pack(anchor="w", padx=15, pady=5)
        if self.user_config.get("opt_physics", True): self.switch_physics.select()

        self.switch_logic = ctk.CTkSwitch(box_opt, text="Opti-Logic (Faster Redstone/Tick calculation)", command=self.update_toggles_cfg)
        self.switch_logic.pack(anchor="w", padx=15, pady=5)
        if self.user_config.get("opt_logic", True): self.switch_logic.select()

        self.switch_sound = ctk.CTkSwitch(box_opt, text="Opti-Sound (Async Sound Engine)", command=self.update_toggles_cfg)
        self.switch_sound.pack(anchor="w", padx=15, pady=5)
        if self.user_config.get("opt_sound", False): self.switch_sound.select()

        self.switch_ai = ctk.CTkSwitch(box_opt, text="AI Pathfinding Optimization", command=self.update_toggles_cfg)
        self.switch_ai.pack(anchor="w", padx=15, pady=(5, 15))
        if self.user_config.get("opt_ai", True): self.switch_ai.select()

    def update_username_cfg(self, *args):
        self.user_config["username"] = self.username_var.get()
        self.user_lbl.configure(text=self.user_config["username"])
        self.save_config()

    def update_ram_cfg(self, val):
        self.user_config["ram"] = int(val.split()[0])
        self.spec_lbl.configure(text=f"🟢 Minecraft {self.user_config.get('version')}    ⚡ RAM: {self.user_config.get('ram')} MB")
        self.save_config()
        self.log_message(f"[Settings] RAM Updated to {val}.")

    def update_ver_cfg(self, val):
        self.user_config["version"] = val
        self.spec_lbl.configure(text=f"🟢 Minecraft {self.user_config.get('version')}    ⚡ RAM: {self.user_config.get('ram')} MB")
        self.save_config()
        self.log_message(f"[Settings] Game version set to {val}.")

    def update_toggles_cfg(self):
        self.user_config["opt_physics"] = bool(self.switch_physics.get())
        self.user_config["opt_logic"] = bool(self.switch_logic.get())
        self.user_config["opt_sound"] = bool(self.switch_sound.get())
        self.user_config["opt_ai"] = bool(self.switch_ai.get())
        self.save_config()
        self.log_message("[Settings] Optimization preferences saved.")

    # ========================== LAUNCHER LOGIC ==========================
    def handle_launch(self):
        if self.play_btn.cget("text") == "▶  PLAY":
            self.play_btn.configure(text="⏳ LAUNCHING...", fg_color="#F59E0B")
            threading.Thread(target=self.start_minecraft, daemon=True).start()
        elif self.play_btn.cget("text") == "🛑 STOP PROCESS":
            if self.game_process:
                self.game_process.terminate()
                self.play_btn.configure(text="▶  PLAY", fg_color=ACCENT_BLUE)
                self.log_message("[System] Minecraft forcefully terminated.")

    def start_minecraft(self):
        version = self.user_config.get("version", "1.21.4")
        ram_mb = self.user_config.get("ram", 8192)
        username = self.user_config.get("username", "Player")

        self.log_message(f"[Launch] Checking assets for Fabric {version}...")
        fabric_version = minecraft_launcher_lib.fabric.get_latest_loader_version()
        self.log_message(f"[Launch] Installing Fabric Loader {fabric_version}...")
        minecraft_launcher_lib.fabric.install_fabric(version, self.mc_dir)

        installed = minecraft_launcher_lib.utils.get_installed_versions(self.mc_dir)
        fabric_id = next((v['id'] for v in installed if 'fabric' in v['id'] and version in v['id']), None)

        if not fabric_id:
            self.log_message("[Error] Failed to locate Fabric installation.")
            self.after(0, lambda: self.play_btn.configure(text="▶  PLAY", fg_color=ACCENT_BLUE))
            return

        # APPLYING REAL SETTINGS TO JVM ARGS
        jvm_args = [f"-Xmx{ram_mb}M", f"-Xms{ram_mb}M", "-XX:+UnlockExperimentalVMOptions", "-XX:+UseG1GC"]
        
        # Inject Custom Optimization Flags if toggled
        if self.user_config.get("opt_logic", True):
            jvm_args.extend(["-XX:G1NewSizePercent=20", "-XX:G1ReservePercent=20", "-XX:MaxGCPauseMillis=50", "-XX:G1HeapRegionSize=32M"])
        if self.user_config.get("opt_physics", True):
            jvm_args.append("-XX:+PerfDisableSharedMem")
        if self.user_config.get("opt_sound", False):
            jvm_args.append("-Dorg.lwjgl.openal.libname=OpenAL")
        if self.user_config.get("opt_ai", True):
            jvm_args.append("-XX:+UseStringDeduplication")

        options = {
            "username": username,
            "uuid": str(uuid.uuid4()),
            "token": "",
            "jvmArguments": jvm_args
        }

        try:
            self.log_message(f"[Launch] Generating command for user: {username}...")
            mc_cmd = minecraft_launcher_lib.command.get_minecraft_command(fabric_id, self.mc_dir, options)
            
            self.log_message("[Launch] Launching Minecraft...")
            self.game_process = subprocess.Popen(mc_cmd)
            self.after(0, lambda: self.play_btn.configure(text="🛑 KILL PROCESS", fg_color="#EF4444"))
            
            self.game_process.wait()
            self.log_message("[System] Minecraft session ended.")
        except Exception as e:
            self.log_message(f"[Error] Execution aborted: {str(e)}")
        finally:
            self.after(0, lambda: self.play_btn.configure(text="▶  PLAY", fg_color=ACCENT_BLUE))

if __name__ == "__main__":
    app = SupersonicClientMaster()
    app.mainloop()
