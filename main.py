import os
import sys
import json
import uuid
import threading
import subprocess
import platform
import concurrent.futures
import urllib.request
import io
import customtkinter as ctk
import minecraft_launcher_lib

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ==============================================================================
# ENGINE & CORE LOGIC (TLauncher-like Instance System)
# ==============================================================================
class SupersonicEngine:
    def __init__(self):
        self.config_file = "supersonic_config.json"
        self.config = self.load_config()
        self.base_minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.target_mc_version = "1.21.4"
        
        # GitHub Repository Details
        self.GITHUB_OWNER = "greeko-afk"
        self.GITHUB_REPO = "Supersonic-Client"
        self.GITHUB_BRANCH = "main"

    def load_config(self):
        default_config = {
            "ram_mb": 8192, 
            "username": "Raffiee_playssMC", 
            "uuid": str(uuid.uuid4()),
            "performance_mode": "Ultra",
            "close_launcher": False
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return {**default_config, **json.load(f)}
            except Exception: 
                return default_config
        return default_config

    def save_config(self, key, value):
        self.config[key] = value
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def generate_jvm_args(self):
        ram = self.config.get("ram_mb", 8192)
        return [
            f"-Xms{ram}M", f"-Xmx{ram}M",
            "-XX:+UseZGC", "-XX:+ZGenerational", "-XX:+ZProactive",
            "-XX:+AlwaysPreTouch", "-XX:+DisableExplicitGC",
            "-Djava.net.preferIPv4Stack=true", "-Dfile.encoding=UTF-8"
        ]

    def sync_github_mods(self, instance_name, status_callback):
        """Downloads custom mods from GitHub directly into the specific instance's mods folder like TLauncher"""
        if not REQUESTS_AVAILABLE: return

        instance_dir = os.path.join(self.base_minecraft_directory, "versions", instance_name)
        mods_dir = os.path.join(instance_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        
        api_url = f"https://api.github.com/repos/{self.GITHUB_OWNER}/{self.GITHUB_REPO}/contents/?ref={self.GITHUB_BRANCH}"
        status_callback("Syncing custom mods from GitHub...")
        
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                files = response.json()
                download_tasks = [(f['name'], f['download_url']) for f in files if f.get('name', '').endswith('.jar') and f.get('download_url')]
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                    for mod_name, download_url in download_tasks:
                        dest_path = os.path.join(mods_dir, mod_name)
                        if not os.path.exists(dest_path):
                            executor.submit(self._download_file, download_url, dest_path)
                status_callback("GitHub sync complete.")
        except Exception as e:
            print(f"GitHub Sync Error: {e}")

    def _download_file(self, url, dest_path):
        try:
            r = requests.get(url, stream=True, timeout=15)
            if r.status_code == 200:
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk: f.write(chunk)
        except Exception: pass

    def launch_instance(self, instance_name, mc_version, loader, status_callback):
        """TLauncher style launch: isolates saves, mods, and configs per instance"""
        try:
            instance_dir = os.path.join(self.base_minecraft_directory, "versions", instance_name)
            os.makedirs(instance_dir, exist_ok=True)
            callback_dict = {"setStatus": lambda s: status_callback(f"Status: {s}")}

            # Sync GitHub Mods for this specific instance
            self.sync_github_mods(instance_name, status_callback)

            status_callback(f"Checking {mc_version} Vanilla...")
            minecraft_launcher_lib.install.install_minecraft_version(mc_version, self.base_minecraft_directory, callback=callback_dict)

            launch_version = mc_version
            if loader.lower() == "fabric":
                status_callback("Checking Fabric Loader...")
                minecraft_launcher_lib.fabric.install_fabric(mc_version, self.base_minecraft_directory, callback=callback_dict)
                installed = minecraft_launcher_lib.utils.get_installed_versions(self.base_minecraft_directory)
                launch_version = next((ver["id"] for ver in installed if "fabric" in ver["id"].lower() and mc_version in ver["id"]), mc_version)

            options = {
                "username": self.config["username"],
                "uuid": self.config["uuid"],
                "token": "",
                "jvmArguments": self.generate_jvm_args(),
                "launcherName": "Supersonic Client",
                "launcherVersion": "2.5.0",
                "gameDirectory": instance_dir # TLauncher-like Isolation
            }

            status_callback("Firing up Engine at Max Speed...")
            cmd = minecraft_launcher_lib.command.get_minecraft_command(launch_version, self.base_minecraft_directory, options)
            subprocess.Popen(cmd, creationflags=0x08000000 if platform.system() == "Windows" else 0)
            status_callback("Game is Running!")

        except Exception as e:
            status_callback(f"Error: {str(e)}")

# ==============================================================================
# UI DESIGN (BASED ON PROVIDED IMAGES)
# ==============================================================================
ctk.set_appearance_mode("Dark")

# Colors from Images
BG_DARK = "#05070D"
NAV_BG = "#0B0E14"
CARD_BG = "#0D111A"
CARD_HOVER = "#1A2130"
ACCENT_BLUE = "#1C4ED8"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#8A93A6"
GREEN_STATUS = "#10B981"
BORDER_COLOR = "#1E293B"

class SupersonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.engine = SupersonicEngine()
        self.title("SUPERSONIC CLIENT v2.5.0")
        self.geometry("1300x800")
        self.configure(fg_color=BG_DARK)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.build_ui_frames()
        self.switch_frame("Dashboard")

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=NAV_BG, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1) # Push profile to bottom

        # Logo
        ctk.CTkLabel(self.sidebar, text="⚡ SUPERSONIC", font=("Segoe UI", 20, "bold", "italic"), text_color=ACCENT_BLUE).pack(pady=(25, 30))

        # Nav Buttons
        self.nav_btns = {}
        nav_items = ["Dashboard", "Modpacks", "Addons", "Instances", "Servers", "Resource Packs", "Worlds", "Settings", "Agent (AI)"]
        
        for item in nav_items:
            btn = ctk.CTkButton(self.sidebar, text=f"   {item}", anchor="w", fg_color="transparent", 
                                text_color=TEXT_SECONDARY, hover_color=CARD_HOVER, font=("Segoe UI", 14), 
                                height=40, command=lambda n=item: self.switch_frame(n))
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_btns[item] = btn

        # Bottom Profile (No Premium Text)
        profile_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        profile_frame.pack(side="bottom", fill="x", padx=15, pady=20)
        
        ctk.CTkLabel(profile_frame, text="Account", text_color=TEXT_SECONDARY, font=("Segoe UI", 11)).pack(anchor="w")
        ctk.CTkLabel(profile_frame, text=self.engine.config['username'], text_color=TEXT_PRIMARY, font=("Segoe UI", 14, "bold")).pack(anchor="w")

    def switch_frame(self, frame_name):
        for name, btn in self.nav_btns.items():
            btn.configure(fg_color=CARD_HOVER if name == frame_name else "transparent", 
                          text_color=TEXT_PRIMARY if name == frame_name else TEXT_SECONDARY)
        
        for frame in self.frames.values():
            frame.grid_remove()
            
        if frame_name in self.frames:
            self.frames[frame_name].grid(row=0, column=0, sticky="nsew")

    def build_ui_frames(self):
        self.frames["Dashboard"] = self.create_dashboard()
        self.frames["Modpacks"] = self.create_modpacks_view()
        self.frames["Addons"] = self.create_addons_view()
        self.frames["Settings"] = self.create_settings_view()
        
        # Placeholders for others
        for tab in ["Instances", "Servers", "Resource Packs", "Worlds", "Agent (AI)"]:
            if tab not in self.frames:
                f = ctk.CTkFrame(self.main_container, fg_color="transparent")
                ctk.CTkLabel(f, text=f"{tab} (Coming Soon)", font=("Segoe UI", 24)).place(relx=0.5, rely=0.5, anchor="center")
                self.frames[tab] = f

    # ---------------------------------------------------------
    # DASHBOARD UI (Matches 1000118465.png)
    # ---------------------------------------------------------
    def create_dashboard(self):
        frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        
        # Top Hero Section
        hero = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        hero.pack(fill="x", pady=(0, 20), ipady=30)
        
        ctk.CTkLabel(hero, text="SUPERSONIC CLIENT", font=("Segoe UI", 36, "bold", "italic")).place(x=40, y=20)
        ctk.CTkLabel(hero, text="Hyper optimized. Ultra fast. Future ready.", font=("Segoe UI", 16), text_color=TEXT_SECONDARY).place(x=40, y=65)
        
        self.play_btn = ctk.CTkButton(hero, text="▶ PLAY", font=("Segoe UI", 24, "bold"), fg_color=ACCENT_BLUE, 
                                      hover_color="#1D40B0", width=200, height=60, command=self.trigger_launch)
        self.play_btn.place(relx=0.95, rely=0.4, anchor="e")
        
        self.dash_status = ctk.CTkLabel(hero, text="Ready to Launch (1.21.4)", font=("Segoe UI", 12), text_color=GREEN_STATUS)
        self.dash_status.place(relx=0.95, rely=0.75, anchor="e")

        # Essential Addons Section
        addons_lbl = ctk.CTkLabel(frame, text="⚡ ALL ADDONS - ONE CLICK INSTALL", font=("Segoe UI", 16, "bold"))
        addons_lbl.pack(anchor="w", pady=(10, 10))
        
        addons_grid = ctk.CTkFrame(frame, fg_color="transparent")
        addons_grid.pack(fill="x")
        
        addon_list = [("Sodium", "Boosts FPS"), ("Iris Shaders", "Shaders Mod"), ("Lithium", "Performance"), 
                      ("Indium", "Mod Compat"), ("Phosphor", "Lighting Engine"), ("Entity Culling", "Optimized Entities")]
        
        for i, (name, desc) in enumerate(addon_list):
            card = ctk.CTkFrame(addons_grid, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=60)
            card.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="ew")
            addons_grid.grid_columnconfigure(i%3, weight=1)
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 14, "bold")).place(x=15, y=10)
            ctk.CTkLabel(card, text=desc, font=("Segoe UI", 11), text_color=TEXT_SECONDARY).place(x=15, y=30)

        # Modpacks Section
        ctk.CTkLabel(frame, text="📦 MODPACKS", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(30, 10))
        mp_grid = ctk.CTkFrame(frame, fg_color="transparent")
        mp_grid.pack(fill="x")
        
        modpacks = ["Fabulously Optimized", "Better MC [FABRIC]", "RLCraft", "All the Mods 9"]
        for i, mp in enumerate(modpacks):
            card = ctk.CTkFrame(mp_grid, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=180)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            mp_grid.grid_columnconfigure(i, weight=1)
            
            # Placeholder for modpack image
            img_box = ctk.CTkFrame(card, fg_color="#1E293B", height=80, corner_radius=5)
            img_box.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(card, text=mp, font=("Segoe UI", 14, "bold")).pack()
            ctk.CTkLabel(card, text="1.21.4", font=("Segoe UI", 11), text_color=TEXT_SECONDARY).pack()
            ctk.CTkButton(card, text="Install", fg_color=ACCENT_BLUE, height=28).pack(pady=10, padx=10, fill="x")

        return frame

    # ---------------------------------------------------------
    # MODPACKS UI (Matches 1000118471.png)
    # ---------------------------------------------------------
    def create_modpacks_view(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="MODPACKS", font=("Segoe UI", 32, "bold", "italic")).pack(side="left")
        
        # Main Layout: Grid on left, Filters on right
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=1)
        
        # Grid
        grid_frame = ctk.CTkScrollableFrame(content, fg_color="transparent")
        grid_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        modpacks = [
            ("Fabulously Optimized", "Performance"), ("Better MC", "Vanilla+"),
            ("Prominence II RPG", "RPG"), ("SkyFactory 5", "Skyblock"),
            ("DawnCraft", "Adventure"), ("Create Above", "Tech")
        ]
        
        for i, (mp, tag) in enumerate(modpacks):
            card = ctk.CTkFrame(grid_frame, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=220)
            card.grid(row=i//3, column=i%3, padx=8, pady=8, sticky="ew")
            grid_frame.grid_columnconfigure(i%3, weight=1)
            
            # Image Placeholder
            ctk.CTkFrame(card, fg_color="#1E293B", height=100, corner_radius=5).pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(card, text=mp, font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=10)
            ctk.CTkLabel(card, text=tag, font=("Segoe UI", 11), text_color=ACCENT_BLUE).pack(anchor="w", padx=10)
            
            btn = ctk.CTkButton(card, text="Download & Install", fg_color=ACCENT_BLUE, height=32,
                                command=lambda m=mp: self.install_modpack(m))
            btn.pack(pady=10, padx=10, fill="x", side="bottom")

        # Filters Sidebar
        filters = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        filters.grid(row=0, column=1, sticky="nsew")
        
        search = ctk.CTkEntry(filters, placeholder_text="Search modpacks...", height=35)
        search.pack(fill="x", padx=15, pady=20)
        
        ctk.CTkLabel(filters, text="Minecraft Version", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=15, pady=(10,0))
        ctk.CTkOptionMenu(filters, values=["1.21.4", "1.21.1", "1.20.4", "1.20.1"]).pack(fill="x", padx=15, pady=5)
        
        return frame

    # ---------------------------------------------------------
    # ADDONS UI (Matches 1000118472.png)
    # ---------------------------------------------------------
    def create_addons_view(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        ctk.CTkLabel(frame, text="ADDONS", font=("Segoe UI", 32, "bold", "italic")).pack(anchor="w", pady=(0, 20))
        
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=1)
        
        grid_frame = ctk.CTkScrollableFrame(content, fg_color="transparent")
        grid_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        addons = ["Sodium", "Iris Shaders", "Lithium", "Indium", "Phosphor", "FerriteCore", "Starlight", "Entity Culling"]
        
        for i, addon in enumerate(addons):
            card = ctk.CTkFrame(grid_frame, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR, height=70)
            card.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="ew")
            grid_frame.grid_columnconfigure(i%2, weight=1)
            
            # Simple logo placeholder (Colored box)
            logo = ctk.CTkFrame(card, width=40, height=40, corner_radius=8, fg_color="#3B82F6")
            logo.place(x=15, y=15)
            
            ctk.CTkLabel(card, text=addon, font=("Segoe UI", 15, "bold")).place(x=70, y=12)
            ctk.CTkLabel(card, text="Installed ✔", font=("Segoe UI", 12), text_color=GREEN_STATUS).place(x=70, y=35)
            
            ctk.CTkSwitch(card, text="", width=40).place(relx=0.95, rely=0.5, anchor="e")

        # Right Panel
        right_panel = ctk.CTkFrame(content, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(right_panel, text="All addons are up to date!", font=("Segoe UI", 14, "bold"), text_color=GREEN_STATUS).pack(pady=20)
        ctk.CTkEntry(right_panel, placeholder_text="Search addons...", height=35).pack(fill="x", padx=15, pady=10)
        
        return frame

    # ---------------------------------------------------------
    # SETTINGS UI (Matches 1000118473.png)
    # ---------------------------------------------------------
    def create_settings_view(self):
        frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        
        ctk.CTkLabel(frame, text="SETTINGS", font=("Segoe UI", 32, "bold", "italic")).pack(anchor="w", pady=(0, 20))
        
        grid = ctk.CTkFrame(frame, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0,1,2), weight=1)
        
        # General Settings Card
        gen = ctk.CTkFrame(grid, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        gen.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(gen, text="GENERAL SETTINGS", font=("Segoe UI", 12, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", padx=15, pady=15)
        
        # Performance Settings Card
        perf = ctk.CTkFrame(grid, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        perf.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(perf, text="PERFORMANCE SETTINGS", font=("Segoe UI", 12, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", padx=15, pady=15)
        
        # RAM Allocation (Actually modifies JSON)
        ram_frame = ctk.CTkFrame(perf, fg_color="transparent")
        ram_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(ram_frame, text="RAM Allocation (MB)", font=("Segoe UI", 13)).pack(anchor="w")
        
        self.ram_var = ctk.StringVar(value=str(self.engine.config.get("ram_mb", 8192)))
        ram_menu = ctk.CTkOptionMenu(ram_frame, variable=self.ram_var, values=["2048", "4096", "6144", "8192", "12288", "16384"],
                                     command=lambda v: self.engine.save_config("ram_mb", int(v)))
        ram_menu.pack(fill="x", pady=5)

        # Minecraft Settings
        mc_set = ctk.CTkFrame(grid, fg_color=CARD_BG, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        mc_set.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(mc_set, text="MINECRAFT SETTINGS", font=("Segoe UI", 12, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", padx=15, pady=15)
        
        # Open Directory Button
        ctk.CTkButton(mc_set, text="Open .minecraft Folder", fg_color="#334155", hover_color="#475569", 
                      command=lambda: os.startfile(self.engine.base_minecraft_directory) if platform.system() == "Windows" else None).pack(padx=15, pady=10, fill="x")

        return frame

    # ---------------------------------------------------------
    # LAUNCH LOGIC
    # ---------------------------------------------------------
    def install_modpack(self, modpack_name):
        self.switch_frame("Dashboard")
        self.play_btn.configure(state="disabled", text="INSTALLING...")
        
        def update_status(msg):
            self.after(0, lambda: self.dash_status.configure(text=msg))
            if "Running" in msg or "Error" in msg:
                self.after(0, lambda: self.play_btn.configure(state="normal", text="▶ PLAY"))

        # Target 1.21.4 with Fabric for the selected Modpack (Instance)
        threading.Thread(target=self.engine.launch_instance, args=(modpack_name, "1.21.4", "fabric", update_status), daemon=True).start()

    def trigger_launch(self):
        # Default quick launch uses the "Supersonic_Main" instance
        self.install_modpack("Supersonic_Main")


if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
