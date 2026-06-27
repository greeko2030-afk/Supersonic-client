import sys
import os
import subprocess
import uuid
import threading
import requests
import json
import customtkinter as ctk
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
        self.geometry("600x400")
        self.resizable(False, False)

        # Title Label
        self.title_label = ctk.CTkLabel(self, text="SUPERSONIC CLIENT", font=ctk.CTkFont(size=30, weight="bold"))
        self.title_label.pack(pady=(40, 20))

        # Username Input
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Enter Username", width=250, height=40, font=ctk.CTkFont(size=14))
        self.username_entry.pack(pady=20)

        # Play Button
        self.play_button = ctk.CTkButton(self, text="PLAY MINECRAFT", width=250, height=50, font=ctk.CTkFont(size=16, weight="bold"), command=self.start_game_thread)
        self.play_button.pack(pady=10)

        # Status Label (Shows download progress)
        self.status_label = ctk.CTkLabel(self, text="Ready to launch.", font=ctk.CTkFont(size=12), text_color="gray")
        self.status_label.pack(side="bottom",搬pady=20)

    def update_status(self, text):
        """Updates the status label from the background thread"""
        self.status_label.configure(text=text)
        self.update_idletasks()

    def start_game_thread(self):
        """Starts the download/launch process in a separate thread so UI doesn't freeze"""
        username = self.username_entry.get().strip()
        if not username:
            self.update_status("Error: Please enter a username!")
            return

        self.play_button.configure(state="disabled")
        self.update_status("Preparing to launch...")
        
        # Run launch logic in background
        threading.Thread(target=self.launch_game, args=(username,), daemon=True).start()

    def download_mod(self, url, mods_dir, filename):
        """Helper function to download a mod jar file"""
        self.update_status(f"Downloading Mod: {filename}...")
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                with open(os.path.join(mods_dir, filename), "wb") as f:
                    f.write(response.content)
        except Exception as e:
            print(f"Failed to download {filename}: {e}")

    def check_shaders_or_resourcepacks(self, minecraft_directory):
        """Checks if shaders or custom resource packs are actively enabled in options.txt"""
        options_txt = os.path.join(minecraft_directory, "options.txt")
        
        # If options file doesn't exist yet, default to False (Vanilla OpenGL)
        if not os.path.exists(options_txt):
            return False
            
        try:
            with open(options_txt, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Checking if Iris/Oculus shaders are enabled or a non-vanilla resourcepack is active
            has_shader = "shaderPack=" in content and "shaderPack=off" not in content and "shaderPack=\n" not in content
            has_resourcepack = "resourcePacks:[" in content and "resourcePacks:[\"vanilla\"" not in content and "resourcePacks:[]" not in content
            
            return has_shader or has_resourcepack
        except Exception:
            return False

    def launch_game(self, username):
        try:
            minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
            
            # ========================================================
            # DYNAMIC GRAPHICS ENGINE PIPELINE SELECTION
            # ========================================================
            use_d3d12 = self.check_shaders_or_resourcepacks(minecraft_directory)
            
            if use_d3d12:
                self.update_status("Shaders/Pack detected! Activating Direct3D12 Engine...")
                os.environ["MESA_LOADER_DRIVER_OVERRIDE"] = "zink"
                os.environ["GALLIUM_DRIVER"] = "zink"
                os.environ["ZINK_USE_DXIL"] = "1"
            else:
                self.update_status("Vanilla Mode! Running on Native OpenGL Engine...")
                # Clearing environment to fallback to native high FPS driver
                os.environ.pop("MESA_LOADER_DRIVER_OVERRIDE", None)
                os.environ.pop("GALLIUM_DRIVER", None)
                os.environ.pop("ZINK_USE_DXIL", None)
                
            os.environ["__GL_THREADED_OPTIMIZATIONS"] = "1"
            # ========================================================
            
            java_exe = resource_path(os.path.join("jre21", "bin", "java.exe"))
            if not os.path.exists(java_exe):
                self.update_status("Error: Bundled Java 21 not found! Check your build paths.")
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

            mods_dir = os.path.join(minecraft_directory, "mods")
            if not os.path.exists(mods_dir):
                os.makedirs(mods_dir)

            modpack = {
                "Sodium.jar": "https://cdn.modrinth.com/data/AANobbMI/versions/99f1I8Lw/sodium-fabric-0.5.8%2Bmc1.20.4.jar",
                "Lithium.jar": "https://cdn.modrinth.com/data/gv9STw84/versions/dtgXv9C6/lithium-fabric-mc1.20.4-0.12.1.jar",
                "Indium.jar": "https://cdn.modrinth.com/data/g96Y6Ofx/versions/L3R6eKIs/indium-1.0.30%2Bmc1.20.4.jar",
                "CustomSkinLoader.jar": "https://github.com/xland44/CustomSkinLoader/releases/download/14.20/CustomSkinLoader_Fabric-14.20-1.20.4.jar"
            }

            for filename, url in modpack.items():
                if not os.path.exists(os.path.join(mods_dir, filename)):
                    self.download_mod(url, mods_dir, filename)

            # Configuring Custom Skin API
            csl_config_folder = os.path.join(minecraft_directory, "CustomSkinLoader")
            if not os.path.exists(csl_config_folder):
                os.makedirs(csl_config_folder)

            config_path = os.path.join(csl_config_folder, "CustomSkinAPI.json")
            skin_config_data = {
                "enable": True,
                "loadlist": [
                    {
                        "name": "SupersonicSkins",
                        "type": "CustomSkinAPI",
                        "root": f"http://your-addxus-site.com/skins/{username}.png"
                    },
                    {
                        "name": "Mojang",
                        "type": "MojangAPI"
                    }
                ]
            }
            
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(skin_config_data, f, indent=2)
            except Exception as e:
                print(f"Failed to create skin config: {e}")

            self.update_status("Files ready! Generating offline ID...")
            offline_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, username))

            options = {
                "username": username,
                "uuid": offline_uuid,
                "token": "",
                "executablePath": java_exe,
                "jvmArguments": [
                    "-Xmx4G",
                    "-XX:+UnlockExperimentalVMOptions",
                    "-XX:+UseG1GC",
                    "-XX:G1NewSizePercent=20",
                    "-XX:G1ReservePercent=20",
                    "-XX:MaxGCPauseMillis=50",
                    "-XX:G1HeapRegionSize=32M",
                ]
            }

            self.update_status("Launching Game... Generating Log.")
            command = minecraft_launcher_lib.command.get_minecraft_command(launch_version, minecraft_directory, options)
            
            log_file_path = os.path.join(minecraft_directory, "supersonic_crash.log")
            log_file = open(log_file_path, "w")
            
            subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT)
            
            self.update_status(f"Game Launched! Mode: {'D3D12' if use_d3d12 else 'OpenGL'}")
            self.play_button.configure(state="normal")
            
        except Exception as e:
            self.update_status(f"Error: {e}")
            self.play_button.configure(state="normal")

if __name__ == "__main__":
    app = SupersonicLauncher()
    app.mainloop()
