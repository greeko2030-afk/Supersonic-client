import os
import sys
import threading
import subprocess
import json
import requests
import customtkinter as ctk
import minecraft_launcher_lib

# --- Configuration & Theme ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

UPDATE_URL = "https://supersonic-client--greeko2030.replit.app/api/version"
CURRENT_VERSION = "2.5.0"
MINECRAFT_DIR = minecraft_launcher_lib.utils.get_minecraft_directory()

class SupersonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Supersonic Client v2.5.0 - Next Gen Launcher")
        self.geometry("1100x700")
        self.resizable(False, False)

        # Main Layout: 2 Columns (Sidebar + Content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SUPERSONIC", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Sidebar Buttons
        self.btn_dash = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.btn_dash.grid(row=1, column=0, padx=20, pady=10)

        self.btn_mods = ctk.CTkButton(self.sidebar_frame, text="Addons (Modrinth)", command=self.show_mods)
        self.btn_mods.grid(row=2, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Settings", command=self.show_settings)
        self.btn_settings.grid(row=3, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Status: Ready", text_color="green")
        self.status_label.grid(row=7, column=0, padx=20, pady=20)

        # --- Content Frames ---
        self.dashboard_frame = ctk.CTkFrame(self, corner_radius=10)
        self.mods_frame = ctk.CTkFrame(self, corner_radius=10)
        self.settings_frame = ctk.CTkFrame(self, corner_radius=10)

        self.build_dashboard()
        self.build_mods_view()
        self.build_settings_view()

        # Check Updates on Startup
        threading.Thread(target=self.check_for_updates, daemon=True).start()
        self.show_dashboard()

    # ====== VIEWS ======
    def show_dashboard(self):
        self.mods_frame.grid_forget()
        self.settings_frame.grid_forget()
        self.dashboard_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_mods(self):
        self.dashboard_frame.grid_forget()
        self.settings_frame.grid_forget()
        self.mods_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def show_settings(self):
        self.dashboard_frame.grid_forget()
        self.mods_frame.grid_forget()
        self.settings_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    # ====== BUILD DASHBOARD ======
    def build_dashboard(self):
        title = ctk.CTkLabel(self.dashboard_frame, text="Supersonic Client", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(pady=20, padx=20, anchor="w")

        # Login Section
        login_frame = ctk.CTkFrame(self.dashboard_frame)
        login_frame.pack(pady=10, padx=20, fill="x")
        
        self.username_entry = ctk.CTkEntry(login_frame, placeholder_text="Username (Offline)")
        self.username_entry.pack(side="left", padx=10, pady=10)

        self.ms_login_btn = ctk.CTkButton(login_frame, text="Microsoft Login", fg_color="#00a4ef", hover_color="#0078d7", command=self.microsoft_login)
        self.ms_login_btn.pack(side="left", padx=10, pady=10)

        # Version & Launch
        launch_frame = ctk.CTkFrame(self.dashboard_frame)
        launch_frame.pack(pady=20, padx=20, fill="x")

        self.version_entry = ctk.CTkEntry(launch_frame, placeholder_text="Version (e.g. 1.21.4)")
        self.version_entry.insert(0, "1.21.4")
        self.version_entry.pack(side="left", padx=10, pady=10)

        self.play_btn = ctk.CTkButton(launch_frame, text="PLAY MINECRAFT", font=ctk.CTkFont(weight="bold"), height=50, command=self.start_launch_thread)
        self.play_btn.pack(side="right", padx=10, pady=10)

    # ====== BUILD SETTINGS ======
    def build_settings_view(self):
        title = ctk.CTkLabel(self.settings_frame, text="Advanced Settings", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=20, padx=20, anchor="w")

        # D3D12 Toggle
        self.d3d12_var = ctk.BooleanVar(value=True)
        d3d12_switch = ctk.CTkSwitch(self.settings_frame, text="Enable Direct3D12 Engine Support", variable=self.d3d12_var)
        d3d12_switch.pack(pady=10, padx=20, anchor="w")

        # JVM Args
        ctk.CTkLabel(self.settings_frame, text="Advanced JVM Arguments:").pack(padx=20, anchor="w")
        self.jvm_entry = ctk.CTkEntry(self.settings_frame, width=400)
        self.jvm_entry.insert(0, "-Xmx4G -XX:+UnlockExperimentalVMOptions")
        self.jvm_entry.pack(pady=5, padx=20, anchor="w")

    # ====== BUILD MODS ======
    def build_mods_view(self):
        title = ctk.CTkLabel(self.mods_frame, text="Modrinth Addons Installer", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=20, padx=20, anchor="w")

        search_frame = ctk.CTkFrame(self.mods_frame)
        search_frame.pack(fill="x", padx=20, pady=10)
        
        self.mod_search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search mods (e.g. sodium)...", width=300)
        self.mod_search_entry.pack(side="left", padx=10, pady=10)
        
        search_btn = ctk.CTkButton(search_frame, text="Search", command=self.search_modrinth)
        search_btn.pack(side="left", padx=10, pady=10)

        self.mod_result_label = ctk.CTkLabel(self.mods_frame, text="Results will appear here.")
        self.mod_result_label.pack(pady=20)

    # ====== REAL FEATURES LOGIC ======

    def check_for_updates(self):
        try:
            # Assuming your replit returns JSON: {"version": "2.6.0", "url": "..."}
            response = requests.get(UPDATE_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("version") != CURRENT_VERSION:
                    self.status_label.configure(text="Update Available!", text_color="orange")
            else:
                pass # Web is offline or not configured yet
        except Exception:
            self.status_label.configure(text="Update Server Offline", text_color="gray")

    def microsoft_login(self):
        # Placeholder for MSAL integration. minecraft_launcher_lib has built-in functions for this.
        self.status_label.configure(text="Microsoft Auth Opening...", text_color="yellow")
        # For real implementation, you will use minecraft_launcher_lib.microsoft_account

    def search_modrinth(self):
        query = self.mod_search_entry.get()
        if not query: return
        self.mod_result_label.configure(text=f"Searching for {query}...")
        
        def fetch():
            try:
                url = f"https://api.modrinth.com/v2/search?query={query}&limit=1"
                res = requests.get(url).json()
                if res['hits']:
                    title = res['hits'][0]['title']
                    desc = res['hits'][0]['description']
                    self.mod_result_label.configure(text=f"Found: {title}\n{desc}\n\n(Auto-install logic requires project ID)")
                else:
                    self.mod_result_label.configure(text="No mods found.")
            except Exception as e:
                self.mod_result_label.configure(text=f"Error: {str(e)}")
        threading.Thread(target=fetch).start()

    def start_launch_thread(self):
        self.play_btn.configure(state="disabled", text="LAUNCHING...")
        self.status_label.configure(text="Preparing Game...", text_color="yellow")
        threading.Thread(target=self.launch_game).start()

    def launch_game(self):
        version = self.version_entry.get()
        username = self.username_entry.get() or "Player"

        # Resolve D3D12 Engine DLL Path
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        engine_path = os.path.join(base_dir, "engine", "opengl32.dll")

        # Setup Launch Options
        options = {
            "username": username,
            "uuid": "",
            "token": "",
            "jvmArguments": self.jvm_entry.get().split(),
            "launcherName": "Supersonic",
            "launcherVersion": CURRENT_VERSION,
        }

        # Apply D3D12 Hook
        if self.d3d12_var.get():
            if os.path.exists(engine_path):
                options["jvmArguments"].append(f"-Dorg.lwjgl.opengl.libname={engine_path}")
                print(f"D3D12 Hook Active: {engine_path}")
            else:
                print("D3D12 enabled but engine/opengl32.dll missing. Falling back to OpenGL.")

        try:
            # Install if missing
            self.status_label.configure(text=f"Checking Version {version}...")
            if not os.path.exists(os.path.join(MINECRAFT_DIR, "versions", version)):
                minecraft_launcher_lib.install.install_minecraft_version(version, MINECRAFT_DIR)

            # Generate Command & Launch
            self.status_label.configure(text="Starting Process...")
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(version, MINECRAFT_DIR, options)
            subprocess.Popen(minecraft_command)
            
            self.status_label.configure(text="Game Running!", text_color="green")
            self.play_btn.configure(state="normal", text="PLAY MINECRAFT")
            
        except Exception as e:
            self.status_label.configure(text="Launch Error!", text_color="red")
            print(f"Error launching: {e}")
            self.play_btn.configure(state="normal", text="PLAY MINECRAFT")

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
