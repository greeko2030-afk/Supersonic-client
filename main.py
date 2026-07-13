import sys
import os
import uuid
import threading
import json
import shutil
import requests
import subprocess
import webbrowser
import urllib.request
import urllib.error
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import minecraft_launcher_lib

# --- THEME & COLOR PALETTE (Matched with Screenshots) ---
BG_COLOR = "#0B0E14"          
SIDEBAR_COLOR = "#11151E"     
CARD_COLOR = "#161B28"        
ACCENT_BLUE = "#1D4ED8"       
ACCENT_CYAN = "#00D4FF"       
ACCENT_GREEN = "#10B981"      
ACCENT_PURPLE = "#7C3AED"
TEXT_PRIMARY = "#FFFFFF"
TEXT_MUTED = "#8A93B2"
BORDER_COLOR = "#1F2937"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class SuperSonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SuperSonic Client v2.5.0")
        self.geometry("1400x850")
        self.minsize(1280, 720)
        self.configure(fg_color=BG_COLOR)

        self.config_file = "supersonic_config.json"
        self.user_config = self.load_config()
        self.game_process = None
        self.hardcoded_api_key = "AQ.Ab8RN6IZzVVGS9dP9RnVtJTGvlYtl8UfW9uUb8FD7G-62moFDQ"
        self.appdata_dir = os.path.join(os.getenv('APPDATA'), 'SupersonicClient', 'bin')
        os.makedirs(self.appdata_dir, exist_ok=True)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()
        self.setup_frames()
        self.show_frame("Dashboard")

    # ==================== SIDEBAR SETUP ====================
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo Area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(20, 30), sticky="w")
        try:
            logo_img = ctk.CTkImage(light_image=Image.open(resource_path("1000117781.png")), dark_image=Image.open(resource_path("1000117781.png")), size=(35, 35))
            ctk.CTkLabel(logo_frame, image=logo_img, text="").pack(side="left")
        except:
            ctk.CTkLabel(logo_frame, text="⚡", font=ctk.CTkFont(size=28), text_color=ACCENT_BLUE).pack(side="left")
            
        ctk.CTkLabel(logo_frame, text=" SUPERSONIC\n CLIENT", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY, justify="left").pack(side="left", padx=10)

        self.nav_buttons = {}
        nav_items = [
            ("🏠 Dashboard", "Dashboard"),
            ("📦 Modpacks", "Modpacks"),
            ("🧩 Addons & Mods", "Addons"),
            ("⚙️ Settings & Accounts", "Settings"),
            ("🤖 Agent (AI)", "Agent")
        ]

        for i, (text, name) in enumerate(nav_items):
            btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", text_color=TEXT_MUTED, font=ctk.CTkFont(size=14, weight="bold"), anchor="w", height=40, command=lambda n=name: self.show_frame(n))
            btn.grid(row=i+1, column=0, sticky="ew", padx=15, pady=2)
            self.nav_buttons[name] = btn

        # Bottom Account Display
        self.acc_frame = ctk.CTkFrame(self.sidebar, fg_color=CARD_COLOR, corner_radius=8)
        self.acc_frame.grid(row=11, column=0, padx=15, pady=20, sticky="ew")
        ctk.CTkLabel(self.acc_frame, text="Active Profile", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(10, 0))
        self.sidebar_user_lbl = ctk.CTkLabel(self.acc_frame, text=self.user_config.get("username", "Player"), font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRIMARY)
        self.sidebar_user_lbl.pack(anchor="w", padx=10)
        ctk.CTkLabel(self.acc_frame, text="👑 Premium", font=ctk.CTkFont(size=11, weight="bold"), text_color="#F59E0B").pack(anchor="w", padx=10, pady=(0, 10))

    # ==================== ALL FRAMES SETUP ====================
    def setup_frames(self):
        self.frames = {}
        
        # --- 1. DASHBOARD ---
        f_dash = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frames["Dashboard"] = f_dash
        
        banner = ctk.CTkFrame(f_dash, fg_color=CARD_COLOR, corner_radius=12, height=180)
        banner.pack(fill="x", padx=30, pady=(30, 20))
        banner.pack_propagate(False)
        
        ctk.CTkLabel(banner, text="SUPERSONIC CLIENT", font=ctk.CTkFont(size=28, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).place(x=30, y=30)
        ctk.CTkLabel(banner, text="Hyper optimized. Ultra fast. Future ready.", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED).place(x=30, y=70)
        
        self.play_btn = ctk.CTkButton(banner, text="▶ PLAY", font=ctk.CTkFont(size=20, weight="bold"), fg_color=ACCENT_BLUE, hover_color="#1E40AF", width=200, height=60, corner_radius=8, command=self.handle_play)
        self.play_btn.place(relx=0.95, rely=0.5, anchor="e")

        stats_frame = ctk.CTkFrame(banner, fg_color="transparent")
        stats_frame.place(x=30, y=120)
        self.dash_stats_lbl = ctk.CTkLabel(stats_frame, text=f"📦 Minecraft {self.user_config.get('version', '1.21.1')}   🚀 Engine: Mesa D3D12   💾 RAM: {self.user_config.get('ram', 4)}GB", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        self.dash_stats_lbl.pack(side="left")

        # Server Card (NarratorMC)
        self.create_section_header(f_dash, "RECOMMENDED SERVER", "")
        server_card = ctk.CTkFrame(f_dash, fg_color=CARD_COLOR, corner_radius=10, height=90)
        server_card.pack(fill="x", padx=30, pady=10)
        server_card.pack_propagate(False)
        ctk.CTkLabel(server_card, text="NarratorMC", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_PRIMARY).place(x=20, y=15)
        ctk.CTkLabel(server_card, text="IP: www.NarratorMC.net", font=ctk.CTkFont(size=13), text_color=TEXT_MUTED).place(x=20, y=45)
        ctk.CTkLabel(server_card, text="ONLINE", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_GREEN, fg_color="#064E3B", corner_radius=5, padx=10, pady=4).place(relx=0.95, rely=0.5, anchor="e")

        # --- 2. MODPACKS (Modrinth Search) ---
        f_packs = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["Modpacks"] = f_packs
        
        top_packs = ctk.CTkFrame(f_packs, fg_color="transparent")
        top_packs.pack(fill="x", padx=30, pady=30)
        ctk.CTkLabel(top_packs, text="MODPACK INSTALLER", font=ctk.CTkFont(size=28, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).pack(side="left")
        self.pack_search = ctk.CTkEntry(top_packs, placeholder_text="Search modpacks (e.g. Fabulously Optimized)...", width=300, fg_color=CARD_COLOR, border_color=BORDER_COLOR)
        self.pack_search.pack(side="left", padx=20)
        ctk.CTkButton(top_packs, text="Find Packs", fg_color=ACCENT_BLUE, command=self.search_modpacks).pack(side="left")

        self.packs_scroll = ctk.CTkScrollableFrame(f_packs, fg_color="transparent")
        self.packs_scroll.pack(fill="both", expand=True, padx=25, pady=10)

        # --- 3. ADDONS & MODS (Search + Local Import + CurseForge Fallback) ---
        f_addons = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["Addons"] = f_addons
        
        top_mods = ctk.CTkFrame(f_addons, fg_color="transparent")
        top_mods.pack(fill="x", padx=30, pady=30)
        ctk.CTkLabel(top_mods, text="MODS MANAGER", font=ctk.CTkFont(size=28, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(top_mods, text="+ Import Local .jar", fg_color=ACCENT_PURPLE, command=self.import_local_mod).pack(side="right")
        
        mod_search_bar = ctk.CTkFrame(f_addons, fg_color="transparent")
        mod_search_bar.pack(fill="x", padx=30, pady=5)
        self.mod_search_entry = ctk.CTkEntry(mod_search_bar, placeholder_text="Search mods globally...", height=40, fg_color=CARD_COLOR, border_color=BORDER_COLOR)
        self.mod_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(mod_search_bar, text="Search Mod", width=120, height=40, fg_color=ACCENT_CYAN, text_color="black", font=ctk.CTkFont(weight="bold"), command=self.search_mods).pack(side="right")

        self.mods_scroll = ctk.CTkScrollableFrame(f_addons, fg_color="transparent")
        self.mods_scroll.pack(fill="both", expand=True, padx=25, pady=10)

        # --- 4. SETTINGS & ACCOUNTS (Alt System + Engine + Skin) ---
        f_settings = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frames["Settings"] = f_settings
        ctk.CTkLabel(f_settings, text="ENGINE & ACCOUNTS", font=ctk.CTkFont(size=28, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=30, pady=30)
        
        set_grid = ctk.CTkFrame(f_settings, fg_color="transparent")
        set_grid.pack(fill="x", padx=30)
        
        # Engine Settings Card
        gen_card = ctk.CTkFrame(set_grid, fg_color=CARD_COLOR, corner_radius=10)
        gen_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(gen_card, text="PERFORMANCE & ENGINE", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=15)
        
        self.ram_var = ctk.StringVar(value=f"{self.user_config.get('ram', 4)} GB")
        ctk.CTkLabel(gen_card, text="RAM Allocation", text_color=TEXT_PRIMARY).pack(anchor="w", padx=20)
        ram_slider = ctk.CTkSlider(gen_card, from_=1, to=16, number_of_steps=15, command=self.update_ram)
        ram_slider.set(self.user_config.get("ram", 4))
        ram_slider.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(gen_card, textvariable=self.ram_var, text_color=ACCENT_CYAN).pack(anchor="w", padx=20, pady=(0, 15))

        ctk.CTkLabel(gen_card, text="Game Version", text_color=TEXT_PRIMARY).pack(anchor="w", padx=20)
        self.ver_dropdown = ctk.CTkOptionMenu(gen_card, values=["1.21.4", "1.21.1", "1.20.6", "1.19.4"], command=self.update_version, fg_color=SIDEBAR_COLOR, button_color=ACCENT_BLUE)
        self.ver_dropdown.set(self.user_config.get("version", "1.21.1"))
        self.ver_dropdown.pack(anchor="w", padx=20, pady=(5, 20))

        # Accounts & Skin Card (Alt System)
        acc_set_card = ctk.CTkFrame(set_grid, fg_color=CARD_COLOR, corner_radius=10)
        acc_set_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(acc_set_card, text="ACCOUNT & SKIN (ALT SYSTEM)", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=15)
        
        self.account_dropdown = ctk.CTkOptionMenu(acc_set_card, values=self.user_config.get("alt_accounts", ["Player"]), command=self.switch_account, fg_color=SIDEBAR_COLOR, button_color=ACCENT_PURPLE)
        self.account_dropdown.set(self.user_config.get("username", "Player"))
        self.account_dropdown.pack(anchor="w", padx=20, pady=5)

        alt_entry_bar = ctk.CTkFrame(acc_set_card, fg_color="transparent")
        alt_entry_bar.pack(fill="x", padx=20, pady=10)
        self.new_alt_entry = ctk.CTkEntry(alt_entry_bar, placeholder_text="New alt name...", width=150, fg_color=SIDEBAR_COLOR)
        self.new_alt_entry.pack(side="left", padx=(0, 10))
        ctk.CTkButton(alt_entry_bar, text="Add Alt", width=80, fg_color=ACCENT_CYAN, text_color="black", command=self.add_alt_account).pack(side="left")

        ctk.CTkButton(acc_set_card, text="Upload Custom Skin (.png)", fg_color=ACCENT_BLUE, command=self.upload_skin).pack(anchor="w", padx=20, pady=15)

        # --- 5. AGENT AI (Crash Reader + Chat) ---
        f_agent = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["Agent"] = f_agent
        
        agent_header = ctk.CTkFrame(f_agent, fg_color=CARD_COLOR, corner_radius=12, height=120)
        agent_header.pack(fill="x", padx=30, pady=30)
        agent_header.pack_propagate(False)
        ctk.CTkLabel(agent_header, text="AGENT (AI) DIAGNOSTICS", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_PRIMARY).place(x=30, y=25)
        ctk.CTkLabel(agent_header, text="Background Automation Active. System Engine synced.", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED).place(x=30, y=60)
        
        chat_container = ctk.CTkFrame(f_agent, fg_color=CARD_COLOR, corner_radius=12)
        chat_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        self.chat_history = ctk.CTkTextbox(chat_container, fg_color="transparent", text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=14))
        self.chat_history.pack(fill="both", expand=True, padx=20, pady=20)
        self.chat_history.insert("end", "🤖 SupersonicAI: Ready. If your game crashes, I will automatically read latest.log and provide a fix.\n\n")
        self.chat_history.configure(state="disabled")

        input_frame = ctk.CTkFrame(chat_container, fg_color=BG_COLOR, corner_radius=8, height=50)
        input_frame.pack(fill="x", padx=20, pady=20)
        input_frame.pack_propagate(False)
        
        self.chat_entry = ctk.CTkEntry(input_frame, placeholder_text="Ask me anything manually...", fg_color="transparent", border_width=0)
        self.chat_entry.pack(side="left", fill="both", expand=True, padx=10)
        ctk.CTkButton(input_frame, text="➤", width=40, fg_color=ACCENT_BLUE, command=self.send_ai_msg).pack(side="right", padx=5)

    # ==================== UI HELPERS ====================
    def create_section_header(self, parent, title, btn_text):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(20, 0))
        ctk.CTkLabel(hdr, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        if btn_text:
            ctk.CTkButton(hdr, text=btn_text, fg_color="transparent", border_width=1, border_color=BORDER_COLOR, text_color=TEXT_PRIMARY, height=28).pack(side="right")

    def show_frame(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.configure(fg_color=CARD_COLOR if btn_name == name else "transparent", text_color=ACCENT_CYAN if btn_name == name else TEXT_MUTED)
        for f_name, f in self.frames.items():
            if f_name == name: f.pack(fill="both", expand=True)
            else: f.pack_forget()

    # ==================== SETTINGS & ACCOUNT LOGIC ====================
    def update_ram(self, val):
        self.ram_var.set(f"{int(val)} GB")
        self.user_config["ram"] = int(val)
        self.dash_stats_lbl.configure(text=f"📦 Minecraft {self.user_config.get('version', '1.21.1')}   🚀 Engine: Mesa D3D12   💾 RAM: {int(val)}GB")
        self.save_config()

    def update_version(self, choice):
        self.user_config["version"] = choice
        self.dash_stats_lbl.configure(text=f"📦 Minecraft {choice}   🚀 Engine: Mesa D3D12   💾 RAM: {self.user_config.get('ram', 4)}GB")
        self.save_config()

    def add_alt_account(self):
        name = self.new_alt_entry.get().strip()
        if name:
            alts = self.user_config.get("alt_accounts", ["Player"])
            if name not in alts:
                alts.append(name)
                self.user_config["alt_accounts"] = alts
                self.account_dropdown.configure(values=alts)
                self.switch_account(name)
                self.new_alt_entry.delete(0, 'end')

    def switch_account(self, val):
        self.user_config["username"] = val
        self.account_dropdown.set(val)
        self.sidebar_user_lbl.configure(text=val)
        self.save_config()

    def upload_skin(self):
        path = filedialog.askopenfilename(filetypes=[("PNG Assets", "*.png")])
        if path:
            self.user_config["custom_skin_path"] = path
            self.save_config()
            messagebox.showinfo("Skin Loaded", f"Custom skin {os.path.basename(path)} configured locally.")

    # ==================== MODS & MODPACKS LOGIC ====================
    def import_local_mod(self):
        file_path = filedialog.askopenfilename(filetypes=[("JAR files", "*.jar")])
        if file_path:
            try:
                target_dir = os.path.join(minecraft_launcher_lib.utils.get_minecraft_directory(), "mods")
                os.makedirs(target_dir, exist_ok=True)
                shutil.copy2(file_path, os.path.join(target_dir, os.path.basename(file_path)))
                messagebox.showinfo("Success", f"Imported {os.path.basename(file_path)} to mods folder.")
            except Exception as e:
                messagebox.showerror("Error", f"Copy failed: {e}")

    def search_modpacks(self):
        query = self.pack_search.get().strip()
        if not query: return
        for w in self.packs_scroll.winfo_children(): w.destroy()
        
        try:
            url = f"https://api.modrinth.com/v2/search?query={query}&facets=[[%22project_type:modpack%22]]"
            res = requests.get(url).json()
            for pack in res.get("hits", []):
                card = ctk.CTkFrame(self.packs_scroll, fg_color=CARD_COLOR, height=60)
                card.pack(fill="x", pady=5)
                ctk.CTkLabel(card, text=pack['title'], font=ctk.CTkFont(weight="bold")).place(x=15, y=15)
                ctk.CTkButton(card, text="View Modpack", fg_color=ACCENT_BLUE, command=lambda s=pack['slug']: webbrowser.open(f"https://modrinth.com/modpack/{s}")).place(relx=0.95, rely=0.5, anchor="e")
        except: pass

    def search_mods(self):
        query = self.mod_search_entry.get().strip()
        if not query: return
        for w in self.mods_scroll.winfo_children(): w.destroy()

        try:
            url = f"https://api.modrinth.com/v2/search?query={query}&facets=[[%22project_type:mod%22]]"
            hits = requests.get(url, timeout=10).json().get("hits", [])
            
            if hits:
                for item in hits:
                    card = ctk.CTkFrame(self.mods_scroll, fg_color=CARD_COLOR, height=70)
                    card.pack(fill="x", pady=5)
                    ctk.CTkLabel(card, text=item.get("title"), font=ctk.CTkFont(weight="bold")).place(x=15, y=10)
                    ctk.CTkLabel(card, text=item.get("description", "")[:80]+"...", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).place(x=15, y=35)
                    ctk.CTkButton(card, text="Install Mod", width=90, fg_color=ACCENT_CYAN, text_color="black", font=ctk.CTkFont(weight="bold"), command=lambda s=item.get("slug"): self.download_mod_from_slug(s)).place(relx=0.95, rely=0.5, anchor="e")
            else:
                card = ctk.CTkFrame(self.mods_scroll, fg_color=CARD_COLOR, height=70)
                card.pack(fill="x", pady=5)
                ctk.CTkLabel(card, text=f"No Modrinth index for '{query}'. Execute CurseForge Fallback.", text_color="orange").place(x=15, y=20)
                ctk.CTkButton(card, text="Search CurseForge", fg_color=ACCENT_PURPLE, command=lambda: webbrowser.open(f"https://www.curseforge.com/minecraft/search?search={query}")).place(relx=0.95, rely=0.5, anchor="e")
        except Exception as e: pass

    def download_mod_from_slug(self, slug):
        try:
            target_dir = os.path.join(minecraft_launcher_lib.utils.get_minecraft_directory(), "mods")
            os.makedirs(target_dir, exist_ok=True)
            ver = self.user_config.get("version", "1.21.1")
            
            builds = requests.get(f"https://api.modrinth.com/v2/project/{slug}/version?game_versions=[\"{ver}\"]").json()
            if builds:
                file_info = builds[0]['files'][0]
                with open(os.path.join(target_dir, file_info['filename']), 'wb') as f:
                    f.write(requests.get(file_info['url']).content)
                messagebox.showinfo("Success", f"Installed {file_info['filename']}!")
            else:
                messagebox.showwarning("Mismatch", f"No file found for game version {ver}")
        except Exception as e: messagebox.showerror("Error", str(e))

    # ==================== ENGINE & LAUNCH LOGIC ====================
    def setup_engine_components(self):
        """Extract Mesa D3D12 rendering engine (opengl32.dll) offline or download fallback"""
        files = {
            "glslangValidator.exe": "https://github.com/vulkan-sdk-mirror/glslangValidator.exe",
            "opengl32.dll": "https://github.com/pal1000/mesa-dist-win/releases/download/23.1.3/opengl32.dll"
        }
        for filename, url in files.items():
            target_path = os.path.join(self.appdata_dir, filename)
            bundled_path = resource_path(filename)
            
            if os.path.exists(bundled_path) and not os.path.isdir(bundled_path):
                if not os.path.exists(target_path) or os.path.getsize(target_path) != os.path.getsize(bundled_path):
                    try: shutil.copy2(bundled_path, target_path)
                    except: pass
            else:
                if not os.path.exists(target_path) or os.path.getsize(target_path) < 500000:
                    try:
                        res = requests.get(url, timeout=15)
                        if res.status_code == 200:
                            with open(target_path, "wb") as f: f.write(res.content)
                    except: pass

    def handle_play(self):
        if self.game_process and self.game_process.poll() is None:
            try:
                self.game_process.terminate()
                self.game_process.kill()
                self.play_btn.configure(text="▶ PLAY", fg_color=ACCENT_BLUE)
            except: pass
        else:
            self.play_btn.configure(state="disabled", text="RUNNING...")
            threading.Thread(target=self.launch_game, daemon=True).start()

    def launch_game(self):
        try:
            self.setup_engine_components()
            
            mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
            version = self.user_config.get("version", "1.21.1")
            
            minecraft_launcher_lib.install.install_minecraft_version(version, mc_dir)
            fabric_ver = minecraft_launcher_lib.fabric.get_latest_loader_version()
            minecraft_launcher_lib.fabric.install_fabric(version, mc_dir, loader_version=fabric_ver)
            
            username = self.user_config.get("username", "Player")
            opts = {
                "username": username,
                "uuid": str(uuid.uuid3(uuid.NAMESPACE_DNS, username)),
                "token": "",
                "jvmArguments": [f"-Xmx{int(self.user_config.get('ram', 4))}G"]
            }
            cmd = minecraft_launcher_lib.command.get_minecraft_command(f"fabric-loader-{fabric_ver}-{version}", mc_dir, opts)
            
            # Custom MESA D3D12 Environment Injection
            custom_env = os.environ.copy()
            custom_env["PATH"] = self.appdata_dir + os.pathsep + custom_env.get("PATH", "")
            custom_env["MESA_GL_VERSION_OVERRIDE"] = "4.6"
            custom_env["MESA_GLSL_VERSION_OVERRIDE"] = "460"
            custom_env["GALLIUM_DRIVER"] = "d3d12"
            
            self.play_btn.configure(state="normal", text="🛑 STOP", fg_color="#DC2626", hover_color="#991B1B")
            self.game_process = subprocess.Popen(cmd, env=custom_env)
            self.game_process.wait()

            if self.game_process.returncode != 0 and self.game_process.returncode != -1:
                self.trigger_background_autofix()
                
        except Exception as e:
            messagebox.showerror("Engine Error", str(e))
        finally:
            self.play_btn.configure(state="normal", text="▶ PLAY", fg_color=ACCENT_BLUE, hover_color="#1E40AF")

    # ==================== AI AGENT LOGIC ====================
    def trigger_background_autofix(self):
        self.show_frame("Agent")
        mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
        log_path = os.path.join(mc_dir, "logs", "latest.log")
        if not os.path.exists(log_path): return
        
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                logs = "".join(f.readlines()[-60:])
            
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", "🤖 System: Crash detected. Analyzing latest.log automatically...\n\n")
            self.chat_history.configure(state="disabled")
            
            threading.Thread(target=self.process_ai_response, args=(f"Analyze this crash log and specify broken mods:\n\n{logs}",), daemon=True).start()
        except: pass

    def send_ai_msg(self):
        msg = self.chat_entry.get().strip()
        if not msg: return
        self.chat_entry.delete(0, 'end')
        
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"👤 You: {msg}\n\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")
        
        threading.Thread(target=self.process_ai_response, args=(msg,), daemon=True).start()

    def process_ai_response(self, text):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={self.hardcoded_api_key}"
            payload = {"contents": [{"parts": [{"text": text}]}]}
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req) as response:
                res = json.loads(response.read().decode('utf-8'))
            reply = res['candidates'][0]['content']['parts'][0]['text'].strip()
            
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", f"🤖 Agent: {reply}\n\n")
            self.chat_history.see("end")
            self.chat_history.configure(state="disabled")
        except Exception:
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", "🤖 Agent: Network error. Failed to reach Gemini API. Please check your internet connection.\n\n")
            self.chat_history.configure(state="disabled")

    # ==================== CONFIG SAVING ====================
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: return json.load(f)
            except: pass
        return {"ram": 4, "username": "Player", "version": "1.21.1", "alt_accounts": ["Player"]}

    def save_config(self):
        try:
            with open(self.config_file, "w") as f: json.dump(self.user_config, f, indent=4)
        except: pass

if __name__ == "__main__":
    app = SuperSonicClient()
    app.mainloop()
