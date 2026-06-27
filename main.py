import sys
import os
import subprocess
import uuid
import threading
import requests
import json
import shutil
import customtkinter as ctk
from tkinter import filedialog
import minecraft_launcher_lib

# Set the modern dark theme for the UI
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SupersonicLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        # UI Window Setup
        self.title("Supersonic Client")
        self.geometry("900x600")
        self.resizable(False, False)

        # Load saved configurations
        self.config_file = "supersonic_config.json"
        self.user_config = self.load_config()

        # ==================== GRID LAYOUT ====================
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) 

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="SUPERSONIC\nCLIENT", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))

        self.btn_home = ctk.CTkButton(self.sidebar_frame, text="Home", fg_color="transparent", command=self.show_home)
        self.btn_home.grid(row=1, column=0, padx=20, pady=10)

        self.btn_versions = ctk.CTkButton(self.sidebar_frame, text="Versions", fg_color="transparent", command=self.show_versions)
        self.btn_versions.grid(row=2, column=0, padx=20, pady=10)

        self.btn_accounts = ctk.CTkButton(self.sidebar_frame, text="Account & Skin", fg_color="transparent", command=self.show_accounts)
        self.btn_accounts.grid(row=3, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(self.sidebar_frame, text="Settings", fg_color="transparent", command=self.show_settings)
        self.btn_settings.grid(row=4, column=0, padx=20, pady=10)

        # Status Label in Sidebar
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Ready.", font=ctk.CTkFont(size=11), text_color="gray")
        self.status_label.grid(row=5, column=0, padx=20, pady=20, sticky="s")

        # ==================== MAIN FRAMES ====================
        
        # 1. HOME FRAME
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)
        
        self.banner_label = ctk.CTkLabel(self.home_frame, text="READY TO PLAY\nSupersonic 1.20.4", font=ctk.CTkFont(size=24, weight="bold"))
        self.banner_label.pack(pady=(100, 20))

        self.username_entry = ctk.CTkEntry(self.home_frame, placeholder_text="Enter Username", width=300, height=40, font=ctk.CTkFont(size=14))
        self.username_entry.pack(pady=20)
        if self.user_config.get("username"):
            self.username_entry.insert(0, self.user_config["username"])

        self.play_button = ctk.CTkButton(self.home_frame, text="LAUNCH GAME", width=300, height=50, corner_radius=10, font=ctk.CTkFont(size=16, weight="bold"), command=self.start_game_thread)
        self.play_button.pack(pady=10)

        # 2. SETTINGS FRAME (Shaders Added)
        self.settings_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        self.settings_title = ctk.CTkLabel(self.settings_frame, text="Settings", font=ctk.CTkFont(size=24, weight="bold"))
        self.settings_title.pack(anchor="w", padx=40, pady=(40, 20))

        # Shader Engine Toggle
        self.shader_switch_var = ctk.IntVar(value=self.user_config.get("enable_shaders", 0))
        self.shader_switch = ctk.CTkSwitch(self.settings_frame, text="Enable Shaders Engine (D3D12/Zink)", variable=self.shader_switch_var, font=ctk.CTkFont(size=14))
        self.shader_switch.pack(anchor="w", padx=40, pady=(0, 10))

        self.btn_open_shaders = ctk.CTkButton(self.settings_frame, text="Open Shaders Folder", width=200, command=self.open_shaders_folder)
        self.btn_open_shaders.pack(anchor="w", padx=40, pady=(0, 20))

        # RAM Slider
        self.ram_label_var = ctk.StringVar(value=f"RAM Allocation: {self.user_config.get('ram', 4)} GB")
        self.ram_label = ctk.CTkLabel(self.settings_frame, textvariable=self.ram_label_var, font=ctk.CTkFont(size=14))
        self.ram_label.pack(anchor="w", padx=40, pady=(10, 0))
        
        self.ram_slider = ctk.CTkSlider(self.settings_frame, from_=1, to=16, number_of_steps=15, width=400, command=self.update_ram_label)
        self.ram_slider.set(self.user_config.get("ram", 4))
        self.ram_slider.pack(anchor="w", padx=40, pady=10)

        # Java Path
        self.java_label = ctk.CTkLabel(self.settings_frame, text="Java Path (Leave empty for bundled Java):", font=ctk.CTkFont(size=14))
        self.java_label.pack(anchor="w", padx=40, pady=(20, 0))

        self.java_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.java_frame.pack(anchor="w", padx=40, pady=5, fill="x")

        self.java_entry = ctk.CTkEntry(self.java_frame, width=400, placeholder_text="Path to java.exe")
        self.java_entry.pack(side="left", padx=(0, 10))
        if self.user_config.get("java_path"):
            self.java_entry.insert(0, self.user_config["java_path"])

        self.btn_autodetect = ctk.CTkButton(self.java_frame, text="Auto-detect", width=100, command=self.auto_detect_java)
        self.btn_autodetect.pack(side="left")

        self.btn_save_settings = ctk.CTkButton(self.settings_frame, text="Save Settings", width=200, command=self.save_config)
        self.btn_save_settings.pack(anchor="w", padx=40, pady=30)

        # 3. ACCOUNTS FRAME (Skin System Added)
        self.accounts_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        self.accounts_title = ctk.CTkLabel(self.accounts_frame, text="Account & Skin Manager", font=ctk.CTkFont(size=24, weight="bold"))
        self.accounts_title.pack(anchor="w", padx=40, pady=(40, 20))

        self.skin_desc_label = ctk.CTkLabel(self.accounts_frame, text="Choose a custom skin (.png) to use offline:", font=ctk.CTkFont(size=14))
        self.skin_desc_label.pack(anchor="w", padx=40, pady=(10, 0))

        self.skin_path_var = ctk.StringVar(value=self.user_config.get("skin_path", "No custom skin selected"))
        self.skin_label = ctk.CTkLabel(self.accounts_frame, textvariable=self.skin_path_var, font=ctk.CTkFont(size=12), text_color="gray")
        self.skin_label.pack(anchor="w", padx=40, pady=(5, 10))

        self.btn_select_skin = ctk.CTkButton(self.accounts_frame, text="Browse Skin (.png)", width=200, command=self.select_skin)
        self.btn_select_skin.pack(anchor="w", padx=40, pady=5)

        # 4. VERSIONS FRAME
        self.versions_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.versions_frame, text="Versions Manager\n(Coming Soon)", font=ctk.CTkFont(size=20)).pack(expand=True)

        # Select default frame
        self.show_home()

    # ==================== UI FRAME LOGIC ====================
    def reset_button_colors(self):
        self.btn_home.configure(fg_color="transparent")
        self.btn_versions.configure(fg_color="transparent")
        self.btn_accounts.configure(fg_color="transparent")
        self.btn_settings.configure(fg_color="transparent")

    def hide_all_frames(self):
        self.home_frame.grid_forget()
        self.versions_frame.grid_forget()
        self.accounts_frame.grid_forget()
        self.settings_frame.grid_forget()

    def show_home(self):
        self.reset_button_colors()
        self.btn_home.configure(fg_color="gray25")
        self.hide_all_frames()
        self.home_frame.grid(row=0, column=1, sticky="nsew")

    def show_versions(self):
        self.reset_button_colors()
        self.btn_versions.configure(fg_color="gray25")
        self.hide_all_frames()
        self.versions_frame.grid(row=0, column=1, sticky="nsew")

    def show_accounts(self):
        self.reset_button_colors()
        self.btn_accounts.configure(fg_color="gray25")
        self.hide_all_frames()
        self.accounts_frame.grid(row=0, column=1, sticky="nsew")

    def show_settings(self):
        self.reset_button_colors()
        self.btn_settings.configure(fg_color="gray25")
        self.hide_all_frames()
        self.settings_frame.grid(row=0, column=1, sticky="nsew")

    # ==================== SETTINGS & SKIN LOGIC ====================
    def update_ram_label(self, value):
        self.ram_label_var.set(f"RAM Allocation: {int(value)} GB")

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
        return {"ram": 4, "java_path": "", "username": "", "skin_path": "", "enable_shaders": 0}

    def save_config(self):
        config = {
            "ram": int(self.ram_slider.get()),
            "java_path": self.java_entry.get().strip(),
            "username": self.username_entry.get().strip(),
            "skin_path": self.skin_path_var.get(),
            "enable_shaders": self.shader_switch_var.get()
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
            self.update_status("✅ Settings saved successfully!")
        except Exception as e:
            self.update_status("⚠️ Error saving settings!")

    def auto_detect_java(self):
        java_path = shutil.which("java")
        if java_path:
            real_path = os.path.realpath(java_path)
            self.java_entry.delete(0, 'end')
            self.java_entry.insert(0, real_path)
            self.update_status("✅ Java auto-detected!")
        else:
            self.update_status("⚠️ Java not found!")

    def select_skin(self):
        filepath = filedialog.askopenfilename(title="Select Minecraft Skin", filetypes=[("PNG Files", "*.png")])
        if filepath:
            self.skin_path_var.set(filepath)
            self.save_config()
            self.update_status("✅ Custom Skin Selected!")

    def open_shaders_folder(self):
        mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
        shaders_dir = os.path.join(mc_dir, "shaderpacks")
        os.makedirs(shaders_dir, exist_ok=True)
        if os.name == 'nt':
            os.startfile(shaders_dir)

    # ==================== LAUNCHER LOGIC ====================
    def download_mod(self, url, mods_dir, filename):
        self.update_status(f"Downloading: {filename}...")
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                with open(os.path.join(mods_dir, filename), "wb") as f:
                    f.write(response.content)
        except Exception as e:
            print(f"Failed to download {filename}: {e}")

    def start_game_thread(self):
        username = self.username_entry.get().strip()
        if not username:
            self.update_status("⚠️ Error: Please enter a username!")
            return

        self.save_config()
        self.play_button.configure(state="disabled")
        self.update_status("Preparing to launch...")
        threading.Thread(target=self.launch_game, args=(username,), daemon=True).start()

    def launch_game(self, username):
        try:
            minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
            
            # GRAPHICS ENGINE PIPELINE SELECTION (From Settings Toggle)
            use_shaders = self.shader_switch_var.get() == 1
            if use_shaders:
                self.update_status("Shaders Engine Activated! (D3D12/Zink)")
                os.environ["MESA_LOADER_DRIVER_OVERRIDE"] = "zink"
                os.environ["GALLIUM_DRIVER"] = "zink"
                os.environ["ZINK_USE_DXIL"] = "1"
            else:
                self.update_status("Vanilla Mode! Running on Native OpenGL...")
                os.environ.pop("MESA_LOADER_DRIVER_OVERRIDE", None)
                os.environ.pop("GALLIUM_DRIVER", None)
                os.environ.pop("ZINK_USE_DXIL", None)
                
            os.environ["__GL_THREADED_OPTIMIZATIONS"] = "1"
            
            # JAVA SELECTION LOGIC
            custom_java = self.java_entry.get().strip()
            if custom_java and os.path.exists(custom_java):
                java_exe = custom_java
            else:
                java_exe = resource_path(os.path.join("jre21", "bin", "java.exe"))
                if not os.path.exists(java_exe):
                    self.update_status("⚠️ Error: Java 21 not found!")
                    self.play_button.configure(state="normal")
                    return

            base_version = "1.20.4"
            
            def print_status(status_text):
                self.update_status(f"Downloading: {status_text}")
                
            callback_dict = {
                "setStatus": print_status,
                "setProgress": lambda p: None,
                "setMax": lambda m: None
            }

            self.update_status(f"Checking Base Minecraft {base_version}...")
            minecraft_launcher_lib.install.install_minecraft_version(base_version, minecraft_directory, callback=callback_dict)
            
            self.update_status("Installing Fabric Optimizer Engine...")
            fabric_version = minecraft_launcher_lib.fabric.get_latest_loader_version()
            minecraft_launcher_lib.fabric.install_fabric(base_version, minecraft_directory, loader_version=fabric_version, callback=callback_dict)
            
            launch_version = f"fabric-loader-{fabric_version}-{base_version}"

            # MODS DOWNLOAD
            mods_dir = os.path.join(minecraft_directory, "mods")
            os.makedirs(mods_dir, exist_ok=True)

            modpack = {
                "Sodium.jar": "https://cdn.modrinth.com/data/AANobbMI/versions/99f1I8Lw/sodium-fabric-0.5.8%2Bmc1.20.4.jar",
                "Lithium.jar": "https://cdn.modrinth.com/data/gv9STw84/versions/dtgXv9C6/lithium-fabric-mc1.20.4-0.12.1.jar",
                "Iris.jar": "https://cdn.modrinth.com/data/YL57xq9U/versions/1uQ0mR2k/iris-1.7.0%2Bmc1.20.4.jar",
                "Sodium-Extra.jar": "https://cdn.modrinth.com/data/PtjYWJkn/versions/0.5.4%2Bmc1.20.4/sodium-extra-0.5.4%2Bmc1.20.4.jar",
                "CustomSkinLoader.jar": "https://github.com/xland44/CustomSkinLoader/releases/download/14.20/CustomSkinLoader_Fabric-14.20-1.20.4.jar"
            }

            for filename, url in modpack.items():
                if not os.path.exists(os.path.join(mods_dir, filename)):
                    self.download_mod(url, mods_dir, filename)

            # CONFIGURE CUSTOM SKIN SYSTEM
            csl_config_folder = os.path.join(minecraft_directory, "CustomSkinLoader")
            os.makedirs(csl_config_folder, exist_ok=True)

            # Copy selected skin file to LocalSkin folder
            skin_path = self.user_config.get("skin_path", "")
            if skin_path and os.path.exists(skin_path):
                local_skin_dir = os.path.join(csl_config_folder, "LocalSkin", "skins")
                os.makedirs(local_skin_dir, exist_ok=True)
                dest_skin = os.path.join(local_skin_dir, f"{username}.png")
                try:
                    shutil.copyfile(skin_path, dest_skin)
                except Exception as e:
                    print(f"Skin Apply Error: {e}")

            config_path = os.path.join(csl_config_folder, "CustomSkinAPI.json")
            skin_config_data = {
                "enable": True,
                "loadlist": [
                    {"name": "SupersonicSkins", "type": "CustomSkinAPI", "root": f"http://addxus.com/skins/{username}.png"},
                    {"name": "Mojang", "type": "MojangAPI"}
                ]
            }
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(skin_config_data, f, indent=2)
            except Exception:
                pass

            self.update_status("Files ready! Generating offline ID...")
            offline_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, username))
            allocated_ram = int(self.ram_slider.get())

            options = {
                "username": username,
                "uuid": offline_uuid,
                "token": "",
                "executablePath": java_exe,
                "jvmArguments": [
                    f"-Xmx{allocated_ram}G",
                    "-XX:+UnlockExperimentalVMOptions",
                    "-XX:+UseG1GC",
                    "-XX:G1NewSizePercent=20",
                    "-XX:G1ReservePercent=20",
                    "-XX:MaxGCPauseMillis=50",
                    "-XX:G1HeapRegionSize=32M",
                ]
            }

            self.update_status("Launching Supersonic Client...")
            command = minecraft_launcher_lib.command.get_minecraft_command(launch_version, minecraft_directory, options)
            
            log_file_path = os.path.join(minecraft_directory, "supersonic_crash.log")
            log_file = open(log_file_path, "w")
            
            subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT)
            
            self.update_status(f"✅ Game Launched! Engine: {'D3D12' if use_shaders else 'OpenGL'}")
            self.play_button.configure(state="normal")
            
        except Exception as e:
            self.update_status(f"⚠️ Launch Error: {e}")
            self.play_button.configure(state="normal")

if __name__ == "__main__":
    app = SupersonicLauncher()
    app.mainloop()
