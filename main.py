import os
import sys
import threading
import subprocess
import requests
import json
import uuid
import traceback
import platform
import customtkinter as ctk
from tkinter import messagebox
import minecraft_launcher_lib

# ==========================================
# CONSTANTS & CONFIGURATIONS
# ==========================================
VERSION = "2.5.0"
UPDATE_URL = "https://supersonic-client--greeko2030.replit.app/api/version"
MINECRAFT_DIR = minecraft_launcher_lib.utils.get_minecraft_directory()
DEFAULT_SERVER = "www.NarratorMC.net"

# UI Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
BG_COLOR = "#0b0f19"
CARD_COLOR = "#141824"
ACCENT_COLOR = "#1f538d"
TEXT_MAIN = "#ffffff"
TEXT_SUB = "#a0aabf"

class SupersonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"SUPERSONIC CLIENT v{VERSION}")
        self.geometry("1400x850")
        self.minsize(1200, 700)
        self.configure(fg_color=BG_COLOR)
        
        # State Variables
        self.username = ctk.StringVar(value="Raffiee_playssMC")
        self.is_premium = ctk.BooleanVar(value=False)
        self.selected_version = ctk.StringVar(value="1.21.4")
        self.ram_allocation = ctk.IntVar(value=8192)
        self.use_d3d12 = ctk.BooleanVar(value=True)
        self.access_token = ""
        self.uuid = ""
        
        # Settings Variables (Mockup states for UI)
        self.perf_mode = ctk.StringVar(value="Ultra (Recommended)")
        self.java_version = ctk.StringVar(value="Java 21 (Recommended)")
        self.start_windows = ctk.BooleanVar(value=False)
        self.preload_assets = ctk.BooleanVar(value=True)
        self.smart_memory = ctk.BooleanVar(value=True)
        self.cloud_sync = ctk.BooleanVar(value=True)

        self.setup_ui()
        self.check_for_updates()

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.setup_dashboard()
        self.setup_modpacks()
        self.setup_addons()
        self.setup_settings()
        
        self.switch_tab("Dashboard")

    # ==========================================
    # SIDEBAR
    # ==========================================
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=CARD_COLOR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo
        logo_lbl = ctk.CTkLabel(self.sidebar, text="SUPERSONIC", font=ctk.CTkFont(size=22, weight="bold", slant="italic"), text_color="#4db8ff")
        logo_lbl.grid(row=0, column=0, padx=20, pady=(25, 5), sticky="w")
        version_lbl = ctk.CTkLabel(self.sidebar, text="CLIENT v2.5.0", font=ctk.CTkFont(size=10), text_color=TEXT_SUB)
        version_lbl.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # Navigation
        nav_items = ["Dashboard", "Modpacks", "Addons", "Instances", "Servers", "Resource Packs", "Worlds", "Settings", "Agent (AI)"]
        self.nav_btns = {}
        for i, name in enumerate(nav_items):
            btn = ctk.CTkButton(self.sidebar, text=f"   {name}", anchor="w", fg_color="transparent", 
                                text_color=TEXT_SUB, hover_color="#1a2133", font=ctk.CTkFont(size=14, weight="bold"),
                                command=lambda n=name: self.switch_tab(n))
            btn.grid(row=i+2, column=0, padx=15, pady=2, sticky="ew")
            self.nav_btns[name] = btn

        # Account Panel
        acc_frame = ctk.CTkFrame(self.sidebar, fg_color="#1a2133", corner_radius=10)
        acc_frame.grid(row=11, column=0, padx=15, pady=20, sticky="ew")
        
        ctk.CTkLabel(acc_frame, text="Account", font=ctk.CTkFont(size=10), text_color=TEXT_SUB).pack(anchor="w", padx=10, pady=(10, 0))
        self.acc_name_lbl = ctk.CTkLabel(acc_frame, textvariable=self.username, font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_MAIN)
        self.acc_name_lbl.pack(anchor="w", padx=10)
        self.acc_status_lbl = ctk.CTkLabel(acc_frame, text="👑 Premium" if self.is_premium.get() else "🔌 Offline", font=ctk.CTkFont(size=11), text_color="#f5c542" if self.is_premium.get() else TEXT_SUB)
        self.acc_status_lbl.pack(anchor="w", padx=10, pady=(0, 10))

    def switch_tab(self, tab_name):
        for frame in self.frames.values():
            frame.grid_forget()
            
        for name, btn in self.nav_btns.items():
            if name == tab_name:
                btn.configure(fg_color="#1c2b4a", text_color=TEXT_MAIN)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SUB)

        if tab_name in self.frames:
            self.frames[tab_name].grid(row=0, column=0, sticky="nsew")

    # ==========================================
    # DASHBOARD TAB
    # ==========================================
    def setup_dashboard(self):
        dash = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Dashboard"] = dash
        dash.grid_columnconfigure(0, weight=3)
        dash.grid_columnconfigure(1, weight=1)
        dash.grid_rowconfigure(1, weight=1)

        # --- Left Content ---
        left_panel = ctk.CTkFrame(dash, fg_color="transparent")
        left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 15))

        # Banner
        banner = ctk.CTkFrame(left_panel, fg_color=CARD_COLOR, corner_radius=15, height=140)
        banner.pack(fill="x", pady=(0, 15))
        banner.pack_propagate(False)
        
        ctk.CTkLabel(banner, text="SUPERSONIC CLIENT", font=ctk.CTkFont(size=28, weight="bold", slant="italic"), text_color=TEXT_MAIN).pack(anchor="w", padx=25, pady=(25, 5))
        ctk.CTkLabel(banner, text="Hyper optimized. Ultra fast. Future ready.", text_color=TEXT_SUB).pack(anchor="w", padx=25)
        
        self.play_btn = ctk.CTkButton(banner, text="▶ PLAY", font=ctk.CTkFont(size=20, weight="bold"), width=160, height=55, fg_color="#2b52ff", hover_color="#1a3bcf", command=self.start_launch_thread)
        self.play_btn.place(relx=0.96, rely=0.5, anchor="e")

        self.status_lbl = ctk.CTkLabel(banner, text="Ready to launch", text_color=TEXT_SUB, font=ctk.CTkFont(size=11))
        self.status_lbl.place(relx=0.96, rely=0.85, anchor="e")
        
        self.progress_bar = ctk.CTkProgressBar(banner, width=160, height=4, progress_color="#4db8ff")
        self.progress_bar.set(0)
        self.progress_bar.place(relx=0.96, rely=0.95, anchor="e")

        # Quick Addons
        addons_frame = ctk.CTkFrame(left_panel, fg_color=CARD_COLOR, corner_radius=10)
        addons_frame.pack(fill="x", pady=10)
        header_f = ctk.CTkFrame(addons_frame, fg_color="transparent")
        header_f.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(header_f, text="⚡ ALL ADDONS - ONE CLICK INSTALL", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(header_f, text="📥 Install All", width=100, fg_color="#1c2b4a").pack(side="right")

        # Dummy Addon Grid
        grid_f = ctk.CTkFrame(addons_frame, fg_color="transparent")
        grid_f.pack(fill="x", padx=10, pady=10)
        addons = ["Sodium", "Iris Shaders", "Lithium", "Indium", "Phosphor", "FerriteCore", "Starlight", "Entity Culling"]
        for i, a in enumerate(addons):
            btn = ctk.CTkButton(grid_f, text=f"{a}\n✔ Installed", fg_color="#1a2133", hover_color="#252f4a", text_color=TEXT_MAIN, height=50)
            btn.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="ew")
            grid_f.grid_columnconfigure(i%4, weight=1)

        # Modpacks Carousel Preview
        mp_frame = ctk.CTkFrame(left_panel, fg_color=CARD_COLOR, corner_radius=10)
        mp_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(mp_frame, text="📦 MODPACKS", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)
        # Fetch preview data from Modrinth API
        self.dash_mp_container = ctk.CTkFrame(mp_frame, fg_color="transparent")
        self.dash_mp_container.pack(fill="both", expand=True, padx=10, pady=10)
        threading.Thread(target=self.fetch_preview_modpacks, daemon=True).start()

        # --- Right Content (Agent AI) ---
        right_panel = ctk.CTkFrame(dash, fg_color=CARD_COLOR, corner_radius=15)
        right_panel.grid(row=0, column=1, rowspan=2, sticky="nsew")
        
        ctk.CTkLabel(right_panel, text="AGENT (AI) BETA", font=ctk.CTkFont(weight="bold", size=14), text_color="#4db8ff").pack(pady=(20, 5))
        ctk.CTkLabel(right_panel, text="🟢 Agent Online", text_color="#5cb85c", font=ctk.CTkFont(size=11)).pack()
        
        chat_box = ctk.CTkTextbox(right_panel, fg_color="#1a2133", text_color=TEXT_SUB, wrap="word")
        chat_box.pack(fill="both", expand=True, padx=15, pady=15)
        chat_box.insert("0.0", f"Hello {self.username.get()}! 👋\n\nI am your Supersonic Agent.\nI can help you:\n✔ Auto fix errors\n✔ Optimize performance\n✔ Detect crashes\n\nAsk me anything!")
        chat_box.configure(state="disabled")

        ctk.CTkButton(right_panel, text="🛠 Scan & Fix Issues", fg_color="#4527a0", hover_color="#311b92", height=40).pack(fill="x", padx=15, pady=(0, 15))
        
        input_f = ctk.CTkFrame(right_panel, fg_color="transparent")
        input_f.pack(fill="x", padx=15, pady=15)
        ctk.CTkEntry(input_f, placeholder_text="Ask the Agent...").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(input_f, text="➤", width=40).pack(side="right")

    # ==========================================
    # MODPACKS TAB
    # ==========================================
    def setup_modpacks(self):
        mp = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Modpacks"] = mp
        
        header = ctk.CTkFrame(mp, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="MODPACKS", font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT_MAIN).pack(side="left")
        ctk.CTkButton(header, text="Browse Modrinth ↗", fg_color="#1c2b4a").pack(side="right", padx=10)
        ctk.CTkButton(header, text="+ Import Modpack", fg_color="transparent", border_width=1, border_color="#1c2b4a").pack(side="right")

        self.mp_scroll = ctk.CTkScrollableFrame(mp, fg_color="transparent")
        self.mp_scroll.pack(fill="both", expand=True)

    def fetch_preview_modpacks(self):
        try:
            res = requests.get('https://api.modrinth.com/v2/search?query=&facets=[["project_type:modpack"]]&limit=4')
            if res.status_code == 200:
                data = res.json()
                for i, p in enumerate(data['hits']):
                    card = ctk.CTkFrame(self.dash_mp_container, fg_color="#1a2133", corner_radius=8)
                    card.grid(row=0, column=i, padx=5, sticky="nsew")
                    self.dash_mp_container.grid_columnconfigure(i, weight=1)
                    
                    ctk.CTkLabel(card, text=p['title'], font=ctk.CTkFont(weight="bold"), text_color=TEXT_MAIN).pack(pady=(15, 5), padx=10)
                    desc = p['description'][:40] + "..." if len(p['description']) > 40 else p['description']
                    ctk.CTkLabel(card, text=desc, text_color=TEXT_SUB, font=ctk.CTkFont(size=11), wraplength=120).pack(pady=5, padx=10)
                    ctk.CTkButton(card, text="📥 Install", fg_color="#2b52ff", height=28).pack(side="bottom", pady=15)
        except:
            pass # Silently fail on network error for preview

    # ==========================================
    # ADDONS TAB
    # ==========================================
    def setup_addons(self):
        addons = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Addons"] = addons
        ctk.CTkLabel(addons, text="ADDONS", font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", pady=(0, 20))
        ctk.CTkLabel(addons, text="All essential addons. One click install.", text_color=TEXT_SUB).pack(anchor="w", pady=(0, 20))
        # UI Structure similar to images can be built out here
        # Keeping it streamlined to avoid extreme code length

    # ==========================================
    # SETTINGS TAB (Exactly like Image)
    # ==========================================
    def setup_settings(self):
        settings = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.frames["Settings"] = settings
        
        # Header
        header = ctk.CTkFrame(settings, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="SETTINGS", font=ctk.CTkFont(size=28, weight="bold", slant="italic")).pack(side="left")
        ctk.CTkButton(header, text="↺ Reset to Default", fg_color="transparent", border_width=1).pack(side="right")
        
        # Tabs inside settings
        tabs_f = ctk.CTkFrame(settings, fg_color="transparent")
        tabs_f.pack(fill="x", pady=(0, 20))
        for t in ["General", "Performance", "Minecraft", "Launcher", "Updates", "Privacy", "Advanced"]:
            color = "#4db8ff" if t == "General" else TEXT_SUB
            ctk.CTkLabel(tabs_f, text=t, font=ctk.CTkFont(weight="bold"), text_color=color).pack(side="left", padx=15)

        content = ctk.CTkFrame(settings, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure((0, 1, 2), weight=2)
        content.grid_columnconfigure(3, weight=1) # Right sidebar

        # --- Column 0: General & Launcher ---
        col0 = ctk.CTkFrame(content, fg_color="transparent")
        col0.grid(row=0, column=0, sticky="nsew", padx=5)
        
        gen_box = self._create_settings_box(col0, "GENERAL SETTINGS")
        self._add_dropdown(gen_box, "Language", "English")
        self._add_dropdown(gen_box, "Theme", "Dark (Default)")
        self._add_switch(gen_box, "Start with Windows", self.start_windows)
        self._add_switch(gen_box, "Minimize to System Tray", ctk.BooleanVar(value=True))

        login_box = self._create_settings_box(col0, "ACCOUNT & AUTH")
        ctk.CTkButton(login_box, text="Login with Microsoft", fg_color="#107c10", hover_color="#0b580b", command=self.login_microsoft).pack(fill="x", padx=15, pady=10)
        off_f = ctk.CTkFrame(login_box, fg_color="transparent")
        off_f.pack(fill="x", padx=15, pady=5)
        self.offline_entry = ctk.CTkEntry(off_f, placeholder_text="Offline Username")
        self.offline_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(off_f, text="Set", width=50, command=self.set_offline).pack(side="right")

        # --- Column 1: Performance & Download ---
        col1 = ctk.CTkFrame(content, fg_color="transparent")
        col1.grid(row=0, column=1, sticky="nsew", padx=5)

        perf_box = self._create_settings_box(col1, "PERFORMANCE SETTINGS")
        self._add_dropdown(perf_box, "Performance Mode", "Ultra (Recommended)")
        self._add_slider(perf_box, "RAM Allocation (MB)", self.ram_allocation, 2048, 16384)
        self._add_switch(perf_box, "Direct3D12 Engine Support", self.use_d3d12)
        self._add_switch(perf_box, "Preload Assets", self.preload_assets)
        self._add_switch(perf_box, "Smart Memory Management", self.smart_memory)

        # --- Column 2: Minecraft & Cloud ---
        col2 = ctk.CTkFrame(content, fg_color="transparent")
        col2.grid(row=0, column=2, sticky="nsew", padx=5)

        mc_box = self._create_settings_box(col2, "MINECRAFT SETTINGS")
        self._add_dropdown(mc_box, "Default Java Version", "Java 21 (Recommended)")
        self._add_switch(mc_box, "Automatically Install Java", ctk.BooleanVar(value=True))
        self._add_dropdown(mc_box, "Game Version", "1.21.4", variable=self.selected_version)

        cloud_box = self._create_settings_box(col2, "CLOUD & SYNC")
        self._add_switch(cloud_box, "Enable Cloud Sync", self.cloud_sync)
        self._add_switch(cloud_box, "Sync Across Devices", ctk.BooleanVar(value=True))

        # --- Column 3: System Overview (Right Sidebar) ---
        col3 = ctk.CTkFrame(content, fg_color="transparent")
        col3.grid(row=0, column=3, sticky="nsew", padx=(15, 0))

        sys_box = self._create_settings_box(col3, "SYSTEM OVERVIEW")
        sys_info = {
            "OS": platform.system() + " " + platform.release(),
            "CPU": platform.processor()[:20] + "...",
            "RAM": "16.0 GB", # Mock or use psutil if available
            "GPU": "Detected",
        }
        for k, v in sys_info.items():
            f = ctk.CTkFrame(sys_box, fg_color="transparent")
            f.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(f, text=k, text_color=TEXT_SUB).pack(side="left")
            ctk.CTkLabel(f, text=v, text_color=TEXT_MAIN).pack(side="right")
        ctk.CTkButton(sys_box, text="〰 Run Diagnostics", fg_color="transparent", border_width=1, border_color="#4db8ff", text_color="#4db8ff").pack(fill="x", padx=15, pady=15)

    # --- Settings UI Helpers ---
    def _create_settings_box(self, parent, title):
        box = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=10)
        box.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(box, text=title, font=ctk.CTkFont(weight="bold", size=11), text_color=TEXT_SUB).pack(anchor="w", padx=15, pady=(15, 10))
        return box

    def _add_switch(self, parent, text, var):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(f, text=text, text_color=TEXT_MAIN).pack(side="left")
        ctk.CTkSwitch(f, text="", variable=var, progress_color="#2b52ff", button_color="#ffffff", button_hover_color="#e0e0e0").pack(side="right")

    def _add_dropdown(self, parent, text, default, variable=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(f, text=text, text_color=TEXT_MAIN).pack(side="left")
        menu = ctk.CTkOptionMenu(f, values=[default, "Other Options..."], fg_color="#1a2133", button_color="#1a2133", variable=variable)
        menu.pack(side="right")

    def _add_slider(self, parent, text, var, min_v, max_v):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=8)
        lbl = ctk.CTkLabel(f, text=f"{text}: {var.get()}", text_color=TEXT_MAIN)
        lbl.pack(side="top", anchor="w")
        slider = ctk.CTkSlider(f, from_=min_v, to=max_v, number_of_steps=20, variable=var, command=lambda v: lbl.configure(text=f"{text}: {int(v)}"))
        slider.pack(side="top", fill="x", pady=(5, 0))

    # ==========================================
    # LOGIC: AUTHENTICATION
    # ==========================================
    def set_offline(self):
        name = self.offline_entry.get()
        if name:
            self.username.set(name)
            self.is_premium.set(False)
            self.acc_status_lbl.configure(text="🔌 Offline", text_color=TEXT_SUB)
            self.uuid = str(uuid.uuid4())
            self.access_token = ""
            messagebox.showinfo("Auth", f"Offline mode set as {name}")

    def login_microsoft(self):
        self.status_lbl.configure(text="Waiting for MS Login...", text_color="#f5c542")
        threading.Thread(target=self._ms_login_thread, daemon=True).start()

    def _ms_login_thread(self):
        try:
            # Placeholder for MSAL device flow implementation
            self.username.set("Premium_User")
            self.is_premium.set(True)
            self.acc_status_lbl.configure(text="👑 Premium", text_color="#f5c542")
            self.status_lbl.configure(text="Microsoft Login Successful!", text_color="#5cb85c")
        except Exception as e:
            self.status_lbl.configure(text=f"Login failed", text_color="red")

    # ==========================================
    # LOGIC: AUTO-UPDATE
    # ==========================================
    def check_for_updates(self):
        def _check():
            try:
                res = requests.get(UPDATE_URL, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("version") != VERSION:
                        print(f"Update available: {data.get('version')}")
            except:
                pass # Silent fail if web is down
        threading.Thread(target=_check, daemon=True).start()

    # ==========================================
    # LOGIC: GAME LAUNCHING & FIXING ERRORS
    # ==========================================
    def start_launch_thread(self):
        self.play_btn.configure(state="disabled", text="LAUNCHING...")
        self.progress_bar.set(0)
        self.status_lbl.configure(text_color=TEXT_SUB)
        threading.Thread(target=self.launch_game, daemon=True).start()

    def launch_game(self):
        mc_version = self.selected_version.get()
        
        def set_status(status: str):
            self.status_lbl.configure(text=status)
            
        def set_progress(progress: int):
            if self.progress_bar.winfo_exists():
                self.progress_bar.set(progress / 100)
            
        def set_max(max_progress: int): pass

        callback_dict = {
            "setStatus": set_status,
            "setProgress": set_progress,
            "setMax": set_max
        }

        try:
            set_status("Installing / Verifying Minecraft files...")
            minecraft_launcher_lib.install.install_minecraft_version(mc_version, MINECRAFT_DIR, callback=callback_dict)

            java_path = minecraft_launcher_lib.utils.get_java_executable()

            options = {
                "username": self.username.get() if self.username.get() else "Player",
                "uuid": self.uuid if self.uuid else str(uuid.uuid4()), 
                "token": self.access_token if self.access_token else "",
                "jvmArguments": [
                    f"-Xmx{self.ram_allocation.get()}M",
                    "-XX:+UnlockExperimentalVMOptions",
                    "-XX:+UseG1GC"
                ],
                "launcherName": "SupersonicClient",
                "launcherVersion": VERSION,
                "server": DEFAULT_SERVER # Auto connects to NarratorMC
            }

            if java_path:
                options["executablePath"] = java_path

            if self.use_d3d12.get():
                engine_path = os.path.join(os.getcwd(), "engine", "opengl32.dll")
                if os.path.exists(engine_path):
                    options["jvmArguments"].append(f"-Dorg.lwjgl.opengl.libname={engine_path}")

            set_status("Generating launch command...")
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(mc_version, MINECRAFT_DIR, options)

            set_status("Game is running!")
            subprocess.Popen(minecraft_command, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            self.after(5000, lambda: self.play_btn.configure(state="normal", text="▶ PLAY"))

        except Exception as e:
            error_msg = str(e)
            full_trace = traceback.format_exc()
            self.status_lbl.configure(text="Install Error! Click for details.", text_color="red")
            self.play_btn.configure(state="normal", text="▶ PLAY")
            
            messagebox.showerror(
                "Minecraft Launch Error", 
                f"Failed to launch the game. Error:\n{error_msg}\n\nTroubleshooting:\n1. Check Internet Connection.\n2. Ensure Java is installed.\n\nAdvanced:\n{full_trace}"
            )

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
