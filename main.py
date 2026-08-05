import os
import json
import uuid
import threading
import subprocess
import platform
import zipfile
import shutil
import tempfile
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
# API HANDLERS
# ==============================================================================

class ModrinthAPI:
    BASE_URL = "https://api.modrinth.com/v2"
    USER_AGENT = "SupersonicClient/2.5.0 (contact@narratormc.net)"

    @staticmethod
    def fetch_projects(project_type="mod", limit=15):
        if not REQUESTS_AVAILABLE:
            return []
            
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
    def get_latest_version_file(project_slug, mc_version="1.21.4", loader="fabric"):
        url = f"{ModrinthAPI.BASE_URL}/project/{project_slug}/version"
        params = {"game_versions": f'["{mc_version}"]', "loaders": f'["{loader}"]'}
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


class CustomModAPI:
    """Handler for your custom backend API to inject Render Culling"""
    BASE_URL = "https://supersonic-client--Greeko2030.replit.app/api/mods"

    @staticmethod
    def get_download_url(mod_id):
        return f"{BASE_URL}/file/{mod_id}"


# ==============================================================================
# ENGINE & CORE LOGIC (.mrpack Extractor & Installer)
# ==============================================================================
class SupersonicEngine:
    def __init__(self):
        self.config_file = "supersonic_config.json"
        self.config = self.load_config()
        self.system_info = self.get_system_info()
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.target_mc_version = "1.21.4"
        self.target_loader = "fabric"

    def load_config(self):
        default_config = {"ram_mb": 8192, "username": "NarratorPlayer", "uuid": str(uuid.uuid4())}
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
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 1) if PSUTIL_AVAILABLE else 16.0 
        return {"os": f"{platform.system()} {platform.release()}", "ram": f"{ram_gb} GB"}

    def generate_jvm_args(self):
        ram = self.config.get("ram_mb", 4096)
        return [
            f"-Xms{ram}M", f"-Xmx{ram}M",
            "-XX:+UseZGC", "-XX:+ZGenerational",
            "-Djava.net.preferIPv4Stack=true", "-Dfile.encoding=UTF-8"
        ]

    def launch_minecraft(self, status_callback):
        try:
            status_callback("Status: Preparing Fast Launch...")
            os.makedirs(self.minecraft_directory, exist_ok=True)
            callback_dict = {"setStatus": lambda s: status_callback(f"Status: {s}")}

            version_folder = os.path.join(self.minecraft_directory, "versions", self.target_mc_version)
            if not os.path.exists(version_folder):
                status_callback(f"Status: Installing {self.target_mc_version}...")
                minecraft_launcher_lib.install.install_minecraft_version(self.target_mc_version, self.minecraft_directory, callback=callback_dict)

            versions_dir = os.path.join(self.minecraft_directory, "versions")
            fabric_version_name = next((f for f in os.listdir(versions_dir) if f.startswith("fabric-loader-") and f.endswith(self.target_mc_version)), None)
            
            if not fabric_version_name:
                status_callback("Status: Installing Fabric Loader...")
                minecraft_launcher_lib.fabric.install_fabric(self.target_mc_version, self.minecraft_directory, callback=callback_dict)
                fabric_version_name = next((f for f in os.listdir(versions_dir) if f.startswith("fabric-loader-") and f.endswith(self.target_mc_version)), None)
            
            launch_version = fabric_version_name if fabric_version_name else self.target_mc_version
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
        """Downloads standard single files (mods, shaders, etc)."""
        try:
            download_url, filename = ModrinthAPI.get_latest_version_file(
                project_slug, mc_version=self.target_mc_version, loader=self.target_loader
            )
            
            if not download_url:
                callback("Error", f"No valid {self.target_mc_version} version found for {project_title}.")
                return

            target_folders = {"mod": "mods", "shader": "shaderpacks", "resourcepack": "resourcepacks", "datapack": "datapacks"}
            target_folder = target_folders.get(project_type, "downloads")
            
            install_dir = os.path.join(self.minecraft_directory, target_folder)
            os.makedirs(install_dir, exist_ok=True)
            filepath = os.path.join(install_dir, filename)

            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
                callback("Success", f"{project_title} successfully installed to {target_folder}/!")
            else:
                callback("Error", f"Failed to download. Code: {response.status_code}")
                
        except Exception as e:
            callback("Error", f"Installation failed: {str(e)}")

    def install_modpack_and_inject_custom(self, project_slug, project_title, callback):
        """Downloads .mrpack, extracts to REAL folders, and auto-injects Render Culling."""
        try:
            callback("Processing", f"Fetching {project_title} Modpack Metadata...")
            download_url, filename = ModrinthAPI.get_latest_version_file(
                project_slug, mc_version=self.target_mc_version, loader=self.target_loader
            )
            
            if not download_url:
                callback("Error", f"No valid version found for {project_title}.")
                return

            mrpack_path = os.path.join(self.minecraft_directory, filename)
            
            # 1. Download the .mrpack file
            callback("Processing", f"Downloading {filename}...")
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                with open(mrpack_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
            else:
                callback("Error", "Failed to download the .mrpack file.")
                return

            # 2. Extract and Parse .mrpack
            callback("Processing", "Extracting modpack environment...")
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(mrpack_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                
                index_path = os.path.join(tmpdir, "modrinth.index.json")
                with open(index_path, 'r') as f:
                    index_data = json.load(f)
                
                files = index_data.get('files', [])
                total_files = len(files)
                
                # 3. Download all mods/shaders/resources to their REAL folders
                for i, file_info in enumerate(files):
                    if 'env' in file_info and file_info['env'].get('client') == 'unsupported':
                        continue # Skip server-side only mods
                        
                    dl_urls = file_info.get('downloads', [])
                    if not dl_urls:
                        continue
                        
                    file_dl_url = dl_urls[0]
                    target_path = os.path.join(self.minecraft_directory, file_info['path'])
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    callback("Processing", f"Downloading ({i+1}/{total_files}):\n{os.path.basename(target_path)}")
                    
                    dl_resp = requests.get(file_dl_url, stream=True)
                    if dl_resp.status_code == 200:
                        with open(target_path, 'wb') as out_f:
                            for chunk in dl_resp.iter_content(chunk_size=8192):
                                if chunk: out_f.write(chunk)
                
                # 4. Copy Overrides (configs, options.txt, etc.)
                callback("Processing", "Applying config overrides...")
                overrides_dir = os.path.join(tmpdir, index_data.get('overrides', 'overrides'))
                if os.path.exists(overrides_dir):
                    shutil.copytree(overrides_dir, self.minecraft_directory, dirs_exist_ok=True)

            # Clean up the .mrpack zip
            if os.path.exists(mrpack_path):
                os.remove(mrpack_path)

            # 5. Inject Custom Mod (Render Culling) automatically
            callback("Processing", "Injecting Custom Mod: Render Culling...")
            custom_url = CustomModAPI.get_download_url(3)
            custom_target = os.path.join(self.minecraft_directory, "mods", "render-culling.jar")
            
            c_resp = requests.get(custom_url, stream=True)
            if c_resp.status_code == 200:
                with open(custom_target, 'wb') as c_file:
                    for chunk in c_resp.iter_content(chunk_size=8192):
                        if chunk: c_file.write(chunk)
                callback("Success", f"{project_title} fully installed!\nRender Culling auto-injected into mods folder.")
            else:
                callback("Success", f"{project_title} installed, but failed to inject Render Culling (Server Error 500).")

        except Exception as e:
            callback("Error", f"Modpack installation crashed: {str(e)}")


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

    def show_progress_popup(self, status, message):
        """A dynamic popup that updates itself to prevent window spam during Modpack install."""
        if not hasattr(self, 'progress_popup') or not self.progress_popup.winfo_exists():
            self.progress_popup = ctk.CTkToplevel(self)
            self.progress_popup.title("Engine Task")
            self.progress_popup.geometry("450x220")
            self.progress_popup.attributes("-topmost", True)
            self.progress_popup.configure(fg_color=CARD_BG)
            
            self.progress_popup.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() // 2) - (450 // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (220 // 2)
            self.progress_popup.geometry(f"+{x}+{y}")

            self.progress_lbl = ctk.CTkLabel(self.progress_popup, text=message, font=("Segoe UI", 12), text_color=TEXT_PRIMARY, wraplength=400, justify="center")
            self.progress_lbl.pack(pady=(35, 20), padx=20)
            
            self.progress_btn = ctk.CTkButton(self.progress_popup, text="Please Wait...", fg_color=ACCENT_BLUE, width=120, state="disabled", command=self.progress_popup.destroy)
            self.progress_btn.pack(side="bottom", pady=20)

        self.progress_popup.title(status)
        self.progress_lbl.configure(text=message)

        if status in ["Success", "Error"]:
            self.progress_btn.configure(state="normal", text="OK")

    def format_downloads(self, num):
        if num >= 1000000: return f"{num/1000000:.1f}M"
        elif num >= 1000: return f"{num/1000:.1f}K"
        return str(num)

    def setup_top_nav(self):
        self.nav_bar = ctk.CTkFrame(self, height=60, fg_color=NAV_BG, corner_radius=0)
        self.nav_bar.grid(row=0, column=0, sticky="ew")
        
        logo_frame = ctk.CTkFrame(self.nav_bar, fg_color="transparent")
        logo_frame.pack(side="left", padx=20, fill="y")
        ctk.CTkLabel(logo_frame, text="⚡ SUPERSONIC", font=("Segoe UI", 18, "bold"), text_color=ACCENT_BLUE).pack(side="left", pady=15)

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
        self.show_progress_popup("Processing", f"Initializing {title}...")
        def callback(status, message):
            self.after(0, lambda: self.show_progress_popup(status, message))
        threading.Thread(target=self.engine.download_and_install_project, args=(slug, title, p_type, callback), daemon=True).start()

    def install_modpack_thread(self, slug, title):
        self.show_progress_popup("Processing", f"Initializing Modpack: {title}...")
        def callback(status, message):
            self.after(0, lambda: self.show_progress_popup(status, message))
        threading.Thread(target=self.engine.install_modpack_and_inject_custom, args=(slug, title, callback), daemon=True).start()

    # --- DASHBOARD TAB ---
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

        cat_frame = ctk.CTkFrame(frame, fg_color="transparent")
        cat_frame.grid(row=1, column=0, sticky="nsew")
        cat_frame.grid_columnconfigure((0,1,2,3), weight=1)

        categories = [
            ("🧩 Mods", "Expand your game with new mechanics", "Mods"),
            ("📦 Modpacks", "Install FO + Auto Custom Mods", "fabulously-optimized"), # Special trigger
            ("✨ Shaders", "Enhance visual fidelity and lighting", "Shaders"),
            ("🎨 Resourcepacks", "Change textures and sounds", "Resourcepack")
        ]

        for i, (title, desc, action) in enumerate(categories):
            card = ctk.CTkFrame(cat_frame, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
            card.grid(row=0, column=i, sticky="nsew", padx=10, pady=10)
            
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 20, "bold")).pack(pady=(20, 5))
            ctk.CTkLabel(card, text=desc, font=("Segoe UI", 12), text_color=TEXT_SECONDARY, wraplength=180).pack(pady=(0, 20))
            
            btn = ctk.CTkButton(card, text="Browse" if i != 1 else "Install FO Suite", fg_color="transparent", border_width=1, border_color=ACCENT_BLUE, text_color=ACCENT_BLUE)
            
            # Setup specific routing for Modpacks to trigger the new mrpack installer directly
            if title == "📦 Modpacks":
                btn.configure(command=lambda s=action: self.install_modpack_thread(s, "Fabulously Optimized"))
            else:
                btn.configure(command=lambda t=action: self.switch_tab(t))
                
            btn.pack(pady=(0, 20))

        return frame

    # --- MODRINTH CATEGORY TABS ---
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
        
        loading_lbl = ctk.CTkLabel(scroll, text=f"Fetching {project_type}s from Modrinth...", font=("Segoe UI", 14), text_color=TEXT_SECONDARY)
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
            ctk.CTkLabel(parent_frame, text="No projects found.", text_color="#EF4444").pack(pady=20)
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
