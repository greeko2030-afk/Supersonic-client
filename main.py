import os
import json
import uuid
import threading
import subprocess
import platform
import requests
import customtkinter as ctk
import minecraft_launcher_lib

# ==============================================================================
# ENGINE & CORE LOGIC (CRASH FIXED & OPTIMIZATION ADDED)
# ==============================================================================
class SupersonicEngine:
    def __init__(self):
        self.config_file = "supersonic_config.json"
        self.config = self.load_config()
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        
        # টার্গেট ভার্সন 1.21.4 রাখা হয়েছে
        self.target_mc_version = "1.21.4"
        
        # ⚠️ পুরনো renderculling মডটি 1.21.4 এ ক্র্যাশ করায় এটি আপাতত ডিসেবল করা হবে
        self.GITHUB_MOD_URL = "https://raw.githubusercontent.com/greeko2030-afk/Supersonic-client/main/renderculling-1.0.0.jar"
        self.CUSTOM_MOD_NAME = "renderculling-1.0.0.jar"

        # 🚀 Fabulously Optimized এর বিকল্প (Direct .jar URLs)
        # Modrinth থেকে 1.21.4 এর .jar ফাইলের ডিরেক্ট লিংকগুলো এখানে বসিয়ে দিন
        self.PERFORMANCE_MODS = {
            "sodium.jar": "https://cdn.modrinth.com/data/AANobbMI/versions/.../sodium.jar", 
            "lithium.jar": "https://cdn.modrinth.com/data/gvQqBUqZ/versions/.../lithium.jar",
            "entityculling.jar": "https://cdn.modrinth.com/data/NNAgCjsB/versions/.../entityculling.jar"
        }

    def load_config(self):
        default_config = {"ram_mb": 8192, "username": "NarratorPlayer", "uuid": str(uuid.uuid4())}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default_config
        return default_config

    def generate_jvm_args(self):
        ram = self.config.get("ram_mb", 4096)
        return [
            f"-Xms{ram}M", f"-Xmx{ram}M",
            "-XX:+UseZGC", "-XX:+ZGenerational",
            "-Djava.net.preferIPv4Stack=true", "-Dfile.encoding=UTF-8"
        ]

    def inject_github_mods(self, status_callback):
        """Automatically ensures your custom mods from GitHub are in the mods folder before launch"""
        mods_dir = os.path.join(self.minecraft_directory, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        mod_path = os.path.join(mods_dir, self.CUSTOM_MOD_NAME)
        
        if not os.path.exists(mod_path):
            status_callback(f"Status: Fetching {self.CUSTOM_MOD_NAME} from GitHub...")
            try:
                response = requests.get(self.GITHUB_MOD_URL, stream=True, timeout=10)
                if response.status_code == 200:
                    with open(mod_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk: f.write(chunk)
                    status_callback("Status: Custom Mod Injected!")
                else:
                    print(f"Failed to download mod from GitHub. HTTP Status: {response.status_code}")
            except Exception as e:
                print(f"GitHub Mod Injection Error: {e}")

    def install_performance_mods(self, status_callback):
        """Downloads Sodium, Lithium, etc. to mimic Fabulously Optimized"""
        mods_dir = os.path.join(self.minecraft_directory, "mods")
        os.makedirs(mods_dir, exist_ok=True)

        for mod_name, download_url in self.PERFORMANCE_MODS.items():
            if "URL_HERE" in download_url or "..." in download_url:
                continue # স্কিপ করবে যদি সঠিক লিংক না দেওয়া থাকে
                
            mod_path = os.path.join(mods_dir, mod_name)
            if not os.path.exists(mod_path):
                status_callback(f"Status: Installing {mod_name}...")
                try:
                    response = requests.get(download_url, stream=True, timeout=10)
                    if response.status_code == 200:
                        with open(mod_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk: f.write(chunk)
                except Exception as e:
                    print(f"Failed to download {mod_name}: {e}")

    def launch_minecraft(self, status_callback):
        try:
            status_callback("Status: Preparing Fast Launch...")
            os.makedirs(self.minecraft_directory, exist_ok=True)
            callback_dict = {"setStatus": lambda s: status_callback(f"Status: {s}")}

            # 1. Check and Install Vanilla Minecraft
            version_folder = os.path.join(self.minecraft_directory, "versions", self.target_mc_version)
            if not os.path.exists(version_folder):
                status_callback(f"Status: Installing {self.target_mc_version} Vanilla...")
                minecraft_launcher_lib.install.install_minecraft_version(self.target_mc_version, self.minecraft_directory, callback=callback_dict)

            # 2. Safely find or install Fabric
            status_callback("Status: Checking Fabric installation...")
            installed_versions = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_directory)
            
            fabric_version = None
            for ver in installed_versions:
                if "fabric" in ver["id"].lower() and self.target_mc_version in ver["id"]:
                    fabric_version = ver["id"]
                    break
                    
            if not fabric_version:
                status_callback("Status: Installing Fabric Loader...")
                minecraft_launcher_lib.fabric.install_fabric(self.target_mc_version, self.minecraft_directory, callback=callback_dict)
                installed_versions = minecraft_launcher_lib.utils.get_installed_versions(self.minecraft_directory)
                for ver in installed_versions:
                    if "fabric" in ver["id"].lower() and self.target_mc_version in ver["id"]:
                        fabric_version = ver["id"]
                        break
            
            launch_version = fabric_version if fabric_version else self.target_mc_version

            # 3. Inject Mods
            # ⚠️ ক্র্যাশ এড়াতে পুরনো renderculling মডটি আপাতত অফ রাখা হয়েছে:
            # self.inject_github_mods(status_callback) 
            
            # 🚀 পারফরম্যান্স বুস্টের জন্য নতুন অপটিমাইজেশন মড ইন্সটলার:
            self.install_performance_mods(status_callback)

            # 4. Generate Command & Launch
            options = {
                "username": self.config["username"],
                "uuid": self.config["uuid"],
                "token": "",
                "jvmArguments": self.generate_jvm_args(),
                "launcherName": "Supersonic Client",
                "launcherVersion": "2.5.0"
            }

            status_callback(f"Status: Generating command for {launch_version}...")
            cmd = minecraft_launcher_lib.command.get_minecraft_command(launch_version, self.minecraft_directory, options)
            
            status_callback("Status: Firing up Engine...")
            subprocess.Popen(cmd, creationflags=0x08000000 if platform.system() == "Windows" else 0)
            status_callback("Status: Game is Running!")

        except Exception as e:
            status_callback(f"Launch Error: {str(e)}")
            print(f"CRITICAL LAUNCH ERROR: {e}")

# ==============================================================================
# UI INTEGRATION
# ==============================================================================
# Inside your SupersonicClient class:
#
#     def start_game(self):
#         self.play_btn.configure(state="disabled", text="LAUNCHING...")
#         def update_label(msg):
#             self.after(0, lambda: self.status_lbl.configure(text=msg))
#             if "Error" in msg or "Game is Running" in msg:
#                 self.after(0, lambda: self.play_btn.configure(state="normal", text="▶ PLAY"))
#         threading.Thread(target=self.engine.launch_minecraft, args=(update_label,), daemon=True).start()
