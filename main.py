import os
import sys
import json
import time
import threading
import subprocess
import urllib.request
import requests
import customtkinter as ctk
import minecraft_launcher_lib
from uuid import uuid1

# --- CONFIGURATION & CONSTANTS ---
VERSION = "2.5.0"
UPDATE_URL = "https://supersonic-client--greeko2030.replit.app/api/version"
MC_DIR = minecraft_launcher_lib.utils.get_minecraft_directory().replace("minecraft", "supersonic")
MODS_DIR = os.path.join(MC_DIR, "mods")
CLIENT_ID = "YOUR_MICROSOFT_CLIENT_ID" # Replace with your Azure App ID

# Custom Color Palette (Matching Images)
BG_COLOR = "#0B0F19"
SIDEBAR_COLOR = "#0F1423"
CARD_COLOR = "#151B2B"
CARD_HOVER = "#1E2638"
ACCENT_BLUE = "#2563EB"
ACCENT_GREEN = "#10B981"
TEXT_PRIMARY = "#F8FAFC"
TEXT_MUTED = "#94A3B8"

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
        if os.path.exists("auth.json"):
            try:
                with open("auth.json", "r") as f:
                    return json.load(f)
            except:
                pass
        return {"logged_in": True, "account_type": "Offline", "username": "Raffiee_playssMC", "uuid": str(uuid1()), "token": ""}

    def save_account(self):
        with open("auth.json", "w") as f:
            json.dump(self.account_data, f, indent=4)

    def load_settings(self):
        default = {
            "ram": "8192", 
            "advanced_jvm": "-XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M",
            "d3d12_wrapper": True, 
            "close_on_launch": True,
            "mc_version": "1.21.4",
            "mod_loader": "fabric"
        }
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    return json.load(f)
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
        except:
            pass

    def build_ui(self):
        # 1. Sidebar (Left)
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=SIDEBAR_COLOR, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Brand Logo Area
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", pady=(20, 30), padx=20)
        ctk.CTkLabel(brand_frame, text="SUPERSONIC", font=("Segoe UI", 20, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(brand_frame, text="CLIENT", font=("Segoe UI", 10, "bold"), text_color=ACCENT_BLUE).pack(anchor="w")

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = ["Dashboard", "Modpacks", "Addons", "Instances", "Servers", "Resource Packs", "Worlds", "Settings", "Agent (AI)"]
        
        for item in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=f"   {item}", anchor="w", fg_color="transparent", 
                hover_color=CARD_HOVER, text_color=TEXT_PRIMARY, font=("Segoe UI", 14), 
                height=45, command=lambda k=item.lower(): self.switch_tab(k)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[item.lower()] = btn

        # Account Area (Bottom Left)
        acc_frame = ctk.CTkFrame(self.sidebar, fg_color=CARD_COLOR, corner_radius=10)
        acc_frame.pack(side="bottom", fill="x", padx=15, pady=20)
        
        ctk.CTkLabel(acc_frame, text="Account", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(10, 0))
        self.lbl_acc_name = ctk.CTkLabel(acc_frame, text=self.account_data["username"], font=("Segoe UI", 14, "bold"), text_color=TEXT_PRIMARY)
        self.lbl_acc_name.pack(anchor="w", padx=15)
        ctk.CTkLabel(acc_frame, text=f"👑 {self.account_data['account_type']}", font=("Segoe UI", 12), text_color="#FBBF24").pack(anchor="w", padx=15, pady=(0, 10))

        # 2. Main Content Area (Center)
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # 3. Right Panel (Agent AI / Context)
        self.right_panel = ctk.CTkFrame(self, width=320, fg_color=SIDEBAR_COLOR, corner_radius=15)
        self.right_panel.pack(side="right", fill="y", padx=(0, 20), pady=20)
        self.right_panel.pack_propagate(False)
        self.build_right_panel()

        # Initialize Default Tab
        self.switch_tab("dashboard")

    def build_right_panel(self):
        # AI Assistant Sidebar Profile
        header = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header, text="AGENT (AI) BETA", font=("Segoe UI", 14, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(header, text="Your personal AI assistant", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w")

        bot_card = ctk.CTkFrame(self.right_panel, fg_color=CARD_COLOR, corner_radius=10)
        bot_card.pack(fill="x", padx=20, pady=10, ipady=20)
        ctk.CTkLabel(bot_card, text="🤖", font=("Segoe UI", 50)).pack()
        ctk.CTkLabel(bot_card, text="🟢 Agent Online", font=("Segoe UI", 12), text_color=ACCENT_GREEN).pack()

        chat_box = ctk.CTkFrame(self.right_panel, fg_color=CARD_COLOR, corner_radius=10)
        chat_box.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(chat_box, text=f"Hello {self.account_data['username']}! 👋", font=("Segoe UI", 13, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(chat_box, text="I can help you:\n✓ Auto fix errors\n✓ Optimize performance\n✓ Suggest mods", justify="left", font=("Segoe UI", 12), text_color=TEXT_MUTED).pack(anchor="w", padx=15)

        ctk.CTkButton(self.right_panel, text="✨ Scan & Fix Issues", fg_color="#4F46E5", hover_color="#4338CA", height=40).pack(fill="x", padx=20, pady=20)

    def switch_tab(self, tab_key):
        # Update button highlights
        for key, btn in self.nav_buttons.items():
            if key == tab_key:
                btn.configure(fg_color=CARD_COLOR, text_color=ACCENT_BLUE)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_PRIMARY)

        # Clear main content
        for widget in self.main_content.winfo_children():
            widget.destroy()

        # Render corresponding tab
        if tab_key == "dashboard":
            self.render_dashboard()
            self.right_panel.pack(side="right", fill="y", padx=(0, 20), pady=20)
        elif tab_key == "addons":
            self.render_addons()
            self.right_panel.pack_forget() # Hide right panel to give more space
        elif tab_key == "modpacks":
            self.render_modpacks()
            self.right_panel.pack_forget()
        elif tab_key == "settings":
            self.render_settings()
            self.right_panel.pack_forget()
        elif tab_key == "agent (ai)":
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
        hero = ctk.CTkFrame(self.main_content, fg_color=CARD_COLOR, corner_radius=15, height=200)
        hero.pack(fill="x", pady=(0, 20))
        hero.pack_propagate(False)

        info_frame = ctk.CTkFrame(hero, fg_color="transparent")
        info_frame.pack(side="left", padx=30, pady=30, fill="y", expand=True)
        ctk.CTkLabel(info_frame, text="SUPERSONIC CLIENT", font=("Segoe UI", 32, "bold", "italic"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(info_frame, text="Hyper optimized. Ultra fast. Future ready.", font=("Segoe UI", 14), text_color=TEXT_MUTED).pack(anchor="w", pady=(5, 15))
        
        tags = ctk.CTkFrame(info_frame, fg_color="transparent")
        tags.pack(anchor="w")
        ctk.CTkLabel(tags, text="📦 Minecraft 1.21.4", font=("Segoe UI", 12), text_color=TEXT_PRIMARY).pack(side="left", padx=(0, 15))
        ctk.CTkLabel(tags, text="🚀 Performance: Ultra", font=("Segoe UI", 12), text_color=ACCENT_GREEN).pack(side="left")

        # Play Button Logic Container
        play_frame = ctk.CTkFrame(hero, fg_color="transparent")
        play_frame.pack(side="right", padx=30, pady=30)
        
        self.play_btn = ctk.CTkButton(play_frame, text="▶ PLAY", font=("Segoe UI", 24, "bold"), fg_color=ACCENT_BLUE, hover_color="#1D4ED8", width=220, height=65, corner_radius=10, command=self.start_game_launch)
        self.play_btn.pack()
        
        self.launch_status = ctk.CTkLabel(play_frame, text="Ready to launch", font=("Segoe UI", 11), text_color=TEXT_MUTED)
        self.launch_status.pack(pady=(5, 0))
        self.launch_progress = ctk.CTkProgressBar(play_frame, width=220, height=5, progress_color=ACCENT_BLUE)
        self.launch_progress.set(0)

        # Quick Addons Grid
        ctk.CTkLabel(self.main_content, text="⚡ QUICK ADDONS (ONE CLICK)", font=("Segoe UI", 14, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", pady=(10, 10))
        grid = ctk.CTkFrame(self.main_content, fg_color="transparent")
        grid.pack(fill="x")
        
        mods = [("Sodium", "Boosts FPS"), ("Iris", "Shaders Mod"), ("Lithium", "Performance"), ("Indium", "Mod Compat")]
        for i, (name, desc) in enumerate(mods):
            card = ctk.CTkFrame(grid, fg_color=CARD_COLOR, corner_radius=10)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            grid.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 14, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(15, 0))
            ctk.CTkLabel(card, text=desc, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=15)
            ctk.CTkLabel(card, text="✓ Installed", font=("Segoe UI", 11), text_color=ACCENT_GREEN).pack(anchor="w", padx=15, pady=(5, 15))

    # ================= ADDONS / MODRINTH DOWNLOADER =================
    def render_addons(self):
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="ADDONS & MODS", font=("Segoe UI", 28, "bold"), text_color=TEXT_PRIMARY).pack(side="left")
        
        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        mods_list = [
            ("sodium", "Sodium", "Modern rendering engine for extreme FPS.", "mcwro6nW"),
            ("iris", "Iris Shaders", "A modern shaders mod for Minecraft.", "YL57xq9U"),
            ("lithium", "Lithium", "General-purpose optimization mod.", "gvQqBUqZ"),
            ("ferrite-core", "FerriteCore", "Memory usage optimizations.", "uXXMubvO")
        ]

        row_frame = None
        for i, (slug, name, desc, project_id) in enumerate(mods_list):
            if i % 3 == 0:
                row_frame = ctk.CTkFrame(scroll, fg_color="transparent")
                row_frame.pack(fill="x", pady=5)
            
            card = ctk.CTkFrame(row_frame, fg_color=CARD_COLOR, corner_radius=10, height=120)
            card.pack(side="left", fill="x", expand=True, padx=5)
            card.pack_propagate(False)
            
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 16, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(15, 2))
            ctk.CTkLabel(card, text=desc, font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=15)
            
            btn = ctk.CTkButton(card, text="Download (Modrinth)", fg_color=ACCENT_BLUE, height=30, 
                                command=lambda s=slug, p=project_id: self.download_mod_from_modrinth(s, p))
            btn.pack(side="bottom", anchor="e", padx=15, pady=15)

    def download_mod_from_modrinth(self, slug, project_id):
        def task():
            try:
                print(f"Fetching Modrinth API for {slug}...")
                version = self.settings["mc_version"]
                loader = self.settings["mod_loader"]
                url = f"https://api.modrinth.com/v2/project/{project_id}/version?game_versions=[%22{version}%22]&loaders=[%22{loader}%22]"
                
                req = urllib.request.Request(url, headers={'User-Agent': 'SupersonicClient/2.5.0'})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                
                if not data:
                    print(f"No compatible version found for {slug}")
                    return
                
                download_url = data[0]['files'][0]['url']
                filename = data[0]['files'][0]['filename']
                filepath = os.path.join(MODS_DIR, filename)
                
                print(f"Downloading {filename}...")
                urllib.request.urlretrieve(download_url, filepath)
                print(f"Successfully installed {filename}!")
            except Exception as e:
                print(f"Failed to download {slug}: {e}")
        
        threading.Thread(target=task, daemon=True).start()

    # ================= MODPACKS UI =================
    def render_modpacks(self):
        ctk.CTkLabel(self.main_content, text="MODPACKS", font=("Segoe UI", 28, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 20))
        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        packs = [("Fabulously Optimized", "1.21.4", "Performance"), ("Better MC", "1.21.4", "Vanilla+"), ("RLCraft", "1.12.2", "Hardcore"), ("All The Mods 9", "1.20.1", "Tech & Magic")]
        row = None
        for i, (name, ver, tag) in enumerate(packs):
            if i % 4 == 0:
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=5)
            
            card = ctk.CTkFrame(row, fg_color=CARD_COLOR, corner_radius=10, height=220)
            card.pack(side="left", fill="x", expand=True, padx=5)
            card.pack_propagate(False)
            
            # Dummy Image Area
            img = ctk.CTkFrame(card, fg_color="#1E293B", height=100, corner_radius=10)
            img.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15)
            ctk.CTkLabel(card, text=f"{ver} • {tag}", font=("Segoe UI", 11), text_color=TEXT_MUTED).pack(anchor="w", padx=15)
            ctk.CTkButton(card, text="📥 Install", fg_color=ACCENT_BLUE).pack(fill="x", padx=15, side="bottom", pady=15)

    # ================= SETTINGS (JVM, RAM, Auth, D3D12) =================
    def render_settings(self):
        ctk.CTkLabel(self.main_content, text="SETTINGS", font=("Segoe UI", 28, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", pady=(0, 20))
        scroll = ctk.CTkScrollableFrame(self.main_content, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # 1. Performance & JVM
        box1 = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=10)
        box1.pack(fill="x", pady=10, ipady=10)
        ctk.CTkLabel(box1, text="PERFORMANCE & JVM", font=("Segoe UI", 14, "bold"), text_color=ACCENT_BLUE).pack(anchor="w", padx=20, pady=(15, 10))
        
        self.ram_lbl = ctk.CTkLabel(box1, text=f"RAM Allocation: {self.settings['ram']} MB", font=("Segoe UI", 13))
        self.ram_lbl.pack(anchor="w", padx=20)
        self.ram_slider = ctk.CTkSlider(box1, from_=2048, to=16384, number_of_steps=14, command=lambda v: self.ram_lbl.configure(text=f"RAM Allocation: {int(v)} MB"))
        self.ram_slider.set(int(self.settings["ram"]))
        self.ram_slider.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(box1, text="Advanced JVM Arguments:", font=("Segoe UI", 13)).pack(anchor="w", padx=20, pady=(10, 0))
        self.jvm_text = ctk.CTkTextbox(box1, height=60, font=("Consolas", 12))
        self.jvm_text.insert("1.0", self.settings["advanced_jvm"])
        self.jvm_text.pack(fill="x", padx=20, pady=10)

        # 2. Graphics & Launcher
        box2 = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=10)
        box2.pack(fill="x", pady=10, ipady=10)
        ctk.CTkLabel(box2, text="GRAPHICS & BEHAVIOR", font=("Segoe UI", 14, "bold"), text_color=ACCENT_BLUE).pack(anchor="w", padx=20, pady=(15, 10))
        
        self.d3d_switch = ctk.CTkSwitch(box2, text="Enable Direct3D12 Translation Wrapper (FPS Boost)")
        if self.settings["d3d12_wrapper"]: self.d3d_switch.select()
        self.d3d_switch.pack(anchor="w", padx=20, pady=5)
        
        self.close_switch = ctk.CTkSwitch(box2, text="Hide Launcher when Minecraft starts")
        if self.settings["close_on_launch"]: self.close_switch.select()
        self.close_switch.pack(anchor="w", padx=20, pady=5)

        # 3. Authentication (Offline + Microsoft)
        box3 = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=10)
        box3.pack(fill="x", pady=10, ipady=10)
        ctk.CTkLabel(box3, text="ACCOUNT AUTHENTICATION", font=("Segoe UI", 14, "bold"), text_color=ACCENT_BLUE).pack(anchor="w", padx=20, pady=(15, 10))
        
        auth_grid = ctk.CTkFrame(box3, fg_color="transparent")
        auth_grid.pack(fill="x", padx=20)
        
        self.off_user = ctk.CTkEntry(auth_grid, placeholder_text="Offline Username", width=250)
        self.off_user.insert(0, self.account_data["username"] if self.account_data["account_type"]=="Offline" else "")
        self.off_user.pack(side="left", padx=(0, 10))
        ctk.CTkButton(auth_grid, text="Set Offline", command=self.set_offline_account, fg_color=CARD_HOVER, border_width=1).pack(side="left", padx=(0, 20))
        
        ctk.CTkButton(auth_grid, text="Login with Microsoft", fg_color=ACCENT_GREEN, hover_color="#059669", command=self.start_ms_login).pack(side="left")

        # Save Button
        ctk.CTkButton(scroll, text="💾 Save All Settings", font=("Segoe UI", 14, "bold"), height=45, command=self.save_all_settings).pack(anchor="w", pady=20)

    def set_offline_account(self):
        uname = self.off_user.get().strip() or "Player"
        self.account_data.update({"account_type": "Offline", "username": uname})
        self.save_account()
        self.lbl_acc_name.configure(text=uname)
        print("Offline account saved.")

    def start_ms_login(self):
        try:
            url, state, ver = minecraft_launcher_lib.microsoft_account.get_login_url(CLIENT_ID, "http://localhost:8080")
            print(f"Microsoft Login URL: {url}")
            # Flow continues in browser usually, handled via redirect server in production.
        except Exception as e:
            print(e)

    def save_all_settings(self):
        self.settings["ram"] = str(int(self.ram_slider.get()))
        self.settings["advanced_jvm"] = self.jvm_text.get("1.0", "end-1c").strip()
        self.settings["d3d12_wrapper"] = bool(self.d3d_switch.get())
        self.settings["close_on_launch"] = bool(self.close_switch.get())
        self.save_settings()
        print("Settings saved.")

    # ================= AGENT AI =================
    def render_agent_dashboard(self):
        header = ctk.CTkFrame(self.main_content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="AGENT (AI) DASHBOARD", font=("Segoe UI", 28, "bold"), text_color=TEXT_PRIMARY).pack(side="left")
        
        sys_health = ctk.CTkFrame(self.main_content, fg_color=CARD_COLOR, corner_radius=10)
        sys_health.pack(fill="x", pady=10, ipady=10)
        ctk.CTkLabel(sys_health, text="System Health: 98% (Excellent)", font=("Segoe UI", 16, "bold"), text_color=ACCENT_GREEN).pack(anchor="w", padx=20, pady=10)
        
        ctk.CTkLabel(self.main_content, text="Active Tasks & Recommendations:", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(10, 5))
        tasks = ["⚙️ Optimize Performance (60%)", "🧹 Cleaning Junk Files (30%)", "🛡️ Scanning for Issues (75%)"]
        for t in tasks:
            ctk.CTkLabel(self.main_content, text=t, font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w", padx=10)

    # ================= GAME LAUNCH ENGINE =================
    def start_game_launch(self):
        self.play_btn.configure(state="disabled", text="INSTALLING...")
        self.launch_progress.pack(pady=(5, 0))
        threading.Thread(target=self.game_launch_thread, daemon=True).start()

    def game_launch_thread(self):
        version = self.settings.get("mc_version", "1.21.4")
        
        # 1. INSTALLATION STEP (This was missing in your previous code)
        self.launch_status.configure(text="Installing Minecraft Assets & Libraries...")
        callback = {
            "setStatus": lambda status: self.launch_status.configure(text=status),
            "setProgress": lambda max_val, cur_val: self.launch_progress.set(cur_val / max_val if max_val > 0 else 0),
            "setMax": lambda max_val: None
        }
        
        try:
            # For Fabric, you'd usually install vanilla then fabric. Here we install vanilla base.
            minecraft_launcher_lib.install.install_minecraft_version(version, MC_DIR, callback=callback)
        except Exception as e:
            print(f"Install failed: {e}")
            self.launch_status.configure(text="Installation Error")
            self.play_btn.configure(state="normal", text="▶ PLAY")
            return

        # 2. GENERATE COMMAND & LAUNCH
        self.launch_status.configure(text="Generating Launch Command...")
        options = {
            "username": self.account_data["username"],
            "uuid": self.account_data["uuid"],
            "token": self.account_data["token"]
        }
        
        ram = self.settings.get("ram", "8192")
        jvm_args = [f"-Xmx{ram}M", "-Xms2048M"] + self.settings.get("advanced_jvm", "").split()
        
        if self.settings.get("d3d12_wrapper", True):
            jvm_args.append("-Dorg.lwjgl.opengl.libname=opengl32.dll")
            
        options["jvmArguments"] = jvm_args

        try:
            cmd = minecraft_launcher_lib.command.get_minecraft_command(version, MC_DIR, options)
            self.launch_status.configure(text="Launching...")
            
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
            self.launch_status.configure(text="Launch Failed!")
            self.play_btn.configure(state="normal", text="▶ PLAY")

    def reset_launch_ui(self):
        self.play_btn.configure(state="normal", text="▶ PLAY")
        self.launch_status.configure(text="Ready to launch")
        self.launch_progress.set(0)
        self.launch_progress.pack_forget()

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
