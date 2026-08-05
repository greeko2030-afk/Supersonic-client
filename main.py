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
# API HANDLERS (MODRINTH & CUSTOM REPLIT API)
# ==============================================================================

class ModrinthAPI:
    BASE_URL = "https://api.modrinth.com/v2"
    USER_AGENT = "SupersonicClient/2.5.0 (contact@narratormc.net)"

    @staticmethod
    def fetch_projects(project_type="mod", limit=12):
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
    def get_latest_version_file(project_slug, mc_version="1.21.4", loader="fabric"):
        url = f"{ModrinthAPI.BASE_URL}/project/{project_slug}/version"
        params = {"loaders": f'["{loader}"]', "game_versions": f'["{mc_version}"]'}
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
    """Handler for the custom Replit Hosted Backend API"""
    BASE_URL = "https://supersonic-client--Greeko2030.replit.app/api/mods"

    @staticmethod
    def fetch_projects(search=None, category=None):
        if not REQUESTS_AVAILABLE:
            return []
        
        params = {}
        if search: params['search'] = search
        if category: params['category'] = category
        
        try:
            response = requests.get(CustomModAPI.BASE_URL, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("mods", [])
            return []
        except Exception as e:
            print(f"Custom API Error: {e}")
            return []

    @staticmethod
    def get_download_url(mod_id):
        return f"{CustomModAPI.BASE_URL}/file/{mod_id}"


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

    def reset_config(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        self.config = self.load_config()

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
            options = {
                "username": self.config["username"],
                "uuid": self.config["uuid"],
                "token": "",
                "jvmArguments": self.generate_jvm_args(),
                "launcherName": "Supersonic Client",
                "launcherVersion": "2.5.0"
            }

            cmd = minecraft_launcher_lib.command.get_minecraft_command(launch_version, self.minecraft_directory, options)
            status_callback("Status: Firing up the Game Engine...")
            subprocess.Popen(cmd, creationflags=0x08000000 if platform.system() == "Windows" else 0)
            status_callback("Status: Game is Running!")

        except Exception as e:
            status_callback(f"Launch Error: {str(e)}")

    def download_and_install_project(self, project_slug, project_title, project_type, source, callback, custom_mod_id=None):
        """Unified downloader for Modrinth and Custom API."""
        try:
            download_url = None
            filename = None

            if source == "modrinth":
                download_url, filename = ModrinthAPI.get_latest_version_file(
                    project_slug, mc_version=self.target_mc_version, loader=self.target_loader
                )
                if not download_url:
                    callback("Error", f"No valid {self.target_mc_version} Fabric version found on Modrinth.")
                    return

            elif source == "custom":
                if custom_mod_id is None:
                    callback("Error", "Missing mod ID for Custom API. Data might be corrupted.")
                    return
                download_url = CustomModAPI.get_download_url(custom_mod_id)
                filename = f"{project_slug}-{self.target_mc_version}.jar" 
                
            else:
                callback("Error", "Unknown source provided.")
                return

            target_folder = "mods" if project_type == "mod" else "modpacks"
            install_dir = os.path.join(self.minecraft_directory, target_folder)
            os.makedirs(install_dir, exist_ok=True)
            
            filepath = os.path.join(install_dir, filename)
            if os.path.exists(filepath):
                callback("Info", f"{project_title} is already installed!")
                return

            # Request execution
            response = requests.get(download_url, stream=True)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                callback("Success", f"{project_title} has been installed from {source.capitalize()}!")
            else:
                # Enhanced Error Logging for Debugging Server Issues (HTTP 500)
                error_msg = f"Failed to download. Status: {response.status_code}"
                if response.status_code == 500:
                    server_response = response.text[:100] if response.text else "No extra details."
                    error_msg += f"\n\nServer Error 500: Please check your Replit logs.\nURL Hit: {download_url}\nResponse: {server_response}"
                elif response.status_code == 404:
                    error_msg += f"\n\nFile not found on server.\nURL Hit: {download_url}"
                    
                callback("Error", error_msg)
                
        except Exception as e:
            callback("Error", f"Installation failed: {str(e)}")


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
SIDEBAR_BG = "#0A0D14"
BORDER_COLOR = "#1E293B"
CUSTOM_BRAND_COLOR = "#F59E0B"

class SupersonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.engine = SupersonicEngine()
        
        self.title("SUPERSONIC CLIENT v2.5.0")
        self.geometry("1100x750")
        self.configure(fg_color=BG_DARK)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.tabs = {}
        self.build_tabs()
        self.switch_tab("Dashboard")

    def show_popup(self, title, message):
        popup = ctk.CTkToplevel(self)
        popup.title(title)
        popup.geometry("450x220") # Increased size for longer error messages
        popup.attributes("-topmost", True)
        popup.configure(fg_color=CARD_BG)
        
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (450 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (220 // 2)
        popup.geometry(f"+{x}+{y}")

        lbl = ctk.CTkLabel(popup, text=message, font=("Segoe UI", 12), text_color=TEXT_PRIMARY, wraplength=400, justify="left")
        lbl.pack(pady=(20, 20), padx=20)
        
        ctk.CTkButton(popup, text="OK", fg_color=ACCENT_BLUE, width=100, command=popup.destroy).pack(side="bottom", pady=20)

    def format_downloads(self, num):
        if num >= 1000000: return f"{num/1000000:.1f}M"
        elif num >= 1000: return f"{num/1000:.1f}K"
        return str(num)

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=SIDEBAR_BG, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, pady=(30, 30), padx=20, sticky="w")
        ctk.CTkLabel(logo_frame, text="⚡", font=("Segoe UI", 28), text_color=ACCENT_BLUE).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(logo_frame, text="SUPERSONIC", font=("Segoe UI", 18, "bold")).pack(side="left")

        nav_items = [
            ("Dashboard", "🏠"), 
            ("Custom Mods", "⭐"), 
            ("Modrinth Mods", "⚡"), 
            ("Settings", "⚙️")
        ]

        self.nav_buttons = {}
        for i, (name, icon) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icon}   {name}", anchor="w", fg_color="transparent",
                text_color=TEXT_SECONDARY, hover_color=CARD_HOVER, font=("Segoe UI", 14, "bold"),
                height=40, command=lambda n=name: self.switch_tab(n)
            )
            btn.grid(row=i+1, column=0, sticky="ew", padx=15, pady=5)
            self.nav_buttons[name] = btn

    def switch_tab(self, tab_name):
        for name, btn in self.nav_buttons.items():
            btn.configure(
                fg_color=CARD_HOVER if name == tab_name else "transparent",
                text_color=ACCENT_BLUE if name == tab_name else TEXT_SECONDARY
            )
        for tab in self.tabs.values():
            tab.grid_remove()
        
        if tab_name in self.tabs:
            self.tabs[tab_name].grid(row=1, column=0, sticky="nsew")

    def build_tabs(self):
        self.tabs["Dashboard"] = self.tab_dashboard()
        self.tabs["Custom Mods"] = self.tab_custom_mods()
        self.tabs["Modrinth Mods"] = self.tab_modrinth_mods()
        self.tabs["Settings"] = self.tab_settings()

    def start_game(self):
        self.play_btn.configure(state="disabled", text="LAUNCHING...")
        def update_label(msg):
            self.after(0, lambda: self.status_lbl.configure(text=msg))
            if "Error" in msg or "Game is Running" in msg:
                self.after(0, lambda: self.play_btn.configure(state="normal", text="▶ PLAY"))
        threading.Thread(target=self.engine.launch_minecraft, args=(update_label,), daemon=True).start()

    def install_project_thread(self, slug, title, p_type, source="modrinth", custom_mod_id=None):
        self.show_popup("Downloading", f"Fetching {title} from {source.capitalize()}...\nPlease wait.")
        def callback(status, message):
            self.after(0, lambda: self.show_popup(status, message))
        threading.Thread(
            target=self.engine.download_and_install_project, 
            args=(slug, title, p_type, source, callback, custom_mod_id), 
            daemon=True
        ).start()

    # --- DASHBOARD TAB ---
    def tab_dashboard(self):
        frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        hero = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 20), ipady=30)
        
        ctk.CTkLabel(hero, text="SUPERSONIC CLIENT", font=("Segoe UI", 32, "bold", "italic")).place(x=30, y=20)
        ctk.CTkLabel(hero, text="Hyper optimized. Ultra fast. Future ready.", font=("Segoe UI", 14), text_color=TEXT_SECONDARY).place(x=30, y=65)
        
        info_bar = ctk.CTkFrame(hero, fg_color="transparent")
        info_bar.place(x=30, y=100)
        ctk.CTkLabel(info_bar, text=f"📦 Minecraft {self.engine.target_mc_version}   🚀 Ultra Mode", font=("Segoe UI", 12), text_color=GREEN_STATUS).pack(side="left")
        
        self.play_btn = ctk.CTkButton(
            hero, text="▶ PLAY", font=("Segoe UI", 24, "bold"),
            fg_color=ACCENT_BLUE, hover_color="#1D40B0", width=200, height=60,
            command=self.start_game
        )
        self.play_btn.place(relx=0.95, rely=0.5, anchor="e")
        self.status_lbl = ctk.CTkLabel(hero, text=f"Status: Ready", font=("Segoe UI", 12), text_color=TEXT_SECONDARY)
        self.status_lbl.place(relx=0.95, rely=0.8, anchor="e")

        return frame

    # --- CUSTOM MODS TAB (YOUR REPLIT API) ---
    def tab_custom_mods(self):
        f = ctk.CTkFrame(self.main_area, fg_color="transparent")
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text="EXCLUSIVE MODS (CUSTOM)", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        
        refresh_btn = ctk.CTkButton(top, text="🔄 Refresh", fg_color="transparent", border_width=1, border_color=CUSTOM_BRAND_COLOR)
        refresh_btn.pack(side="right")

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        
        loading_lbl = ctk.CTkLabel(scroll, text="Fetching Custom Mods from your server...", font=("Segoe UI", 14), text_color=TEXT_SECONDARY)
        loading_lbl.pack(pady=50)

        def load_custom_mods():
            projects = CustomModAPI.fetch_projects()
            self.after(0, lambda: self.render_custom_rows(scroll, loading_lbl, projects))

        refresh_btn.configure(command=lambda: threading.Thread(target=load_custom_mods, daemon=True).start())
        threading.Thread(target=load_custom_mods, daemon=True).start()

        return f

    def render_custom_rows(self, parent_frame, loading_lbl, projects):
        loading_lbl.destroy()
        for widget in parent_frame.winfo_children(): widget.destroy()

        if not projects:
            ctk.CTkLabel(parent_frame, text="No custom mods found on your server.", text_color=TEXT_SECONDARY).pack(pady=20)
            return

        for p in projects:
            # Fallback for ID if 'id' is not present but '_id' is (common in MongoDB)
            mod_id = p.get("id") or p.get("_id")
            title = p.get("name", "Unknown Mod")
            slug = p.get("slug", title.lower().replace(" ", "-"))
            desc = p.get("description", "No description provided.")[:80] + "..."
            version = p.get("version", "v1.0")
            category = p.get("category", "Mod")
            
            row = ctk.CTkFrame(parent_frame, fg_color=CARD_BG, corner_radius=10, height=80)
            row.pack(fill="x", padx=10, pady=5)
            row.pack_propagate(False)
            
            ctk.CTkLabel(row, text=f"{title} ({version})", font=("Segoe UI", 14, "bold")).place(x=20, y=15)
            ctk.CTkLabel(row, text=f"[{category.upper()}] {desc}", font=("Segoe UI", 11), text_color=TEXT_SECONDARY).place(x=20, y=40)
            
            ctk.CTkButton(
                row, text="Download", fg_color=CUSTOM_BRAND_COLOR, hover_color="#D97706", text_color="#000", width=100, 
                command=lambda s=slug, t=title, mid=mod_id: self.install_project_thread(s, t, "mod", source="custom", custom_mod_id=mid)
            ).place(relx=0.95, rely=0.5, anchor="e")

    # --- MODRINTH MODS TAB ---
    def tab_modrinth_mods(self):
        f = ctk.CTkFrame(self.main_area, fg_color="transparent")
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text="GLOBAL MODS (MODRINTH)", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        
        refresh_btn = ctk.CTkButton(top, text="🔄 Refresh", fg_color="transparent", border_width=1, border_color=ACCENT_BLUE)
        refresh_btn.pack(side="right")

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        
        loading_lbl = ctk.CTkLabel(scroll, text="Fetching from Modrinth API...", font=("Segoe UI", 14), text_color=TEXT_SECONDARY)
        loading_lbl.pack(pady=50)

        def load_mods():
            projects = ModrinthAPI.fetch_projects("mod", limit=12)
            self.after(0, lambda: self.render_modrinth_rows(scroll, loading_lbl, projects))

        refresh_btn.configure(command=lambda: threading.Thread(target=load_mods, daemon=True).start())
        threading.Thread(target=load_mods, daemon=True).start()

        return f

    def render_modrinth_rows(self, parent_frame, loading_lbl, projects):
        loading_lbl.destroy()
        for widget in parent_frame.winfo_children(): widget.destroy()

        if not projects:
            ctk.CTkLabel(parent_frame, text="No projects found.", text_color="#EF4444").pack(pady=20)
            return

        for p in projects:
            title = p.get("title", "Unknown")
            slug = p.get("slug", "")
            desc = p.get("description", "")[:80] + "..."
            dls = self.format_downloads(p.get("downloads", 0))
            
            row = ctk.CTkFrame(parent_frame, fg_color=CARD_BG, corner_radius=10, height=80)
            row.pack(fill="x", padx=10, pady=5)
            row.pack_propagate(False)
            
            ctk.CTkLabel(row, text=title, font=("Segoe UI", 14, "bold")).place(x=20, y=15)
            ctk.CTkLabel(row, text=f"{desc} | ⬇ {dls}", font=("Segoe UI", 11), text_color=TEXT_SECONDARY).place(x=20, y=40)
            
            ctk.CTkButton(
                row, text="Install", fg_color="transparent", border_width=1, border_color=GREEN_STATUS, text_color=GREEN_STATUS, width=100, 
                command=lambda s=slug, t=title: self.install_project_thread(s, t, "mod", source="modrinth")
            ).place(relx=0.95, rely=0.5, anchor="e")

    # --- SETTINGS TAB ---
    def tab_settings(self):
        f = ctk.CTkFrame(self.main_area, fg_color="transparent")
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text="SETTINGS", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")

        card1 = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=12)
        card1.pack(fill="x", padx=10, pady=10, ipady=10)
        
        row1 = ctk.CTkFrame(card1, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(row1, text="Username", font=("Segoe UI", 13, "bold")).pack(side="left")
        username_entry = ctk.CTkEntry(row1, width=200, fg_color=BORDER_COLOR)
        username_entry.insert(0, self.engine.config.get("username", "Player"))
        username_entry.pack(side="right")

        return f

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
