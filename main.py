import os
import sys
import json
import uuid
import time
import threading
import subprocess
import platform
import customtkinter as ctk
import minecraft_launcher_lib

# ==============================================================================
# SAFE DEPENDENCY IMPORTS & FALLBACKS
# ==============================================================================
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

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
    USER_AGENT = "SupersonicClient/2.5.0 (contact@narratormc.net)"

    @staticmethod
    def fetch_projects(project_type="mod", limit=15):
        """Fetches projects dynamically based on type (mod, shader, resourcepack, etc.)"""
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
        """Gets the exact download file link based on game version and loader compatibility."""
        url = f"{ModrinthAPI.BASE_URL}/project/{project_slug}/version"
        params = {"game_versions": f'["{mc_version}"]'}
        
        # Only strict enforce loader for mods. Shaders/Resourcepacks are often loader-agnostic on API.
        if project_type == "mod":
            params["loaders"] = f'["{loader}"]'
            
        headers = {"User-Agent": ModrinthAPI.USER_AGENT}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                versions = response.json()
                if not versions:
                    return None, None
                files = versions[0].get('files', [])
                primary_file = next((f for f in files if f.get('primary')), files[0] if files else None)
                if primary_file:
                    return primary_file['url'], primary_file['filename']
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
        self.system_info = self.get_system_info()
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.target_mc_version = "1.21.4"
        self.target_loader = "fabric"

        # --- GITHUB MOD INJECTION VARIABLES ---
        self.GITHUB_MOD_URL = "https://raw.githubusercontent.com/greeko2030-afk/Supersonic-client/main/renderculling-1.0.0.jar"
        self.CUSTOM_MOD_NAME = "renderculling-1.0.0.jar"

    def load_config(self):
        default_config = {
            "ram_mb": 8192,
            "username": "NarratorPlayer",
            "uuid": str(uuid.uuid4())
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default_config
        return default_config

    def save_config(self, key, value):
        self.config[key] = value
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception:
            pass

    def get_system_info(self):
        if PSUTIL_AVAILABLE:
            ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
        else:
            ram_gb = 16.0 
        return {
            "os": f"{platform.system()} {platform.release()}",
            "ram": f"{ram_gb} GB"
        }

    def generate_jvm_args(self):
        ram = self.config.get("ram_mb", 4096)
        return [
            f"-Xms{ram}M", f"-Xmx{ram}M",
            "-XX:+UseZGC", "-XX:+ZGenerational",
            "-XX:+AlwaysPreTouch", "-XX:+DisableExplicitGC",
            "-XX:+PerfDisableSharedMem", "-Djava.net.preferIPv4Stack=true",
            "-Dfile.encoding=UTF-8"
        ]
        
    def inject_github_mods(self, status_callback):
        """Automatically ensures your custom mods from GitHub are in the mods folder before launch"""
        mods_dir = os.path.join(self.minecraft_directory, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        
        mod_path = os.path.join(mods_dir, self.CUSTOM_MOD_NAME)
        
        if not os.path.exists(mod_path):
            status_callback(f"Status: Fetching {self.CUSTOM_MOD_NAME} from GitHub...")
            try:
                if REQUESTS_AVAILABLE:
                    response = requests.get(self.GITHUB_MOD_URL, stream=True, timeout=10)
                    if response.status_code == 200:
                        with open(mod_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk: f.write(chunk)
                        status_callback("Status: Custom Mod Injected!")
                    else:
                        print(f"Failed to download mod from GitHub. HTTP Status: {response.status_code}")
                else:
                    print("Requests library is not available, skipping mod download.")
            except Exception as e:
                print(f"GitHub Mod Injection Error: {e}")

    def launch_minecraft(self, status_callback):
        try:
            status_callback("Status: Preparing Fast Launch...")
            os.makedirs(self.minecraft_directory, exist_ok=True)

            callback_dict = {
                "setStatus": lambda s: status_callback(f"Status: {s}"),
                "setProgress": lambda p: None,
                "setMax": lambda m: None
            }

            version_folder = os.path.join(self.minecraft_directory, "versions", self.target_mc_version)
            if not os.path.exists(version_folder):
                status_callback(f"Status: Installing {self.target_mc_version}...")
                minecraft_launcher_lib.install.install_minecraft_version(
                    self.target_mc_version, self.minecraft_directory, callback=callback_dict
                )

            versions_dir = os.path.join(self.minecraft_directory, "versions")
            fabric_version_name = None
            if os.path.exists(versions_dir):
                for folder in os.listdir(versions_dir):
                    if folder.startswith("fabric-loader-") and folder.endswith(self.target_mc_version):
                        fabric_version_name = folder
                        break
            
            if not fabric_version_name:
                status_callback("Status: Installing Fabric Loader...")
                minecraft_launcher_lib.fabric.install_fabric(self.target_mc_version, self.minecraft_directory, callback=callback_dict)
                for folder in os.listdir(versions_dir):
                    if folder.startswith("fabric-loader-") and folder.endswith(self.target_mc_version):
                        fabric_version_name = folder
                        break
            
            launch_version = fabric_version_name if fabric_version_name else self.target_mc_version

            # --- INJECT GITHUB MODS HERE BEFORE LAUNCH ---
            self.inject_github_mods(status_callback)

            options = {
                "username": self.config["username"],
                "uuid": self.config["uuid"],
                "token": "",
                "jvmArguments": self.generate_jvm_args(),
                "launcherName": "Supersonic Client",
                "launcherVersion": "2.5.0"
            }

            cmd = minecraft_launcher_lib.command.get_minecraft_command(launch_version, self.minecraft_directory, options)
            status_callback("Status: Firing up Engine...")
            subprocess.Popen(cmd, creationflags=0x08000000 if platform.system() == "Windows" else 0)
            status_callback("Status: Game is Running!")

        except Exception as e:
            status_callback(f"Launch Error: {str(e)}")

    def download_and_install_project(self, project_slug, project_title, project_type, callback):
        """Automatically routes files to their respective Minecraft directories based on project type."""
        try:
            download_url, filename = ModrinthAPI.get_latest_version_file(
                project_slug, 
                mc_version=self.target_mc_version, 
                loader=self.target_loader,
                project_type=project_type
            )
            
            if not download_url:
                callback("Error", f"No valid {self.target_mc_version} version found for {project_title}.")
                return

            # Smart Directory Routing Map
            target_folders = {
                "mod": "mods",
                "shader": "shaderpacks",
                "resourcepack": "resourcepacks",
                "datapack": "datapacks",
                "modpack": "modpacks"
            }
            target_folder = target_folders.get(project_type, "downloads")
            
            install_dir = os.path.join(self.minecraft_directory, target_folder)
            os.makedirs(install_dir, exist_ok=True)
            filepath = os.path.join(install_dir, filename)

            # File Stream Download
            response = requests.get(download_url, stream=True)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
                callback("Success", f"{project_title} successfully installed to {target_folder} folder!")
            else:
                callback("Error", f"Failed to download stream. Status Code: {response.status_code}")
                
        except Exception as e:
            callback("Error", f"Installation failed: {str(e)}")


# ==============================================================================
# USER INTERFACE CONSTRUCTION (TOP TABS)
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

        # Main Layout: Row 0 is Top Nav, Row 1 is Main Content
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

    def show_popup(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("420x200")
        popup.attributes("-topmost", True)
        popup.configure(fg_color=CARD_BG)
        
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (420 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (200 // 2)
        popup.geometry(f"+{x}+{y}")

        lbl = ctk.CTkLabel(popup, text=message, font=("Segoe UI", 12), text_color=TEXT_PRIMARY, wraplength=380, justify="center")
        lbl.pack(pady=(25, 20), padx=20)
        
        ctk.CTkButton(popup, text="OK", fg_color=ACCENT_BLUE, width=100, command=popup.destroy).pack(side="bottom", pady=20)

    def format_downloads(self, num):
        if num >= 1000000: return f"{num/1000000:.1f}M"
        elif num >= 1000: return f"{num/1000:.1f}K"
        return str(num)

    def setup_top_nav(self):
        self.nav_bar = ctk.CTkFrame(self, height=60, fg_color=NAV_BG, corner_radius=0)
        self.nav_bar.grid(row=0, column=0, sticky="ew")
        
        # Logo on the left
        logo_frame = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        logo_frame.pack(side="left", padx=20, fill="y")
        ctk.CTkLabel(logo_frame, text="⚡ SUPERSONIC", font=("Segoe UI", 18, "bold"), text_color=ACCENT_BLUE).pack(side="left", pady=15)

        # Tabs in the center/right
        nav_items = ["Dashboard", "Mods", "Shaders", "Resourcepack", "Datapack"]
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
            if name == tab_name:
                btn.configure(fg_color=CARD_HOVER, text_color=ACCENT_BLUE)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)
                
        for tab in self.tabs.values():
            tab.grid_remove()
        
        if tab_name in self.tabs:
            self.tabs[tab_name].grid(row=0, column=0, sticky="nsew")

    def build_tabs(self):
        self.tabs["Dashboard"] = self.tab_dashboard()
        self.tabs["Mods"] = self.create_modrinth_tab("EXPLORE MODS", "mod")
        self.tabs["Shaders"] = self.create_modrinth_tab("EXPLORE SHADERS", "shader")
        self.tabs["Resourcepack"] = self.create_modrinth_tab("EXPLORE RESOURCE PACKS", "resourcepack")
        self.tabs["Datapack"] = self.create_modrinth_tab("EXPLORE DATA PACKS", "datapack")

    def start_game(self):
        self.play_btn.configure(state="disabled", text="LAUNCHING...")
        def update_label(msg):
            self.after(0, lambda: self.status_lbl.configure(text=msg))
            if "Error" in msg or "Game is Running" in msg:
                self.after(0, lambda: self.play_btn.configure(state="normal", text="▶ PLAY"))
        threading.Thread(target=self.engine.launch_minecraft, args=(update_label,), daemon=True).start()

    def install_project_thread(self, slug, title, p_type):
        self.show_popup("Downloading", f"Downloading {title}...\nPlease wait while stream is being saved.")
        def callback(status, message):
            self.after(0, lambda: self.show_popup(status, message))
        threading.Thread(
            target=self.engine.download_and_install_project, 
            args=(slug, title, p_type, callback), 
            daemon=True
        ).start()

    # --- DASHBOARD TAB (1st PAGE WITH CATEGORIES) ---
    def tab_dashboard(self):
        frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        hero = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 20), ipady=30)
        
        ctk.CTkLabel(hero, text="ADDONS HUB", font=("Segoe UI", 32, "bold", "italic")).place(x=30, y=20)
        ctk.CTkLabel(hero, text="Manage all your Mods, Shaders, and Resources from one place.", font=("Segoe UI", 14), text_color=TEXT_SECONDARY).place(x=30, y=65)
        
        info_bar = ctk.CTkFrame(hero, fg_color="transparent")
        info_bar.place(x=30, y=100)
        ctk.CTkLabel(info_bar, text=f"📦 Target: Minecraft {self.engine.target_mc_version}", font=("Segoe UI", 12), text_color=GREEN_STATUS).pack(side="left")
        
        self.play_btn = ctk.CTkButton(
            hero, text="▶ PLAY", font=("Segoe UI", 24, "bold"),
            fg_color=ACCENT_BLUE, hover_color="#1D40B0", width=200, height=60,
            command=self.start_game
        )
        self.play_btn.place(relx=0.95, rely=0.5, anchor="e")
        self.status_lbl = ctk.CTkLabel(hero, text=f"Status: Ready", font=("Segoe UI", 12), text_color=TEXT_SECONDARY)
        self.status_lbl.place(relx=0.95, rely=0.8, anchor="e")

        # Visual Categories Grid
        cat_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cat_frame.grid(row=1, column=0, sticky="nsew")
        cat_frame.grid_columnconfigure((0,1,2,3), weight=1)

        categories = [
            ("🧩 Mods", "Expand your game with new mechanics", "Mods"),
            ("📦 Modpacks", "Curated collections of mods", "Dashboard"),
            ("✨ Shaders", "Enhance visual fidelity and lighting", "Shaders"),
            ("🎨 Resourcepacks", "Change textures and sounds", "Resourcepack")
        ]

        for i, (title, desc, target_tab) in enumerate(categories):
            card = ctk.CTkFrame(cat_frame, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=0, column=i, sticky="nsew", padx=10, pady=10)
            
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 20, "bold")).pack(pady=(20, 5))
            ctk.CTkLabel(card, text=desc, font=("Segoe UI", 12), text_color=TEXT_SECONDARY, wraplength=180).pack(pady=(0, 20))
            ctk.CTkButton(card, text="Browse", fg_color="transparent", border_width=1, border_color=ACCENT_BLUE, text_color=ACCENT_BLUE,
                          command=lambda t=target_tab: self.switch_tab(t)).pack(pady=(0, 20))

        return frame

    # --- GENERIC TAB BUILDER FOR MODRINTH CATEGORIES ---
    def create_modrinth_tab(self, header_title, project_type):
        f = ctk.CTkFrame(self.main_area, fg_color="transparent")
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text=header_title, font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        
        refresh_btn = ctk.CTkButton(top, text="🔄 Refresh", fg_color="transparent", border_width=1, border_color=ACCENT_BLUE)
        refresh_btn.pack(side="right")

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        
        loading_lbl = ctk.CTkLabel(scroll, text=f"Fetching latest {project_type}s from Modrinth...", font=("Segoe UI", 14), text_color=TEXT_SECONDARY)
        loading_lbl.pack(pady=50)

        def load_projects():
            projects = ModrinthAPI.fetch_projects(project_type, limit=15)
            self.after(0, lambda: self.render_modrinth_rows(scroll, loading_lbl, projects, project_type))

        refresh_btn.configure(command=lambda: threading.Thread(target=load_projects, daemon=True).start())
        threading.Thread(target=load_projects, daemon=True).start()

        return f

    def render_modrinth_rows(self, parent_frame, loading_lbl, projects, project_type):
        loading_lbl.destroy()
        for widget in parent_frame.winfo_children(): widget.destroy()

        if not projects:
            ctk.CTkLabel(parent_frame, text="No projects found for this category.", text_color="#EF4444").pack(pady=20)
            return

        for p in projects:
            title = p.get("title", "Unknown")
            slug = p.get("slug", "")
            desc = p.get("description", "")[:90] + "..."
            dls = self.format_downloads(p.get("downloads", 0))
            
            row = ctk.CTkFrame(parent_frame, fg_color=CARD_BG, corner_radius=10, height=80)
            row.pack(fill="x", padx=10, pady=5)
            row.pack_propagate(False)
            
            ctk.CTkLabel(row, text=title, font=("Segoe UI", 15, "bold")).place(x=20, y=15)
            ctk.CTkLabel(row, text=f"{desc} | ⬇ {dls}", font=("Segoe UI", 12), text_color=TEXT_SECONDARY).place(x=20, y=40)
            
            ctk.CTkButton(
                row, text="Install", fg_color="transparent", border_width=1, border_color=GREEN_STATUS, text_color=GREEN_STATUS, width=100, 
                command=lambda s=slug, t=title, pt=project_type: self.install_project_thread(s, t, pt)
            ).place(relx=0.95, rely=0.5, anchor="e")


if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
