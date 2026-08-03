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
# MODRINTH API HANDLER
# ==============================================================================
class ModrinthAPI:
    BASE_URL = "https://api.modrinth.com/v2"
    USER_AGENT = "SupersonicClient/2.5.0 (contact@narratormc.net)"

    @staticmethod
    def fetch_projects(project_type="mod", limit=12):
        if not REQUESTS_AVAILABLE:
            return [{"title": "Error", "description": "Please 'pip install requests' to use Modrinth API.", "downloads": 0}]
            
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
            else:
                print(f"Modrinth API Error: Status {response.status_code}")
                return []
        except Exception as e:
            print(f"Modrinth Connection Error: {e}")
            return []

    @staticmethod
    def get_latest_version_file(project_slug, mc_version="1.21.4", loader="fabric"):
        """Fetches the actual download URL for the latest matching mod version."""
        url = f"{ModrinthAPI.BASE_URL}/project/{project_slug}/version"
        params = {
            "loaders": f'["{loader}"]',
            "game_versions": f'["{mc_version}"]'
        }
        headers = {"User-Agent": ModrinthAPI.USER_AGENT}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                versions = response.json()
                if not versions:
                    return None, None
                
                # Get the first (latest) version's primary file
                files = versions[0].get('files', [])
                primary_file = next((f for f in files if f.get('primary')), files[0] if files else None)
                
                if primary_file:
                    return primary_file['url'], primary_file['filename']
            return None, None
        except Exception as e:
            print(f"Failed to fetch version info: {e}")
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
        self.is_premium = False

    def load_config(self):
        default_config = {
            "ram_mb": 8192,
            "performance_mode": "Ultra",
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
        except Exception as e:
            print(f"[Error] Failed to save config: {e}")

    def reset_config(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        self.config = self.load_config()

    def get_system_info(self):
        if PSUTIL_AVAILABLE:
            ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
        else:
            ram_gb = 16.0 

        try:
            if platform.system() == "Windows":
                gpu = subprocess.check_output(
                    "wmic path win32_videocard get name", shell=True
                ).decode(errors="ignore").split('\n')[1].strip()
            else:
                gpu = "Metal/Vulkan GPU"
        except Exception:
            gpu = "Auto GPU Detection Fallback"
            
        return {
            "os": f"{platform.system()} {platform.release()}",
            "cpu": platform.processor()[:30] if platform.processor() else "Unknown CPU",
            "ram": f"{ram_gb} GB",
            "gpu": gpu
        }

    def generate_jvm_args(self):
        """Max Optimized Java Arguments for Modern Minecraft (ZGC / High Performance)"""
        ram = self.config.get("ram_mb", 4096)
        return [
            f"-Xms{ram}M", f"-Xmx{ram}M",
            "-XX:+UseZGC",                     # Best for modern Minecraft, eliminates micro-stutters
            "-XX:+ZGenerational",              # Generational ZGC (Java 21+)
            "-XX:+AlwaysPreTouch",             # Pre-allocates RAM for faster in-game performance
            "-XX:+DisableExplicitGC",          # Prevents external GC calls that cause lag spikes
            "-XX:+PerfDisableSharedMem",       # Prevents disk I/O blocks during GC
            "-Djava.net.preferIPv4Stack=true", # Better networking
            "-Dfile.encoding=UTF-8"
        ]

    def launch_minecraft(self, status_callback):
        try:
            status_callback("Status: Preparing Fast Launch...")
            
            if not os.path.exists(self.minecraft_directory):
                os.makedirs(self.minecraft_directory, exist_ok=True)

            def set_status(status):
                status_callback(f"Status: {status}")

            callback_dict = {
                "setStatus": set_status,
                "setProgress": lambda p: None,
                "setMax": lambda m: None
            }

            # VANILLA CHECK
            version_folder = os.path.join(self.minecraft_directory, "versions", self.target_mc_version)
            if not os.path.exists(version_folder):
                status_callback(f"Status: Installing {self.target_mc_version} (Vanilla Base)...")
                minecraft_launcher_lib.install.install_minecraft_version(
                    version=self.target_mc_version,
                    minecraft_directory=self.minecraft_directory,
                    callback=callback_dict
                )
            else:
                status_callback("Status: Vanilla Base found! Proceeding...")

            # FABRIC CHECK & INSTALLATION (Required for Mods)
            status_callback("Status: Checking Fabric Loader...")
            versions_dir = os.path.join(self.minecraft_directory, "versions")
            os.makedirs(versions_dir, exist_ok=True)
            
            fabric_version_name = None
            # Search for already installed fabric for this version
            for folder in os.listdir(versions_dir):
                if folder.startswith("fabric-loader-") and folder.endswith(self.target_mc_version):
                    fabric_version_name = folder
                    break
            
            # Install Fabric if not found
            if not fabric_version_name:
                status_callback("Status: Installing Fabric Loader for Addons...")
                minecraft_launcher_lib.fabric.install_fabric(self.target_mc_version, self.minecraft_directory, callback=callback_dict)
                
                # Fetch the installed folder name
                for folder in os.listdir(versions_dir):
                    if folder.startswith("fabric-loader-") and folder.endswith(self.target_mc_version):
                        fabric_version_name = folder
                        break
            
            launch_version = fabric_version_name if fabric_version_name else self.target_mc_version

            status_callback(f"Status: Generating Launch Command ({launch_version})...")
            options = {
                "username": self.config["username"],
                "uuid": self.config["uuid"],
                "token": "",
                "jvmArguments": self.generate_jvm_args(),
                "launcherName": "Supersonic Client",
                "launcherVersion": "2.5.0"
            }

            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
                version=launch_version,
                minecraft_directory=self.minecraft_directory,
                options=options
            )

            status_callback("Status: Firing up the Game Engine...")
            
            subprocess.Popen(
                minecraft_command,
                creationflags=0x08000000 if platform.system() == "Windows" else 0
            )
            status_callback("Status: Game is Running!")

        except Exception as e:
            error_msg = str(e)
            if "FileNotFoundError" in error_msg or "java" in error_msg.lower():
                status_callback("Error: Java 21+ is not installed or not in PATH!")
            else:
                status_callback(f"Launch Error: {error_msg}")

    def download_and_install_project(self, project_slug, project_title, project_type, callback):
        """Actually downloads the mod/modpack into the Minecraft directory."""
        try:
            download_url, filename = ModrinthAPI.get_latest_version_file(
                project_slug, 
                mc_version=self.target_mc_version, 
                loader=self.target_loader
            )
            
            if not download_url:
                callback("Error", f"No valid {self.target_mc_version} Fabric version found for {project_title}.")
                return

            target_folder = "mods" if project_type == "mod" else "modpacks"
            install_dir = os.path.join(self.minecraft_directory, target_folder)
            os.makedirs(install_dir, exist_ok=True)
            
            filepath = os.path.join(install_dir, filename)
            
            # Skip if already downloaded
            if os.path.exists(filepath):
                callback("Info", f"{project_title} is already installed in your {target_folder} folder!")
                return

            # Download the file
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                callback("Success", f"{project_title} has been successfully installed to {target_folder}!")
            else:
                callback("Error", f"Failed to download {project_title}. Status code: {response.status_code}")
                
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
        popup.geometry("350x150")
        popup.attributes("-topmost", True)
        popup.configure(fg_color=CARD_BG)
        
        popup.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (350 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (150 // 2)
        popup.geometry(f"+{x}+{y}")

        ctk.CTkLabel(popup, text=message, font=("Segoe UI", 14), text_color=TEXT_PRIMARY, wraplength=300).pack(pady=(30, 20))
        ctk.CTkButton(popup, text="OK", fg_color=ACCENT_BLUE, width=100, command=popup.destroy).pack()

    def format_downloads(self, num):
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
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
            ("Modpacks", "📦"),
            ("Addons", "⚡"), 
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

        acc = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        acc.grid(row=11, column=0, sticky="ew", padx=20, pady=10)
        ctk.CTkLabel(acc, text="Account", font=("Segoe UI", 11), text_color=TEXT_SECONDARY).pack(anchor="w")
        ctk.CTkLabel(acc, text=self.engine.config["username"], font=("Segoe UI", 14, "bold")).pack(anchor="w")
        
        ctk.CTkButton(self.sidebar, text="Sign Out", fg_color="transparent", text_color="#EF4444", hover_color="#3F1616", command=lambda: self.show_popup("Sign Out", "Successfully signed out of the current account.")).grid(row=12, column=0, pady=(0, 20))

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
        self.tabs["Modpacks"] = self.tab_modpacks()
        self.tabs["Addons"] = self.tab_addons()
        self.tabs["Settings"] = self.tab_settings()

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
        ctk.CTkLabel(info_bar, text=f"📦 Minecraft {self.engine.target_mc_version}   🚀 Ultra Mode   📅 Ready", font=("Segoe UI", 12), text_color=GREEN_STATUS).pack(side="left")
        
        self.play_btn = ctk.CTkButton(
            hero, text="▶ PLAY", font=("Segoe UI", 24, "bold"),
            fg_color=ACCENT_BLUE, hover_color="#1D40B0", width=200, height=60,
            corner_radius=8, command=self.start_game
        )
        self.play_btn.place(relx=0.95, rely=0.5, anchor="e")
        self.status_lbl = ctk.CTkLabel(hero, text=f"Status: Ready to Launch ({self.engine.target_mc_version})", font=("Segoe UI", 12), text_color=TEXT_SECONDARY)
        self.status_lbl.place(relx=0.95, rely=0.8, anchor="e")

        addons_frame = ctk.CTkFrame(frame, fg_color=CARD_BG, corner_radius=12)
        addons_frame.grid(row=1, column=0, sticky="nsew")
        
        top_a = ctk.CTkFrame(addons_frame, fg_color="transparent")
        top_a.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(top_a, text="⚡ QUICK INSTALL: ESSENTIALS", font=("Segoe UI", 14, "bold")).pack(side="left")

        scroll = ctk.CTkScrollableFrame(addons_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        quick_addons = [
            ("sodium", "Sodium", "Boosts FPS massively"), 
            ("iris", "Iris Shaders", "Shaders Mod Support"), 
            ("lithium", "Lithium", "Performance Fixes"), 
            ("indium", "Indium", "Mod Compatibility")
        ]
        
        r, c = 0, 0
        for slug, name, desc in quick_addons:
            card = ctk.CTkFrame(scroll, fg_color="#151B28", corner_radius=8, width=200, height=80)
            card.grid(row=r, column=c, padx=10, pady=10)
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 13, "bold")).place(x=15, y=10)
            ctk.CTkLabel(card, text=desc, font=("Segoe UI", 11), text_color=TEXT_SECONDARY).place(x=15, y=30)
            
            btn = ctk.CTkButton(card, text="Install", height=24, width=60, font=("Segoe UI", 10), 
                                command=lambda s=slug, n=name: self.install_project_thread(s, n, "mod"))
            btn.place(x=15, y=50)
            
            c += 1
            if c > 3: c, r = 0, r + 1

        return frame

    def start_game(self):
        self.play_btn.configure(state="disabled", text="LAUNCHING...")
        def update_label(msg):
            self.after(0, lambda: self.status_lbl.configure(text=msg))
            if "Error" in msg or "Game is Running" in msg:
                self.after(0, lambda: self.play_btn.configure(state="normal", text="▶ PLAY"))

        threading.Thread(target=self.engine.launch_minecraft, args=(update_label,), daemon=True).start()

    def install_project_thread(self, slug, title, p_type):
        """Runs the actual download in a background thread."""
        self.show_popup("Downloading", f"Fetching {title} from Modrinth API...\nPlease wait.")
        
        def callback(status, message):
            self.after(0, lambda: self.show_popup(status, message))

        threading.Thread(target=self.engine.download_and_install_project, args=(slug, title, p_type, callback), daemon=True).start()

    # --- MODPACKS TAB (MODRINTH API) ---
    def tab_modpacks(self):
        f = ctk.CTkFrame(self.main_area, fg_color="transparent")
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text="MODPACKS (MODRINTH)", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        
        refresh_btn = ctk.CTkButton(top, text="🔄 Refresh", fg_color="transparent", border_width=1, border_color=ACCENT_BLUE)
        refresh_btn.pack(side="right")
        
        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        
        loading_lbl = ctk.CTkLabel(scroll, text="Fetching Modpacks from Modrinth API...", font=("Segoe UI", 14), text_color=TEXT_SECONDARY)
        loading_lbl.pack(pady=50)

        def load_modpacks():
            projects = ModrinthAPI.fetch_projects("modpack", limit=12)
            self.after(0, lambda: self.render_modrinth_cards(scroll, loading_lbl, projects, "Install Pack", "modpack"))

        refresh_btn.configure(command=lambda: threading.Thread(target=load_modpacks, daemon=True).start())
        threading.Thread(target=load_modpacks, daemon=True).start()

        return f

    # --- ADDONS TAB (MODRINTH API) ---
    def tab_addons(self):
        f = ctk.CTkFrame(self.main_area, fg_color="transparent")
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        
        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text="ADDONS & MODS (MODRINTH)", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        
        refresh_btn = ctk.CTkButton(top, text="🔄 Refresh", fg_color="transparent", border_width=1, border_color=ACCENT_BLUE)
        refresh_btn.pack(side="right")

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        
        loading_lbl = ctk.CTkLabel(scroll, text="Fetching Mods from Modrinth API...", font=("Segoe UI", 14), text_color=TEXT_SECONDARY)
        loading_lbl.pack(pady=50)

        def load_mods():
            projects = ModrinthAPI.fetch_projects("mod", limit=12)
            self.after(0, lambda: self.render_modrinth_rows(scroll, loading_lbl, projects))

        refresh_btn.configure(command=lambda: threading.Thread(target=load_mods, daemon=True).start())
        threading.Thread(target=load_mods, daemon=True).start()

        return f

    def render_modrinth_cards(self, parent_frame, loading_lbl, projects, btn_text, p_type):
        loading_lbl.destroy()
        
        for widget in parent_frame.winfo_children():
            widget.destroy()

        if not projects:
            ctk.CTkLabel(parent_frame, text="No projects found or API error.", text_color="#EF4444").pack(pady=20)
            return

        r, c = 0, 0
        for p in projects:
            title = p.get("title", "Unknown")
            slug = p.get("slug", "")
            dls = self.format_downloads(p.get("downloads", 0))
            
            card = ctk.CTkFrame(parent_frame, fg_color=CARD_BG, corner_radius=12, width=220, height=220)
            card.grid(row=r, column=c, padx=10, pady=10)
            card.grid_propagate(False)
            
            img_ph = ctk.CTkFrame(card, fg_color=BORDER_COLOR, height=80, corner_radius=10)
            img_ph.pack(fill="x", padx=10, pady=10)
            ctk.CTkLabel(img_ph, text=title[:15], text_color=TEXT_SECONDARY).place(relx=0.5, rely=0.5, anchor="center")
            
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15)
            ctk.CTkLabel(card, text=f"⬇ {dls} Downloads", font=("Segoe UI", 11), text_color=GREEN_STATUS).pack(anchor="w", padx=15)
            
            ctk.CTkButton(card, text=btn_text, fg_color=ACCENT_BLUE, width=180, 
                          command=lambda s=slug, t=title, pt=p_type: self.install_project_thread(s, t, pt)).pack(side="bottom", pady=15)
            
            c += 1
            if c > 3: c, r = 0, r + 1

    def render_modrinth_rows(self, parent_frame, loading_lbl, projects):
        loading_lbl.destroy()
        
        for widget in parent_frame.winfo_children():
            widget.destroy()

        if not projects:
            ctk.CTkLabel(parent_frame, text="No projects found or API error.", text_color="#EF4444").pack(pady=20)
            return

        for p in projects:
            title = p.get("title", "Unknown")
            slug = p.get("slug", "")
            desc = p.get("description", "No description")[:80] + "..."
            dls = self.format_downloads(p.get("downloads", 0))
            
            row = ctk.CTkFrame(parent_frame, fg_color=CARD_BG, corner_radius=10, height=80)
            row.pack(fill="x", padx=10, pady=5)
            row.pack_propagate(False)
            
            ctk.CTkLabel(row, text=title, font=("Segoe UI", 14, "bold")).place(x=20, y=15)
            ctk.CTkLabel(row, text=f"{desc} | ⬇ {dls}", font=("Segoe UI", 11), text_color=TEXT_SECONDARY).place(x=20, y=40)
            
            ctk.CTkButton(row, text="Add to Profile", fg_color="transparent", border_width=1, border_color=GREEN_STATUS, text_color=GREEN_STATUS, width=100, 
                          command=lambda s=slug, t=title: self.install_project_thread(s, t, "mod")).place(relx=0.95, rely=0.5, anchor="e")

    # --- SETTINGS TAB ---
    def tab_settings(self):
        f = ctk.CTkFrame(self.main_area, fg_color="transparent")
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(f, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ctk.CTkLabel(top, text="SETTINGS", font=("Segoe UI", 28, "bold", "italic")).pack(side="left")
        
        def reset_action():
            self.engine.reset_config()
            self.show_popup("Settings Reset", "All settings have been reset to default values. Please restart the launcher.")

        def save_action():
            self.show_popup("Saved", "Your launcher configuration has been saved successfully.")

        ctk.CTkButton(top, text="💾 Save Changes", fg_color=ACCENT_BLUE, command=save_action).pack(side="right", padx=10)
        ctk.CTkButton(top, text="🔄 Reset Defaults", fg_color="transparent", border_width=1, border_color=TEXT_SECONDARY, command=reset_action).pack(side="right")

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")

        card1 = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=12)
        card1.pack(fill="x", padx=10, pady=10, ipady=10)
        ctk.CTkLabel(card1, text="LAUNCHER PREFERENCES", font=("Segoe UI", 12, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(15, 10))
        
        row1 = ctk.CTkFrame(card1, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(row1, text="Username", font=("Segoe UI", 13, "bold")).pack(side="left")
        username_entry = ctk.CTkEntry(row1, width=200, fg_color=BORDER_COLOR)
        username_entry.insert(0, self.engine.config.get("username", "Player"))
        username_entry.pack(side="right")

        card2 = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=12)
        card2.pack(fill="x", padx=10, pady=10, ipady=10)
        ctk.CTkLabel(card2, text="PERFORMANCE", font=("Segoe UI", 12, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(15, 10))
        
        row2 = ctk.CTkFrame(card2, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(row2, text="RAM Allocation (MB)", font=("Segoe UI", 13, "bold")).pack(side="left")
        
        ram_menu = ctk.CTkOptionMenu(row2, values=["2048", "4096", "8192", "12288", "16384"], fg_color=BORDER_COLOR)
        ram_menu.set(str(self.engine.config.get("ram_mb", 8192)))
        ram_menu.pack(side="right")

        card3 = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=12)
        card3.pack(fill="x", padx=10, pady=10, ipady=10)
        ctk.CTkLabel(card3, text="SYSTEM OVERVIEW", font=("Segoe UI", 12, "bold"), text_color=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(15, 10))
        
        for k, v in self.engine.system_info.items():
            r = ctk.CTkFrame(card3, fg_color="transparent")
            r.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(r, text=k.upper(), font=("Segoe UI", 12, "bold")).pack(side="left")
            ctk.CTkLabel(r, text=v, font=("Segoe UI", 11), text_color=TEXT_SECONDARY).pack(side="right")

        return f

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
