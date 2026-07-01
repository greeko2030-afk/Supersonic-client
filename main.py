import sys
import os
import uuid
import threading
import json
import shutil
import requests
import subprocess
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
import minecraft_launcher_lib

# --- THEME SETTINGS ---
ctk.set_appearance_mode("dark")
BG_COLOR = "#07090E"        
SIDEBAR_COLOR = "#0B0E14"   
CARD_COLOR = "#121722"      
ACCENT_CYAN = "#00E5FF"     
ACCENT_PURPLE = "#8B5CF6"   
TEXT_MUTED = "#8A93A6"      

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SuperSonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()

        # UI Window Setup
        self.title("SuperSonic Client")
        self.geometry("1000x650")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        self.config_file = "supersonic_config.json"
        self.user_config = self.load_config()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_COLOR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        # --- LOGO SETUP ---
        logo_path = resource_path("1000084689.png")
        if os.path.exists(logo_path):
            # Load and resize the logo
            self.logo_image = ctk.CTkImage(light_image=Image.open(logo_path), 
                                           dark_image=Image.open(logo_path), 
                                           size=(110, 110))
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo_image, text="SuperSonic\nCLIENT", 
                                           compound="top", font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT_CYAN)
        else:
            # Fallback text if image is missing
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="❖ SuperSonic\nC L I E N T", 
                                           font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_CYAN)
            
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))

        # Navigation Buttons
        self.btn_home = self.create_nav_button("⌂  Home", 1, self.show_home)
        self.btn_versions = self.create_nav_button("⚡ Versions", 2, self.show_versions)
        self.btn_accounts = self.create_nav_button("👤  Accounts", 3, self.show_accounts)
        self.btn_settings = self.create_nav_button("⚙  Settings", 4, self.show_settings)

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Ready.", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.status_label.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # ==================== HOME FRAME ====================
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)
        
        self.ready_label = ctk.CTkLabel(self.home_frame, text="READY TO PLAY", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_CYAN)
        self.ready_label.pack(pady=(50, 0))

        current_ver = self.user_config.get("version", "1.21.1")
        self.banner_label = ctk.CTkLabel(self.home_frame, text=f"SuperSonic {current_ver}", font=ctk.CTkFont(size=28, weight="bold"), text_color="white")
        self.banner_label.pack(pady=(5, 20))

        self.play_button = ctk.CTkButton(self.home_frame, text="▶ PLAY", width=250, height=50, 
                                         corner_radius=8, font=ctk.CTkFont(size=16, weight="bold"), 
                                         fg_color=ACCENT_PURPLE, hover_color="#7C3AED", command=self.start_game_thread)
        self.play_button.pack(pady=10)
        
        self.info_label = ctk.CTkLabel(self.home_frame, text=f"Fabric Loader • {self.user_config.get('ram', 4)*1024} MB RAM", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.info_label.pack(pady=(0, 40))

        self.server_card = ctk.CTkFrame(self.home_frame, fg_color=CARD_COLOR, corner_radius=10, width=500, height=100)
        self.server_card.pack(pady=10, padx=50, fill="x")
        
        self.server_title = ctk.CTkLabel(self.server_card, text="NarratorMC", font=ctk.CTkFont(size=16, weight="bold"), text_color="white")
        self.server_title.place(x=20, y=15)
        self.server_ip = ctk.CTkLabel(self.server_card, text="www.NarratorMC.net", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        self.server_ip.place(x=20, y=40)
        
        self.server_status = ctk.CTkLabel(self.server_card, text="ONLINE", font=ctk.CTkFont(size=12, weight="bold"), text_color="#10B981", fg_color="#064E3B", corner_radius=5)
        self.server_status.place(relx=0.95, y=20, anchor="ne")

        # ==================== ACCOUNTS FRAME ====================
        self.accounts_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.accounts_frame, text="Account Configuration", font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(anchor="w", padx=40, pady=(40, 10))

        self.acc_container = ctk.CTkFrame(self.accounts_frame, fg_color="transparent")
        self.acc_container.pack(fill="both", expand=True, padx=40, pady=10)

        self.main_panel = ctk.CTkFrame(self.acc_container, fg_color="transparent")
        self.main_panel.pack(fill="both", expand=True, pady=(0, 20))

        self.acc_card = ctk.CTkFrame(self.main_panel, fg_color=CARD_COLOR, corner_radius=10)
        self.acc_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(self.acc_card, text="Player Username:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(20, 5))
        self.username_entry = ctk.CTkEntry(self.acc_card, placeholder_text="Enter your username", width=400, height=40, fg_color=SIDEBAR_COLOR, border_color=ACCENT_CYAN)
        self.username_entry.pack(anchor="w", padx=20, pady=(0, 20))
        if self.user_config.get("username"):
            self.username_entry.insert(0, self.user_config["username"])

        self.skin_card = ctk.CTkFrame(self.main_panel, fg_color=CARD_COLOR, corner_radius=10)
        self.skin_card.pack(fill="x")

        ctk.CTkLabel(self.skin_card, text="Custom In-Game Skin (.png):", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.skin_path_var = ctk.StringVar(value=self.user_config.get("skin_path", ""))
        self.skin_status_label = ctk.CTkLabel(self.skin_card, text="No skin selected (Default Alex/Steve will be used)", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        
        self.btn_select_skin = ctk.CTkButton(self.skin_card, text="Browse Skin File", width=160, fg_color=SIDEBAR_COLOR, border_width=1, border_color=ACCENT_CYAN, hover_color="#1A2233", command=self.select_skin)
        self.btn_select_skin.pack(anchor="w", padx=20, pady=(5, 5))
        self.skin_status_label.pack(anchor="w", padx=20, pady=(0, 20))

        if self.user_config.get("skin_path") and os.path.exists(self.user_config["skin_path"]):
            self.skin_status_label.configure(text=f"Selected: {os.path.basename(self.user_config['skin_path'])}", text_color="#10B981")

        # ==================== VERSIONS FRAME ====================
        self.versions_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.versions_frame, text="Versions Manager", font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(anchor="w", padx=40, pady=(40, 20))

        self.ver_card = ctk.CTkFrame(self.versions_frame, fg_color=CARD_COLOR, corner_radius=10)
        self.ver_card.pack(fill="x", padx=40, pady=10)

        ctk.CTkLabel(self.ver_card, text="Select Game Version (1.20.x / 1.21.x):", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(20, 5))
        
        self.version_options = ["1.21.4", "1.21.1", "1.21", "1.20.6", "1.20.4"]
        
        self.version_dropdown = ctk.CTkOptionMenu(
            self.ver_card, 
            values=self.version_options,
            fg_color=SIDEBAR_COLOR,
            button_color=ACCENT_CYAN,
            button_hover_color="#00B3CC",
            dropdown_fg_color=CARD_COLOR,
            command=self.change_version
        )
        self.version_dropdown.set(current_ver)
        self.version_dropdown.pack(anchor="w", padx=20, pady=(0, 20))

        # ==================== SETTINGS FRAME ====================
        self.settings_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.settings_frame, text="Settings", font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(anchor="w", padx=40, pady=(40, 20))

        self.set_card = ctk.CTkFrame(self.settings_frame, fg_color=CARD_COLOR, corner_radius=10)
        self.set_card.pack(fill="x", padx=40, pady=10)

        self.ram_label_var = ctk.StringVar(value=f"RAM Allocation: {self.user_config.get('ram', 4)} GB")
        ctk.CTkLabel(self.set_card, textvariable=self.ram_label_var, font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(20, 5))
        self.ram_slider = ctk.CTkSlider(self.set_card, from_=1, to=16, number_of_steps=15, width=400, button_color=ACCENT_CYAN, command=self.update_ram_label)
        self.ram_slider.set(self.user_config.get("ram", 4))
        self.ram_slider.pack(anchor="w", padx=20, pady=(0, 20))

        self.shader_switch_var = ctk.IntVar(value=self.user_config.get("enable_shaders", 0))
        self.shader_switch = ctk.CTkSwitch(self.set_card, text="Enable Shaders Engine (D3D12/Zink)", variable=self.shader_switch_var, progress_color=ACCENT_CYAN)
        self.shader_switch.pack(anchor="w", padx=20, pady=(0, 20))

        self.show_home()

    def change_version(self, choice):
        self.banner_label.configure(text=f"SuperSonic {choice}")
        self.save_config()
        self.update_status(f"Version switched to {choice}")

    def select_skin(self):
        filepath = filedialog.askopenfilename(title="Select Minecraft Skin", filetypes=[("PNG Files", "*.png")])
        if filepath:
            self.skin_path_var.set(filepath)
            self.save_config()
            self.skin_status_label.configure(text=f"Selected: {os.path.basename(filepath)}", text_color="#10B981")

    # --- OTHER UI & LOGIC ---
    def create_nav_button(self, text, row, command):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, fg_color="transparent", text_color=TEXT_MUTED, 
                            font=ctk.CTkFont(size=14, weight="bold"), anchor="w", command=command)
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        return btn

    def reset_nav_buttons(self):
        for btn in [self.btn_home, self.btn_versions, self.btn_accounts, self.btn_settings]:
            btn.configure(fg_color="transparent", text_color=TEXT_MUTED)

    def hide_all_frames(self):
        for frame in [self.home_frame, self.versions_frame, self.accounts_frame, self.settings_frame]:
            frame.grid_forget()

    def show_home(self):
        self.reset_nav_buttons()
        self.btn_home.configure(fg_color=CARD_COLOR, text_color=ACCENT_CYAN)
        self.hide_all_frames()
        self.home_frame.grid(row=0, column=1, sticky="nsew")

    def show_versions(self):
        self.reset_nav_buttons()
        self.btn_versions.configure(fg_color=CARD_COLOR, text_color=ACCENT_CYAN)
        self.hide_all_frames()
        self.versions_frame.grid(row=0, column=1, sticky="nsew")

    def show_accounts(self):
        self.reset_nav_buttons()
        self.btn_accounts.configure(fg_color=CARD_COLOR, text_color=ACCENT_CYAN)
        self.hide_all_frames()
        self.accounts_frame.grid(row=0, column=1, sticky="nsew")

    def show_settings(self):
        self.reset_nav_buttons()
        self.btn_settings.configure(fg_color=CARD_COLOR, text_color=ACCENT_CYAN)
        self.hide_all_frames()
        self.settings_frame.grid(row=0, column=1, sticky="nsew")

    def update_ram_label(self, value):
        self.ram_label_var.set(f"RAM Allocation: {int(value)} GB")
        self.info_label.configure(text=f"Fabric Loader • {int(value)*1024} MB RAM")

    def update_status(self, text):
        self.status_label.configure(text=text)
        self.update_idletasks()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"ram": 4, "username": "", "skin_path": "", "enable_shaders": 0, "version": "1.21.1"}

    def save_config(self):
        config = {
            "ram": int(self.ram_slider.get()),
            "username": self.username_entry.get().strip(),
            "skin_path": self.skin_path_var.get(),
            "enable_shaders": self.shader_switch_var.get(),
            "version": self.version_dropdown.get()
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception:
            pass

    def download_mod(self, url, mods_dir, filename):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                with open(os.path.join(mods_dir, filename), "wb") as f:
                    f.write(response.content)
        except Exception:
            pass

    def start_game_thread(self):
        username = self.username_entry.get().strip()
        if not username:
            self.update_status("⚠️ Please enter username in Accounts tab!")
            self.show_accounts()
            return

        self.save_config()
        self.play_button.configure(state="disabled", text="LOADING...")
        threading.Thread(target=self.launch_game, args=(username,), daemon=True).start()

    def launch_game(self, username):
        try:
            minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
            
            use_shaders = self.shader_switch_var.get() == 1
            if use_shaders:
                os.environ["MESA_LOADER_DRIVER_OVERRIDE"] = "zink"
                os.environ["GALLIUM_DRIVER"] = "zink"
                os.environ["ZINK_USE_DXIL"] = "1"
            
            java_exe = shutil.which("java")
            if not java_exe:
                java_exe = resource_path(os.path.join("jre21", "bin", "java.exe"))

            base_version = self.user_config.get("version", "1.21.1")
            callback_dict = {"setStatus": lambda s: self.update_status(f"Loading: {s}")}

            minecraft_launcher_lib.install.install_minecraft_version(base_version, minecraft_directory, callback=callback_dict)
            fabric_version = minecraft_launcher_lib.fabric.get_latest_loader_version()
            minecraft_launcher_lib.fabric.install_fabric(base_version, minecraft_directory, loader_version=fabric_version, callback=callback_dict)
            launch_version = f"fabric-loader-{fabric_version}-{base_version}"

            mods_dir = os.path.join(minecraft_directory, "mods")
            os.makedirs(mods_dir, exist_ok=True)
            
            if base_version == "1.20.4":
                csl_url = "https://github.com/xland44/CustomSkinLoader/releases/download/14.20/CustomSkinLoader_Fabric-14.20-1.20.4.jar"
                csl_file = os.path.join(mods_dir, "CustomSkinLoader.jar")
                if not os.path.exists(csl_file):
                    self.update_status("Downloading Skin Loader...")
                    self.download_mod(csl_url, mods_dir, "CustomSkinLoader.jar")

            skin_path = self.skin_path_var.get()
            if skin_path and os.path.exists(skin_path):
                local_skin_dir = os.path.join(minecraft_directory, "CustomSkinLoader", "LocalSkin", "skins")
                os.makedirs(local_skin_dir, exist_ok=True)
                dest_skin = os.path.join(local_skin_dir, f"{username}.png")
                shutil.copyfile(skin_path, dest_skin)
                self.update_status("Skin applied successfully!")

            offline_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, username))
            allocated_ram = int(self.ram_slider.get())

            options = {
                "username": username,
                "uuid": offline_uuid,
                "token": "",
                "executablePath": java_exe,
                "jvmArguments": [f"-Xmx{allocated_ram}G"]
            }

            self.update_status(f"Launching SuperSonic {base_version}...")
            command = minecraft_launcher_lib.command.get_minecraft_command(launch_version, minecraft_directory, options)
            subprocess.Popen(command)
            
            self.update_status("✅ Game Running!")
            self.play_button.configure(state="normal", text="▶ PLAY")
            
        except Exception as e:
            self.update_status(f"⚠️ Error: {e}")
            self.play_button.configure(state="normal", text="▶ PLAY")

if __name__ == "__main__":
    app = SuperSonicClient()
    app.mainloop()
