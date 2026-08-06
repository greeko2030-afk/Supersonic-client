import os
import sys
import json
import uuid
import threading
import subprocess
import platform
import concurrent.futures
import customtkinter as ctk
import minecraft_launcher_lib

# ==============================================================================
# SAFE DEPENDENCY IMPORTS & FALLBACKS
# ==============================================================================
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ==============================================================================
# API HANDLERS (MODRINTH INTEGRATION)
# ==============================================================================
class ModrinthAPI:
    BASE_URL = "https://api.modrinth.com/v2"
    USER_AGENT = "SupersonicClient/2.5.0"

    @staticmethod
    def fetch_projects(project_type="mod", limit=15):
        if not REQUESTS_AVAILABLE:
            return [{"title": "Error", "description": "Please 'pip install requests'", "downloads": 0}]
            
        url = f"{ModrinthAPI.BASE_URL}/search"
        params = {
            "facets": f'[["project_type:{project_type}"]]',
            "limit": limit,
            "index": "downloads"
        }
        headers = {"User-Agent": ModrinthAPI.USER_AGENT}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json().get("hits", [])
            return []
        except Exception as e:
            print(f"Modrinth Connection Error: {e}")
            return []

    @staticmethod
    def get_latest_version_file(project_slug, mc_version="1.21.4", loader="fabric", project_type="mod"):
        url = f"{ModrinthAPI.BASE_URL}/project/{project_slug}/version"
        params = {"game_versions": f'["{mc_version}"]'}
        if project_type == "mod":
            params["loaders"] = f'["{loader}"]'
            
        headers = {"User-Agent": ModrinthAPI.USER_AGENT}
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                versions = response.json()
                if not versions: return None, None
                files = versions[0].get('files', [])
                primary_file = next((f for f in files if f.get('primary')), files[0] if files else None)
                if primary_file: return primary_file['url'], primary_file['filename']
            return None, None
        except Exception:
            return None, None

# ==============================================================================
# ENGINE & CORE LOGIC
# ==============================================================================
class SupersonicEngine:
    def __init__(self):
        self.config_file = "supersonic_config.json"
        self.config = self.load_config()
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.target_mc_version = "1.21.4"
        self.target_loader = "fabric"
        
        # GitHub Repository Details
        self.GITHUB_OWNER = "greeko-afk"
        self.GITHUB_REPO = "Supersonic-Client"
        self.GITHUB_BRANCH = "main"

        # Start GitHub Sync on engine initialization
        self.start_github_sync()

    def load_config(self):
        default_config = {"ram_mb": 8192, "username": "NarratorPlayer", "uuid": str(uuid.uuid4())}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception: 
                return default_config
        return default_config

    def generate_jvm_args(self):
        ram = self.config.get("ram_mb", 8192)
        # Max Speed & Performance Arguments for Minecraft
        return [
            f"-Xms{ram}M", f"-Xmx{ram}M",
            "-XX:+UseZGC", "-XX:+ZGenerational", "-XX:+ZProactive",
            "-XX:+AlwaysPreTouch", "-XX:+DisableExplicitGC",
            "-Djava.net.preferIPv4Stack=true", "-Dfile.encoding=UTF-8"
        ]

    def start_github_sync(self):
        """Triggers the background download of mods from GitHub upon launcher startup."""
        threading.Thread(target=self._sync_github_mods_task, daemon=True).start()

    def _sync_github_mods_task(self):
        """Fetches all .jar files from the specified GitHub repository and downloads them fast."""
        if self.GITHUB_OWNER == "YOUR_GITHUB_USERNAME":
            print("GitHub Sync Skipped: Please update your GitHub username and repo in the code.")
            return

        mods_dir = os.path.join(self.minecraft_directory, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        
        api_url = f"https://api.github.com/repos/{self.GITHUB_OWNER}/{self.GITHUB_REPO}/contents/?ref={self.GITHUB_BRANCH}"
        print(f"Connecting to GitHub: {api_url}")
        
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                files = response.json()
                download_tasks = []
                
                for file_info in files:
                    if file_info.get('name', '').endswith('.jar') and file_info.get('download_url'):
                        download_tasks.append((file_info['name'], file_info['download_url']))
                
                if not download_tasks:
                    print("No .jar files found in the repository main branch.")
                    return

                print(f"Found {len(download_tasks)} mods on GitHub. Starting parallel download...")
                
                # Multi-threading for maximum download speed
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    for mod_name, download_url in download_tasks:
                        dest_path = os.path.join(mods_dir, mod_name)
                        executor.submit(self._download_single_mod, download_url, dest_path, mod_name)
                        
                print("GitHub Mod Sync Completed Successfully!")
            else:
                print(f"GitHub API Error: HTTP {response.status_code}")
        except Exception as e:
            print(f"Failed to sync with GitHub: {e}")

    def _download_single_mod(self, url, dest_path, mod_name):
        """Downloads a single mod file using large chunks if it does not already exist."""
        if os.path.exists(dest_path):
            return # Skip if already downloaded to save time
            
        try:
            print(f"Downloading {mod_name}...")
            r = requests.get(url, stream=True, timeout=15)
            if r.status_code == 200:
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024): # 1MB chunks for fast I/O
                        if chunk: f.write(chunk)
        except Exception as e:
            print(f"Error downloading {mod_name}: {e}")

    def launch_minecraft(self, status_callback):
        try:
            status_callback("Status: Preparing Fast Launch...")
            os.makedirs(self.minecraft_directory, exist_ok=True)
            callback_dict = {"setStatus": lambda s: status_callback(f"Status: {s}")}

            # 1. Check and Install Vanilla Minecraft
            version_folder = os.path.join(self.minecraft_directory, "versions", self.target_mc_version)
            if not os.path.exists(version_folder):
                status_callback(f"Status: Installing {self.target_mc_version} Vanilla...")
                minecraft_launcher_lib.install.install_minecraft_version(self.target_mc_version, self.minecraft_directory, callback=callback_dict)

            # 2. Check and Install Fabric
            status_callback("Status: Checking Fabric installation...")
            installed_versions = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_directory)
            fabric_version = next((ver["id"] for ver in installed_versions if "fabric" in ver["id"].lower() and self.target_mc_version in ver["id"]), None)
                    
            if not fabric_version:
                status_callback("Status: Installing Fabric Loader...")
                minecraft_launcher_lib.fabric.install_fabric(self.target_mc_version, self.minecraft_directory, callback=callback_dict)
                installed_versions = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_directory)
                fabric_version = next((ver["id"] for ver in installed_versions if "fabric" in ver["id"].lower() and self.target_mc_version in ver["id"]), None)
            
            launch_version = fabric_version if fabric_version else self.target_mc_version

            # 3. Launch Game with Max Speed Settings
            options = {
                "username": self.config["username"],
                "uuid": self.config["uuid"],
                "token": "",
                "jvmArguments": self.generate_jvm_args(),
                "launcherName": "Supersonic Client",
                "launcherVersion": "2.5.0"
            }

            status_callback(f"Status: Generating command for {launch_version}...")
            cmd = minecraft_launcher_lib.command.get_minecraft_command(launch_version, self.minecraft_directory, options)
            
            status_callback("Status: Firing up Engine at Max Speed...")
            subprocess.Popen(cmd, creationflags=0x08000000 if platform.system() == "Windows" else 0)
            status_callback("Status: Game is Running!")

        except Exception as e:
            status_callback(f"Launch Error: {str(e)}")

# ==============================================================================
# USER INTERFACE CONSTRUCTION
# ==============================================================================
ctk.set_appearance_mode("Dark")
BG_DARK = "#05070D"
CARD_BG = "#0D111A"
CARD_HOVER = "#1A2130"
ACCENT_BLUE = "#1C4ED8"
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#8A93A6"
GREEN_STATUS = "#10B981"
NAV_BG = "#0A0D14"
BORDER_COLOR = "#1E293B"

class SupersonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.engine = SupersonicEngine()
        self.title("SUPERSONIC CLIENT v2.5.0")
        self.geometry("1100x750")
        self.configure(fg_color=BG_DARK)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.setup_top_nav()
        
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.tabs = {}
        self.build_tabs()
        self.switch_tab("Dashboard")

    def setup_top_nav(self):
        self.nav_bar = ctk.CTkFrame(self, height=60, fg_color=NAV_BG, corner_radius=0)
        self.nav_bar.grid(row=0, column=0, sticky="ew")
        logo_frame = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        logo_frame.pack(side="left", padx=20, fill="y")
        ctk.CTkLabel(logo_frame, text="⚡ SUPERSONIC", font=("Segoe UI", 18, "bold"), text_color=ACCENT_BLUE).pack(side="left", pady=15)
        
        nav_items = ["Dashboard", "Mods", "Shaders"]
        self.nav_buttons = {}
        tabs_frame = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        tabs_frame.pack(side="left", padx=30, fill="y")
        for name in nav_items:
            btn = ctk.CTkButton(
                tabs_frame, text=name.upper(), fg_color="transparent",
                text_color=TEXT_SECONDARY, hover_color=CARD_HOVER, font=("Segoe UI", 13, "bold"),
                width=120, height=40, command=lambda n=name: self.switch_tab(n)
            )
            btn.pack(side="left", padx=5, pady=10)
            self.nav_buttons[name] = btn

    def switch_tab(self, tab_name):
        for name, btn in self.nav_buttons.items():
            btn.configure(fg_color=CARD_HOVER if name == tab_name else "transparent", 
                          text_color=ACCENT_BLUE if name == tab_name else TEXT_SECONDARY)
        for tab in self.tabs.values(): tab.grid_remove()
        if tab_name in self.tabs: self.tabs[tab_name].grid(row=0, column=0, sticky="nsew")

    def build_tabs(self):
        self.tabs["Dashboard"] = self.tab_dashboard()
        self.tabs["Mods"] = self.create_modrinth_tab("EXPLORE MODS", "mod")
        self.tabs["Shaders"] = self.create_modrinth_tab("EXPLORE SHADERS", "shader")

    def start_game(self):
        self.play_btn.configure(state="disabled", text="LAUNCHING...")
        def update_label(msg):
            self.after(0, lambda: self.status_lbl.configure(text=msg))
            if "Error" in msg or "Game is Running" in msg:
                self.after(0, lambda: self.play_btn.configure(state="normal", text="▶ PLAY"))
        threading.Thread(target=self.engine.launch_minecraft, args=(update_label,), daemon=True).start()

    def tab_dashboard(self):
        frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        hero = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 20), ipady=30)
        ctk.CTkLabel(hero, text="DASHBOARD", font=("Segoe UI", 32, "bold", "italic")).place(x=30, y=20)
        ctk.CTkLabel(hero, text="Your GitHub mods sync automatically in the background.", font=("Segoe UI", 14), text_color=TEXT_SECONDARY).place(x=30, y=65)
        
        self.play_btn = ctk.CTkButton(hero, text="▶ PLAY", font=("Segoe UI", 24, "bold"), fg_color=ACCENT_BLUE, hover_color="#1D40B0", width=200, height=60, command=self.start_game)
        self.play_btn.place(relx=0.95, rely=0.5, anchor="e")
        self.status_lbl = ctk.CTkLabel(hero, text=f"Status: GitHub Sync Active", font=("Segoe UI", 12), text_color=GREEN_STATUS)
        self.status_lbl.place(relx=0.95, rely=0.8, anchor="e")
        return frame

    def create_modrinth_tab(self, header_title, project_type):
        f = ctk.CTkFrame(self.main_area, fg_color="transparent")
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text=header_title, font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        ctk.CTkLabel(scroll, text=f"Use GitHub to sync your {project_type}s.", font=("Segoe UI", 14), text_color=TEXT_SECONDARY).pack(pady=50)
        return f

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
