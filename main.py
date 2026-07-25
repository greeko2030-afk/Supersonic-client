import os
import sys
import json
import time
import threading
import subprocess
import traceback
import webbrowser
from uuid import uuid1
import urllib.request

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
APP_DIR = os.path.dirname(os.path.abspath(__file__))
MC_DIR = minecraft_launcher_lib.utils.get_minecraft_directory().replace("minecraft", "supersonic")
MODS_DIR = os.path.join(MC_DIR, "mods")
ENGINE_DIR = os.path.join(MC_DIR, "engine") # Folder for your C++/CMake compiled binaries

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

        # Variables for UI
        self.ram_var = ctk.IntVar(value=self.settings.get("ram", 8192))
        self.d3d12_var = ctk.BooleanVar(value=self.settings.get("d3d12_wrapper", True))

        threading.Thread(target=self.check_for_updates, daemon=True).start()
        self.build_ui()

    def setup_directories(self):
        os.makedirs(MC_DIR, exist_ok=True)
        os.makedirs(MODS_DIR, exist_ok=True)
        os.makedirs(ENGINE_DIR, exist_ok=True)

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
        if hasattr(self, 'lbl_acc_name'):
            self.lbl_acc_name.configure(text=self.account_data["username"])
            self.lbl_acc_type.configure(text=f"👑 {self.account_data['account_type']}")

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
        self.settings["ram"] = self.ram_var.get()
        self.settings["d3d12_wrapper"] = self.d3d12_var.get()
        if hasattr(self, 'jvm_text'):
            self.settings["advanced_jvm"] = self.jvm_text.get("1.0", "end-1c").strip()
            
        with open("settings.json", "w") as f:
            json.dump(self.settings, f, indent=4)

    def check_for_updates(self):
        try:
            res = requests.get(UPDATE_URL, timeout=5)
            if res.status_code == 200:
                data = res.json()
                latest_version = data.get("version", VERSION)
                download_url = data.get("download_url", "")
                
                if latest_version != VERSION and download_url:
                    print("Update found! Downloading...")
                    # Real auto-update logic (Downloads new main.py and replaces current one)
                    new_file = os.path.join(APP_DIR, "main_update.py")
                    urllib.request.urlretrieve(download_url, new_file)
                    
                    # Overwrite and restart logic would go here depending on OS
                    # For safety in this script, we just notify
                    print(f"Update downloaded to {new_file}. Please restart.")
        except Exception as e:
            print(f"Auto-update check failed: {e}")

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
        ctk.CTkLabel(self.top_bar, text="C++ POWERED ENGINE • PYTHON UI", font=("Segoe UI", 11, "bold"), text_color=ACCENT_GREEN).pack(side="left", padx=20)
        
        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=SIDEBAR_COLOR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "🏠"), ("Modpacks", "📦"), ("Addons", "🧩"), 
            ("Settings", "⚙️"), ("Agent (AI)", "🤖")
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

        # ACCOUNT SECTION
        acc_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        acc_frame.pack(side="bottom", fill="x", pady=20)
        
        user_card = ctk.CTkFrame(acc_frame, fg_color=CARD_COLOR, corner_radius=10, border_color=BORDER_COLOR, border_width=1)
        user_card.pack(fill="x", padx=15)
        ctk.CTkLabel(user_card, text="Account", font=("Segoe UI", 10), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 0))
        self.lbl_acc_name = ctk.CTkLabel(user_card, text=self.account_data["username"], font=("Segoe UI", 14, "bold"), text_color=TEXT_PRIMARY)
        self.lbl_acc_name.pack(anchor="w", padx=15)
        self.lbl_acc_type = ctk.CTkLabel(user_card, text=f"👑 {self.account_data['account_type']}", font=("Segoe UI", 11, "bold"), text_color="#FBBF24")
        self.lbl_acc_type.pack(anchor="w", padx=15, pady=(0, 10))

        # MAIN CONTENT AREA
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(side="left", fill="both", expand=True, padx=20, pady=(0, 20))

        self.switch_tab("dashboard")

    def switch_tab(self, tab_key):
        tab_key = tab_key.replace(" (ai)", "")
        for key, btn in self.nav_buttons.items():
            if key.replace(" (ai)", "") == tab_key:
                btn.configure(fg_color=CARD_HOVER, text_color=ACCENT_BLUE)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_PRIMARY)

        for widget in self.main_content.winfo_children(): widget.destroy()

        if tab_key == "dashboard": self.render_dashboard()
        elif tab_key == "addons": self.render_addons()
        elif tab_key == "modpacks": self.render_modpacks()
        elif tab_key == "settings": self.render_settings()
        elif tab_key == "agent": self.render_placeholder("Agent (AI)")

    def render_placeholder(self, title):
        ctk.CTkLabel(self.main_content, text=title, font=("Segoe UI", 28, "bold")).pack(anchor="w")
        ctk.CTkLabel(self.main_content, text="Module currently under development.", font=("Segoe UI", 14), text_color=TEXT_MUTED).pack(anchor="w", pady=10)

    # ================= 1. DASHBOARD =================
    def render_dashboard(self):
        hero = ctk.CTkFrame(self.main_content, fg_color=CARD_COLOR, corner_radius=15, height=160, border_width=1, border_color=BORDER_COLOR)
        hero.pack(fill="x", pady=(0, 20))
        hero.pack_propagate(False)

        info_f = ctk.CTkFrame(hero, fg_color="transparent")
        info_f.pack(side="left", padx=30, pady=25, fill="y")
        ctk.CTkLabel(info_f, text="SUPERSONIC CLIENT", font=("Segoe UI", 28, "bold", "italic")).pack(anchor="w")
        ctk.CTkLabel(info_f, text="Direct3D12 Engine Ready. Ultra fast.", font=("Segoe UI", 14), text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 10))
        
        tags_f = ctk.CTkFrame(info_f, fg_color="transparent")
        tags_f.pack(anchor="w")
        ctk.CTkLabel(tags_f, text=f"📦 {self.settings['mc_version']}", font=("Segoe UI", 11, "bold"), fg_color=BG_COLOR, corner_radius=5).pack(side="left", padx=(0, 10), ipadx=8, ipady=4)
        engine_txt = "🚀 C++ Engine: D3D12" if self.settings.get("d3d12_wrapper") else "🚀 Standard Engine: OpenGL"
        ctk.CTkLabel(tags_f, text=engine_txt, font=("Segoe UI", 11, "bold"), text_color=ACCENT_GREEN, fg_color=BG_COLOR, corner_radius=5).pack(side="left", padx=(0, 10), ipadx=8, ipady=4)

        play_f = ctk.CTkFrame(hero, fg_color="transparent")
        play_f.pack(side="right", padx=30, pady=25)
        self.play_btn = ctk.CTkButton(play_f, text="▶ PLAY", font=("Segoe UI", 24, "bold"), fg_color=ACCENT_BLUE, hover_color=ACCENT_BLUE_HOVER, width=180, height=60, corner_radius=10, command=self.start_game_launch)
        self.play_btn.pack()
        self.launch_status = ctk.CTkLabel(play_f, text="Ready to Launch", font=("Segoe UI", 11), text_color=TEXT_MUTED)
        self.launch_status.pack(pady=(5, 0))
        self.launch_progress = ctk.CTkProgressBar(play_f, width=180, height=5, progress_color=ACCENT_GREEN)
        self.launch_progress.set(0)

        # Quick Stats
        bot_bar = ctk.CTkFrame(self.main_content, height=80, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        bot_bar.pack(side="bottom", fill="x")
        bot_bar.pack_propagate(False)
        for label, val, p_val, color in [("Allocated RAM", f"{self.settings['ram']} MB", self.settings['ram']/16384, ACCENT_BLUE), ("D3D12 Pipeline", "Active", 1.0, ACCENT_GREEN)]:
            f = ctk.CTkFrame(bot_bar, fg_color="transparent")
            f.pack(side="left", expand=True, fill="both", padx=20, pady=15)
            hf = ctk.CTkFrame(f, fg_color="transparent")
            hf.pack(fill="x")
            ctk.CTkLabel(hf, text=label, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(hf, text=val, font=("Segoe UI", 12, "bold")).pack(side="right")
            pb = ctk.CTkProgressBar(f, height=6, progress_color=color, fg_color=BG_COLOR)
            pb.pack(fill="x", pady=5)
            pb.set(p_val)

    # ================= 2. MODPACKS (CurseForge/Modrinth Logic) =================
    def render_modpacks(self):
        head = ctk.CTkFrame(self.main_content, fg_color="transparent")
        head.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(head, text="MODPACKS", font=("Segoe UI", 28, "bold", "italic")).pack(anchor="w")
        ctk.CTkLabel(head, text="High performance preset packs.", font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w")
        
        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Simplified modpack installer for the requested version
        packs = [("Supersonic Optimized", "Ultimate FPS Boost for 1.21.4", ["sodium", "lithium", "iris", "ferrite-core"]),
                 ("Vanilla+", "Better graphics & sounds", ["iris", "presence-footsteps", "sound-physics-remastered"])]
        
        for name, desc, mods in packs:
            card = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=5)
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 16, "bold")).pack(side="left", padx=15, pady=15)
            ctk.CTkLabel(card, text=desc, font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(side="left", padx=10)
            
            btn = ctk.CTkButton(card, text="Install Pack", fg_color=ACCENT_BLUE)
            btn.configure(command=lambda m=mods, b=btn: self.install_modpack(m, b))
            btn.pack(side="right", padx=15)

    def install_modpack(self, mod_list, btn):
        btn.configure(state="disabled", text="Installing...")
        def task():
            for mod in mod_list:
                self.thread_safe_update(btn, text=f"Downloading {mod}...")
                self._download_modrinth_file(mod)
            self.thread_safe_update(btn, text="✓ Installed", fg_color=ACCENT_GREEN)
        threading.Thread(target=task, daemon=True).start()

    # ================= 3. ADDONS (Modrinth Impl) =================
    def render_addons(self):
        head = ctk.CTkFrame(self.main_content, fg_color="transparent")
        head.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(head, text="ADDONS (Modrinth)", font=("Segoe UI", 28, "bold", "italic")).pack(anchor="w")
        
        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        mods = [
            ("sodium", "Sodium", "Modern rendering engine (Boosts FPS)"),
            ("iris", "Iris Shaders", "Shaders mod for stunning visuals"),
            ("lithium", "Lithium", "General-purpose optimization"),
            ("indium", "Indium", "Sodium addon for Fabric Rendering API")
        ]

        for slug, name, desc in mods:
            card = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=5)
            inf = ctk.CTkFrame(card, fg_color="transparent")
            inf.pack(side="left", fill="both", expand=True, padx=15, pady=15)
            ctk.CTkLabel(inf, text=name, font=("Segoe UI", 15, "bold")).pack(anchor="w")
            ctk.CTkLabel(inf, text=desc, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")
            
            btn = ctk.CTkButton(card, text="Install", width=100, border_width=1)
            btn.configure(command=lambda s=slug, b=btn: self.install_mod(s, b))
            btn.pack(side="right", padx=15)

    def _download_modrinth_file(self, slug):
        ver = self.settings.get("mc_version", "1.21.4")
        url = f"https://api.modrinth.com/v2/project/{slug}/version"
        params = {'game_versions': f'["{ver}"]', 'loaders': '["fabric"]'}
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200 and res.json():
            file_data = res.json()[0]['files'][0]
            dl = requests.get(file_data['url'], stream=True)
            filepath = os.path.join(MODS_DIR, file_data['filename'])
            with open(filepath, 'wb') as f:
                for chunk in dl.iter_content(8192): f.write(chunk)
            return True
        return False

    def install_mod(self, slug, btn):
        btn.configure(state="disabled", text="Installing...")
        def task():
            try:
                success = self._download_modrinth_file(slug)
                if success:
                    self.thread_safe_update(btn, text="✓ Installed", fg_color="transparent", text_color=ACCENT_GREEN, border_color=ACCENT_GREEN)
                else:
                    self.thread_safe_update(btn, text="Failed (No Version)", state="normal")
            except Exception as e:
                self.thread_safe_update(btn, text="Error", state="normal")
        threading.Thread(target=task, daemon=True).start()

    # ================= 4. SETTINGS & LOGIN UI =================
    def render_settings(self):
        head = ctk.CTkFrame(self.main_content, fg_color="transparent")
        head.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(head, text="SETTINGS & ENGINE", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        ctk.CTkButton(head, text="💾 Save Changes", command=self.save_settings, fg_color=ACCENT_GREEN, hover_color="#059669").pack(side="right")
        
        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # C++ Engine Settings
        c1 = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        c1.pack(fill="x", pady=5)
        ctk.CTkLabel(c1, text="C++ ENGINE TRANSLATION", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkSwitch(c1, text="Enable Direct3D12 Wrapper (opengl32.dll injection)", variable=self.d3d12_var, progress_color=ACCENT_BLUE).pack(anchor="w", padx=15, pady=(0, 15))

        # Authentication Settings
        c2 = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        c2.pack(fill="x", pady=5)
        ctk.CTkLabel(c2, text="AUTHENTICATION (Microsoft / Offline)", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        
        auth_f = ctk.CTkFrame(c2, fg_color="transparent")
        auth_f.pack(fill="x", padx=15, pady=(0,15))
        
        self.off_user = ctk.CTkEntry(auth_f, placeholder_text="Offline Username", fg_color=BG_COLOR, width=200)
        self.off_user.insert(0, self.account_data["username"] if self.account_data["account_type"] == "Offline" else "Player")
        self.off_user.pack(side="left", padx=(0, 10))
        ctk.CTkButton(auth_f, text="Set Offline", command=self.do_offline_login, border_width=1).pack(side="left", padx=(0, 20))
        ctk.CTkButton(auth_f, text="Log in with Microsoft", command=self.do_ms_login, fg_color="#107C10", hover_color="#0B5C0B").pack(side="left")

        # System Settings
        c3 = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        c3.pack(fill="x", pady=5)
        ctk.CTkLabel(c3, text="SYSTEM & JVM", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(15, 10))
        
        lbl = ctk.CTkLabel(c3, text=f"Allocated RAM: {self.ram_var.get()} MB")
        lbl.pack(anchor="w", padx=15)
        def update_ram_lbl(val): lbl.configure(text=f"Allocated RAM: {int(val)} MB")
        slider = ctk.CTkSlider(c3, from_=2048, to=16384, variable=self.ram_var, command=update_ram_lbl)
        slider.pack(fill="x", padx=15, pady=(5, 15))

        ctk.CTkLabel(c3, text="Advanced JVM Arguments", font=("Segoe UI", 11)).pack(anchor="w", padx=15)
        self.jvm_text = ctk.CTkTextbox(c3, height=60, font=("Consolas", 11), fg_color=BG_COLOR)
        self.jvm_text.insert("1.0", self.settings.get("advanced_jvm", ""))
        self.jvm_text.pack(fill="x", padx=15, pady=(0, 15))

    def do_offline_login(self):
        self.account_data = {"logged_in": True, "account_type": "Offline", "username": self.off_user.get() or "Player", "uuid": str(uuid1()), "token": ""}
        self.save_account()

    def do_ms_login(self):
        # Implementation for Microsoft Login using minecraft-launcher-lib
        def task():
            CLIENT_ID = "00000000402b5328" # Generic Xbox Client ID
            login_url, state, pkce = minecraft_launcher_lib.microsoft_account.get_login_url(CLIENT_ID, "https://login.live.com/oauth20_desktop.srf")
            webbrowser.open(login_url)
            
            # Simple dialog to ask user for the redirected URL
            dialog = ctk.CTkInputDialog(text="Paste the URL you were redirected to:", title="Microsoft Login")
            redirect_url = dialog.get_input()
            
            if redirect_url:
                try:
                    auth_code = minecraft_launcher_lib.microsoft_account.parse_auth_code_url(redirect_url, state)
                    account_dict = minecraft_launcher_lib.microsoft_account.complete_login(CLIENT_ID, None, redirect_url, auth_code, pkce)
                    
                    self.account_data = {
                        "logged_in": True,
                        "account_type": "Microsoft",
                        "username": account_dict["name"],
                        "uuid": account_dict["id"],
                        "token": account_dict["access_token"]
                    }
                    self.save_account()
                    print("Microsoft Login Successful!")
                except Exception as e:
                    print(f"Microsoft Login failed: {e}")
                    
        threading.Thread(target=task, daemon=True).start()

    # ================= GAME LAUNCH ENGINE =================
    def start_game_launch(self):
        self.play_btn.configure(state="disabled", text="PREPARING...")
        self.launch_progress.set(0)
        threading.Thread(target=self.game_launch_thread, daemon=True).start()

    def game_launch_thread(self):
        ver = self.settings.get("mc_version", "1.21.4")
        self.thread_safe_update(self.launch_status, text="Checking Assets & Fabric Libraries...")
        
        callback = {
            "setStatus": lambda s: self.thread_safe_update(self.launch_status, text=s),
            "setProgress": lambda m, c: self.thread_safe_update(self.launch_progress, set=(c/m if m>0 else 0)), 
            "setMax": lambda m: None
        }
        
        try:
            # Install specific loader version (Fabric for addons support)
            fabric_ver = minecraft_launcher_lib.fabric.get_latest_minecraft_version(ver)
            if not fabric_ver:
                minecraft_launcher_lib.install.install_minecraft_version(ver, MC_DIR, callback=callback)
            else:
                minecraft_launcher_lib.fabric.install_fabric(ver, MC_DIR, callback=callback)
                # Fabric modifies version string usually to fabric-loader-...
                installed_vers = minecraft_launcher_lib.utils.get_installed_versions(MC_DIR)
                for v in installed_vers:
                    if "fabric" in v['id'] and ver in v['id']:
                        ver = v['id']
                        break
        except Exception as e:
            print(f"Install failed:\n{traceback.format_exc()}")
            self.thread_safe_update(self.launch_status, text="Install Error! Check Console.", text_color="red")
            self.thread_safe_update(self.play_btn, state="normal", text="▶ PLAY")
            return

        self.thread_safe_update(self.launch_status, text="Injecting C++ Engine & JVM Args...", text_color=TEXT_MUTED)
        
        options = {
            "username": self.account_data["username"],
            "uuid": self.account_data["uuid"],
            "token": self.account_data["token"]
        }
        
        # Engine integration logic
        jvm = [f"-Xmx{self.settings['ram']}M", "-Xms2048M"]
        jvm.extend(self.settings.get("advanced_jvm", "").split())
            
        if self.settings.get("d3d12_wrapper", True):
            # Tell Java to load the custom C++ compiled DLL wrapper for D3D12 translation
            jvm.append(f"-Dorg.lwjgl.opengl.libname={os.path.join(ENGINE_DIR, 'opengl32.dll')}")
            
        options["jvmArguments"] = jvm

        try:
            cmd = minecraft_launcher_lib.command.get_minecraft_command(ver, MC_DIR, options)
            self.thread_safe_update(self.launch_status, text="Launching Supersonic Client...")
            
            if self.settings.get("close_on_launch", True):
                self.after(0, self.withdraw)

            if sys.platform == "win32":
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(cmd)
                
            self.after(2000, self.reset_launch_ui)
        except Exception as e:
            print(f"Launch failed:\n{traceback.format_exc()}")
            self.thread_safe_update(self.launch_status, text="Launch Failed!", text_color="red")
            self.thread_safe_update(self.play_btn, state="normal", text="▶ PLAY")

    def reset_launch_ui(self):
        self.play_btn.configure(state="normal", text="▶ PLAY")
        self.launch_status.configure(text="Ready to Launch", text_color=TEXT_MUTED)
        self.launch_progress.set(0)

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
