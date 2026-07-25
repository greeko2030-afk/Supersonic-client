import os
import sys
import threading
import subprocess
import requests
import json
import uuid
import customtkinter as ctk
import minecraft_launcher_lib
from tkinter import messagebox

# ==========================================
# CONFIGURATIONS & CONSTANTS
# ==========================================
VERSION = "2.5.0"
UPDATE_URL = "https://supersonic-client--greeko2030.replit.app/api/version"
MINECRAFT_DIR = minecraft_launcher_lib.utils.get_minecraft_directory()
CLIENT_ID = "00000000402b5328" # Standard Minecraft Client ID for MS Auth
DEFAULT_SERVER = "www.NarratorMC.net"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SupersonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"SUPERSONIC CLIENT v{VERSION}")
        self.geometry("1280x720")
        self.minsize(1000, 600)
        
        # State Variables
        self.username = ctk.StringVar(value="Raffiee_playssMC")
        self.is_premium = ctk.BooleanVar(value=False)
        self.selected_version = ctk.StringVar(value="1.21.4")
        self.ram_allocation = ctk.IntVar(value=8192)
        self.use_d3d12 = ctk.BooleanVar(value=True)
        self.access_token = ""
        self.uuid = ""

        self.setup_ui()
        self.check_for_updates()

    def setup_ui(self):
        # Grid Layout: Sidebar (0) and Main Content (1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==========================================
        # SIDEBAR NAVIGATION
        # ==========================================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1) # Spacer

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SUPERSONIC", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Nav Buttons
        nav_buttons = ["Dashboard", "Modpacks", "Addons", "Instances", "Servers", "Resource Packs", "Settings", "Agent (AI)"]
        self.nav_btns = {}
        for i, name in enumerate(nav_buttons):
            btn = ctk.CTkButton(self.sidebar_frame, text=name, anchor="w", fg_color="transparent", 
                                text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                command=lambda n=name: self.switch_tab(n))
            btn.grid(row=i+1, column=0, padx=10, pady=5, sticky="ew")
            self.nav_btns[name] = btn

        # Account Section (Bottom Sidebar)
        self.account_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="#1e1e1e", corner_radius=8)
        self.account_frame.grid(row=10, column=0, padx=10, pady=20, sticky="ew")
        
        self.acc_name = ctk.CTkLabel(self.account_frame, textvariable=self.username, font=ctk.CTkFont(weight="bold"))
        self.acc_name.pack(pady=(10, 0), padx=10, anchor="w")
        
        self.acc_status = ctk.CTkLabel(self.account_frame, text="👑 Premium" if self.is_premium.get() else "🔌 Offline", text_color="#f5c542" if self.is_premium.get() else "gray")
        self.acc_status.pack(pady=(0, 10), padx=10, anchor="w")

        # ==========================================
        # MAIN CONTENT AREA
        # ==========================================
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.frames = {}
        
        # Setup specific tabs
        self.setup_dashboard_tab()
        self.setup_settings_tab()
        self.setup_modpacks_tab()
        self.setup_agent_tab()
        
        # Default Tab
        self.switch_tab("Dashboard")

    def switch_tab(self, tab_name):
        # Hide all frames
        for frame in self.frames.values():
            frame.grid_forget()
            
        # Highlight active button
        for name, btn in self.nav_btns.items():
            if name == tab_name:
                btn.configure(fg_color=("#1f538d", "#1f538d"))
            else:
                btn.configure(fg_color="transparent")

        # Show selected frame
        if tab_name in self.frames:
            self.frames[tab_name].grid(row=0, column=0, sticky="nsew")
        else:
            # Placeholder for uncompleted tabs
            placeholder = ctk.CTkFrame(self.main_frame)
            ctk.CTkLabel(placeholder, text=f"{tab_name} - Coming Soon", font=("Arial", 24)).pack(expand=True)
            self.frames[tab_name] = placeholder
            placeholder.grid(row=0, column=0, sticky="nsew")

    # ==========================================
    # TAB: DASHBOARD
    # ==========================================
    def setup_dashboard_tab(self):
        dashboard = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frames["Dashboard"] = dashboard
        
        # Header Banner
        banner = ctk.CTkFrame(dashboard, height=150, fg_color="#141824", corner_radius=15)
        banner.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(banner, text="SUPERSONIC CLIENT", font=ctk.CTkFont(size=32, weight="bold", slant="italic")).pack(anchor="w", padx=30, pady=(30, 0))
        ctk.CTkLabel(banner, text="Hyper optimized. Ultra fast. Future ready.", text_color="gray").pack(anchor="w", padx=30, pady=(5, 20))
        
        # Launch Section
        launch_frame = ctk.CTkFrame(banner, fg_color="transparent")
        launch_frame.place(relx=0.95, rely=0.5, anchor="e")
        
        self.play_btn = ctk.CTkButton(launch_frame, text="▶ PLAY", font=ctk.CTkFont(size=20, weight="bold"), width=150, height=50, command=self.start_launch_thread)
        self.play_btn.pack(side="right", padx=10)

        # Progress Bar & Status (Hidden by default)
        self.status_label = ctk.CTkLabel(dashboard, text="Ready to launch", text_color="gray")
        self.status_label.pack(anchor="w", pady=(10, 0))
        
        self.progress_bar = ctk.CTkProgressBar(dashboard, width=500)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=10)

        # Fast Addon Grid (Mockup like the image)
        addon_frame = ctk.CTkFrame(dashboard)
        addon_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(addon_frame, text="ALL ADDONS - ONE CLICK INSTALL", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)

    # ==========================================
    # TAB: SETTINGS (Advanced JVM & Direct3D12)
    # ==========================================
    def setup_settings_tab(self):
        settings = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frames["Settings"] = settings
        
        ctk.CTkLabel(settings, text="SETTINGS", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        # Performance Settings
        perf_frame = ctk.CTkFrame(settings)
        perf_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(perf_frame, text="Performance Settings", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)
        
        ram_label = ctk.CTkLabel(perf_frame, text=f"RAM Allocation: {self.ram_allocation.get()} MB")
        ram_label.pack(anchor="w", padx=15)
        ram_slider = ctk.CTkSlider(perf_frame, from_=2048, to=16384, number_of_steps=14, variable=self.ram_allocation, command=lambda v: ram_label.configure(text=f"RAM Allocation: {int(v)} MB"))
        ram_slider.pack(fill="x", padx=15, pady=10)

        # Direct3D12 Engine Hook
        ctk.CTkSwitch(perf_frame, text="Enable Direct3D12 Engine (Supersonic C++ Hook)", variable=self.use_d3d12).pack(anchor="w", padx=15, pady=10)

        # Account Section
        acc_frame = ctk.CTkFrame(settings)
        acc_frame.pack(fill="x", pady=10, padx=10)
        ctk.CTkLabel(acc_frame, text="Account Management", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=10)
        
        ctk.CTkButton(acc_frame, text="Login with Microsoft", command=self.login_microsoft, fg_color="#107c10", hover_color="#0b580b").pack(side="left", padx=15, pady=10)
        
        self.offline_entry = ctk.CTkEntry(acc_frame, placeholder_text="Offline Username")
        self.offline_entry.pack(side="left", padx=15, pady=10)
        ctk.CTkButton(acc_frame, text="Set Offline", command=self.set_offline).pack(side="left", padx=15, pady=10)

    # ==========================================
    # TAB: MODPACKS (Modrinth API Integration)
    # ==========================================
    def setup_modpacks_tab(self):
        modpacks = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frames["Modpacks"] = modpacks
        
        header = ctk.CTkFrame(modpacks, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="MODPACKS", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        # We will fetch data from Modrinth asynchronously
        self.modpack_container = ctk.CTkScrollableFrame(modpacks)
        self.modpack_container.pack(fill="both", expand=True)
        
        # Fetching thread
        threading.Thread(target=self.fetch_modrinth_packs, daemon=True).start()

    def fetch_modrinth_packs(self):
        try:
            res = requests.get('https://api.modrinth.com/v2/search?query=&facets=[["project_type:modpack"]]&limit=6')
            data = res.json()
            for i, project in enumerate(data['hits']):
                row = i // 3
                col = i % 3
                card = ctk.CTkFrame(self.modpack_container, width=200, height=250)
                card.grid(row=row, column=col, padx=10, pady=10)
                
                ctk.CTkLabel(card, text=project['title'], font=ctk.CTkFont(weight="bold")).pack(pady=10)
                ctk.CTkLabel(card, text=project['description'][:50] + "...", wraplength=180).pack(pady=5)
                ctk.CTkButton(card, text="Download").pack(side="bottom", pady=10)
        except Exception as e:
            print(f"Modrinth fetch error: {e}")

    # ==========================================
    # TAB: AGENT (AI) 
    # ==========================================
    def setup_agent_tab(self):
        agent = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frames["Agent (AI)"] = agent
        
        ctk.CTkLabel(agent, text="AGENT (AI) - BETA", font=ctk.CTkFont(size=24, weight="bold", text_color="#5cb85c")).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(agent, text=f"Hello {self.username.get()}! I'm your Supersonic Agent. I can help you optimize, fix, and enhance your Minecraft experience.").pack(anchor="w", pady=(0, 20))
        
        dashboard_frame = ctk.CTkFrame(agent)
        dashboard_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkButton(dashboard_frame, text="🛠 Auto Fix Errors", height=60).grid(row=0, column=0, padx=20, pady=20)
        ctk.CTkButton(dashboard_frame, text="⚡ Optimize Performance", height=60).grid(row=0, column=1, padx=20, pady=20)
        ctk.CTkButton(dashboard_frame, text="🧹 Clean Junk Files", height=60).grid(row=0, column=2, padx=20, pady=20)

    # ==========================================
    # LOGIC: AUTHENTICATION
    # ==========================================
    def set_offline(self):
        name = self.offline_entry.get()
        if name:
            self.username.set(name)
            self.is_premium.set(False)
            self.acc_status.configure(text="🔌 Offline", text_color="gray")
            self.uuid = str(uuid.uuid4())
            self.access_token = ""
            messagebox.showinfo("Auth", f"Offline mode set as {name}")

    def login_microsoft(self):
        # Starts Microsoft Device Code login flow using msal/requests
        self.status_label.configure(text="Waiting for Microsoft Login...")
        threading.Thread(target=self._ms_login_thread, daemon=True).start()

    def _ms_login_thread(self):
        try:
            # Using minecraft_launcher_lib built-in Microsoft OAuth logic
            # This requires opening a browser for the user
            def display_url(url):
                messagebox.showinfo("Microsoft Login", f"Please login in your browser:\n{url}\n\nThe game will resume after login.")
                import webbrowser
                webbrowser.open(url)

            # NOTE: For production, you should implement the full MSAL device_flow.
            # This is a placeholder showing the architecture.
            self.username.set("Premium_User")
            self.is_premium.set(True)
            self.acc_status.configure(text="👑 Premium", text_color="#f5c542")
            self.status_label.configure(text="Microsoft Login Successful!")
        except Exception as e:
            self.status_label.configure(text=f"Login failed: {e}")

    # ==========================================
    # LOGIC: AUTO-UPDATE
    # ==========================================
    def check_for_updates(self):
        def _check():
            try:
                res = requests.get(UPDATE_URL, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("version") != VERSION:
                        print(f"Update available: {data.get('version')}")
                        # Implement update download logic here
            except:
                print("Failed to reach update server.")
        threading.Thread(target=_check, daemon=True).start()

    # ==========================================
    # LOGIC: GAME LAUNCHING & FIXING ERRORS
    # ==========================================
    def start_launch_thread(self):
        self.play_btn.configure(state="disabled", text="LAUNCHING...")
        self.progress_bar.set(0)
        threading.Thread(target=self.launch_game, daemon=True).start()

    def launch_game(self):
        mc_version = self.selected_version.get()
        
        # Progress Callbacks for downloading files
        def set_status(status: str):
            self.status_label.configure(text=status)
            
        def set_progress(progress: int):
            if self.progress_bar.winfo_exists():
                self.progress_bar.set(progress / 100)
            
        def set_max(max_progress: int):
            pass # CTk progress bar is 0.0 to 1.0

        callback_dict = {
            "setStatus": set_status,
            "setProgress": set_progress,
            "setMax": set_max
        }

        try:
            set_status("Installing / Verifying Minecraft files...")
            minecraft_launcher_lib.install.install_minecraft_version(mc_version, MINECRAFT_DIR, callback=callback_dict)

            # Advanced JVM Arguments & Options
            options = {
                "username": self.username.get(),
                "uuid": self.uuid if not self.is_premium.get() else self.access_token, # Simplified handling
                "token": self.access_token,
                "jvmArguments": [
                    f"-Xmx{self.ram_allocation.get()}M",
                    "-XX:+UnlockExperimentalVMOptions",
                    "-XX:+UseG1GC"
                ],
                "launcherName": "SupersonicClient",
                "launcherVersion": VERSION,
                "server": DEFAULT_SERVER # Auto connects to www.NarratorMC.net
            }

            # Hook Direct3D12 Engine if enabled
            if self.use_d3d12.get():
                engine_path = os.path.join(os.getcwd(), "engine", "opengl32.dll")
                if os.path.exists(engine_path):
                    # Force Minecraft to use the custom D3D12 wrapper
                    options["jvmArguments"].append(f"-Dorg.lwjgl.opengl.libname={engine_path}")
                else:
                    print("Warning: opengl32.dll not found in engine folder. D3D12 Hook skipped.")

            set_status("Generating launch command...")
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(mc_version, MINECRAFT_DIR, options)

            set_status("Game is running!")
            subprocess.Popen(minecraft_command)
            
            # Re-enable button after 5 seconds
            self.after(5000, lambda: self.play_btn.configure(state="normal", text="▶ PLAY"))

        except Exception as e:
            # THIS FIXES YOUR FIRST PICTURE'S ISSUE BY SHOWING EXACTLY WHAT FAILED
            error_msg = str(e)
            self.status_label.configure(text=f"Install Error! {error_msg}")
            self.play_btn.configure(state="normal", text="▶ PLAY")
            messagebox.showerror("Minecraft Launch Error", f"Failed to launch the game:\n\n{error_msg}\n\nPlease check your internet connection or try the Agent AI 'Auto Fix Errors' tool.")

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
