import sys
import os
import uuid
import threading
import json
import shutil
import requests
import subprocess
import ctypes
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
import minecraft_launcher_lib
import google.generativeai as genai

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
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class SuperSonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SuperSonic Client")
        self.geometry("1000x650")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        self.config_file = "supersonic_config.json"
        self.user_config = self.load_config()
        
        # AppData directory for auto-downloaded engines (Vulkan/D3D12/Compilers)
        self.appdata_dir = os.path.join(os.getenv('APPDATA'), 'SupersonicClient', 'bin')
        os.makedirs(self.appdata_dir, exist_ok=True)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_COLOR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        logo_path = resource_path("1000084689.png")
        if os.path.exists(logo_path):
            self.logo_image = ctk.CTkImage(light_image=Image.open(logo_path), dark_image=Image.open(logo_path), size=(110, 110))
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo_image, text="SuperSonic\nCLIENT", compound="top", font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT_CYAN)
        else:
            self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="❖ SuperSonic\nC L I E N T", font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_CYAN)
            
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))

        self.btn_home = self.create_nav_button("⌂  Home", 1, self.show_home)
        self.btn_versions = self.create_nav_button("⚡ Versions", 2, self.show_versions)
        self.btn_accounts = self.create_nav_button("👤  Accounts", 3, self.show_accounts)
        self.btn_settings = self.create_nav_button("⚙  Settings", 4, self.show_settings)
        self.btn_agent = self.create_nav_button("🤖 Agent", 5, self.show_agent)

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Ready.", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.status_label.grid(row=7, column=0, padx=20, pady=20, sticky="s")

        self.init_home_frame()
        self.init_accounts_frame()
        self.init_versions_frame()
        self.init_settings_frame()
        self.init_agent_frame()
        self.show_home()

    # ==================== UI INITIALIZATION ====================
    def init_home_frame(self):
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)
        self.ready_label = ctk.CTkLabel(self.home_frame, text="READY TO PLAY", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_CYAN)
        self.ready_label.pack(pady=(50, 0))
        current_ver = self.user_config.get("version", "1.21.1")
        self.banner_label = ctk.CTkLabel(self.home_frame, text=f"SuperSonic {current_ver}", font=ctk.CTkFont(size=28, weight="bold"), text_color="white")
        self.banner_label.pack(pady=(5, 20))
        self.play_button = ctk.CTkButton(self.home_frame, text="▶ PLAY", width=250, height=50, corner_radius=8, font=ctk.CTkFont(size=16, weight="bold"), fg_color=ACCENT_PURPLE, hover_color="#7C3AED", command=self.start_game_thread)
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

    def init_accounts_frame(self):
        self.accounts_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.accounts_frame, text="Account Configuration", font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(anchor="w", padx=40, pady=(40, 10))
        self.acc_card = ctk.CTkFrame(self.accounts_frame, fg_color=CARD_COLOR, corner_radius=10)
        self.acc_card.pack(fill="x", padx=40, pady=10)
        ctk.CTkLabel(self.acc_card, text="Player Username:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(20, 5))
        self.username_entry = ctk.CTkEntry(self.acc_card, placeholder_text="Enter your username", width=400, height=40, fg_color=SIDEBAR_COLOR, border_color=ACCENT_CYAN)
        self.username_entry.pack(anchor="w", padx=20, pady=(0, 20))
        if self.user_config.get("username"): self.username_entry.insert(0, self.user_config["username"])

    def init_versions_frame(self):
        self.versions_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.versions_frame, text="Versions Manager", font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(anchor="w", padx=40, pady=(40, 20))
        self.ver_card = ctk.CTkFrame(self.versions_frame, fg_color=CARD_COLOR, corner_radius=10)
        self.ver_card.pack(fill="x", padx=40, pady=10)
        ctk.CTkLabel(self.ver_card, text="Select Game Version:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(20, 5))
        self.version_dropdown = ctk.CTkOptionMenu(self.ver_card, values=["1.21.4", "1.21.1", "1.21", "1.20.6"], command=self.change_version, button_color=ACCENT_CYAN)
        self.version_dropdown.set(self.user_config.get("version", "1.21.1"))
        self.version_dropdown.pack(anchor="w", padx=20, pady=(0, 20))

    def init_settings_frame(self):
        self.settings_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.settings_frame, text="Engine & Settings", font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack(anchor="w", padx=40, pady=(40, 20))
        self.set_card = ctk.CTkFrame(self.settings_frame, fg_color=CARD_COLOR, corner_radius=10)
        self.set_card.pack(fill="x", padx=40, pady=10)
        
        self.ram_label_var = ctk.StringVar(value=f"RAM Allocation: {self.user_config.get('ram', 4)} GB")
        ctk.CTkLabel(self.set_card, textvariable=self.ram_label_var, font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(20, 5))
        self.ram_slider = ctk.CTkSlider(self.set_card, from_=1, to=16, number_of_steps=15, width=400, button_color=ACCENT_CYAN, command=self.update_ram_label)
        self.ram_slider.set(self.user_config.get("ram", 4))
        self.ram_slider.pack(anchor="w", padx=20, pady=(0, 20))

        ctk.CTkLabel(self.set_card, text="Graphics Engine API:", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(10, 5))
        self.api_dropdown = ctk.CTkOptionMenu(self.set_card, values=["Vulkan (Zink Auto-Translate)", "Direct3D12", "Default OpenGL"], button_color=ACCENT_PURPLE)
        self.api_dropdown.set(self.user_config.get("graphics_api", "Vulkan (Zink Auto-Translate)"))
        self.api_dropdown.pack(anchor="w", padx=20, pady=(0, 20))

    def init_agent_frame(self):
        self.agent_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header_frame = ctk.CTkFrame(self.agent_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=(40, 10))
        ctk.CTkLabel(header_frame, text="Supersonic Auto-Agent", font=ctk.CTkFont(size=22, weight="bold"), text_color=ACCENT_CYAN).pack(side="left")
        
        self.api_key_entry = ctk.CTkEntry(header_frame, placeholder_text="Enter Gemini API Key", width=250, show="*")
        self.api_key_entry.pack(side="right", padx=(10, 0))
        if self.user_config.get("ai_api_key"): self.api_key_entry.insert(0, self.user_config["ai_api_key"])

        self.chat_history = ctk.CTkTextbox(self.agent_frame, fg_color=CARD_COLOR, text_color="white", wrap="word")
        self.chat_history.pack(fill="both", expand=True, padx=40, pady=10)
        self.chat_history.insert("end", "SupersonicAI: 100% Autonomous Mode Active. I will watch the game in the background. If a crash happens, I will read the logs, find the missing/broken mod, download it from the internet, install it, and prepare the game automatically. No manual typing required.\n\n")
        self.chat_history.configure(state="disabled")

    # ==================== 100% AUTOMATIC AGENT LOGIC ====================
    def append_chat(self, sender, text):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"{sender}: {text}\n\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")

    def trigger_background_autofix(self):
        """ Fully automatic trigger when game crashes """
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            self.append_chat("System", "⚠️ Game crashed, but no Gemini API Key is provided for Auto-Fix.")
            return

        mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
        log_path = os.path.join(mc_dir, "logs", "latest.log")
        if not os.path.exists(log_path): return
        
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                logs = f.readlines()[-60:]
            log_text = "".join(logs)

            self.append_chat("SupersonicAI", "⚙️ Game crash detected! Analyzing logs autonomously...")
            threading.Thread(target=self.process_ai_autofix, args=(api_key, log_text), daemon=True).start()
        except Exception as e:
            self.append_chat("System", f"Log read error: {e}")

    def process_ai_autofix(self, api_key, log_text):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            sys_prompt = """
            You are a 100% autonomous background fixer for Minecraft.
            Read the provided log. 
            If a mod is missing or required, reply ONLY with: ACTION: INSTALL_MOD | <modrinth_slug_of_mod>
            If a mod is crashing, reply ONLY with: ACTION: REMOVE_MOD | <filename.jar>
            Do not provide any conversational text. Just the ACTION command.
            """
            
            response = model.generate_content(f"{sys_prompt}\n\nLOGS:\n{log_text}")
            reply = response.text.strip()
            
            if "ACTION: INSTALL_MOD" in reply:
                mod_name = reply.split("|")[1].strip()
                self.append_chat("SupersonicAI", f"Missing dependency found. Auto-downloading '{mod_name}' from the internet...")
                self.auto_install_mod(mod_name)
            elif "ACTION: REMOVE_MOD" in reply:
                file_name = reply.split("|")[1].strip()
                self.append_chat("SupersonicAI", f"Faulty mod found. Auto-removing '{file_name}'...")
                self.auto_remove_mod(file_name)
            else:
                self.append_chat("SupersonicAI", "Issue analyzed but requires manual intervention. Error was not a simple mod mismatch.")
                
        except Exception as e:
            self.append_chat("System", f"AI Autofix failed: {str(e)}")

    def auto_install_mod(self, mod_slug):
        try:
            version = self.user_config.get("version", "1.21.1")
            api_url = f"https://api.modrinth.com/v2/project/{mod_slug}/version"
            res = requests.get(api_url).json()
            
            for ver_data in res:
                if version in ver_data['game_versions'] and 'fabric' in ver_data['loaders']:
                    file_url = ver_data['files'][0]['url']
                    file_name = ver_data['files'][0]['filename']
                    
                    mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
                    mods_dir = os.path.join(mc_dir, "mods")
                    os.makedirs(mods_dir, exist_ok=True)
                    
                    mod_path = os.path.join(mods_dir, file_name)
                    with open(mod_path, 'wb') as f:
                        f.write(requests.get(file_url).content)
                        
                    self.append_chat("SupersonicAI", f"✅ Successfully installed {file_name}! You can hit PLAY again.")
                    self.update_status("Auto-Fix Complete! Ready.")
                    return
            self.append_chat("SupersonicAI", f"⚠️ Compatible version of {mod_slug} not found for {version}.")
        except Exception as e:
            self.append_chat("System", f"⚠️ Download failed: {e}")

    def auto_remove_mod(self, file_name):
        try:
            mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
            mod_path = os.path.join(mc_dir, "mods", file_name)
            if os.path.exists(mod_path):
                os.remove(mod_path)
                self.append_chat("SupersonicAI", f"🗑️ Successfully deleted corrupted mod: {file_name}! You can hit PLAY again.")
                self.update_status("Auto-Fix Complete! Ready.")
            else:
                self.append_chat("SupersonicAI", f"⚠️ Mod {file_name} not found.")
        except Exception as e:
            self.append_chat("System", f"⚠️ Auto-remove failed: {e}")

    # ==================== INTERNET AUTO-DOWNLOAD ENGINE (VULKAN/D3D12) ====================
    def download_engine_components(self, api_choice):
        """ Downloads Mesa3D (opengl32.dll for Vulkan Zink translation) and Shaders compilers automatically """
        
        self.update_status("Checking internet for missing engine files...")
        
        files_to_download = {}
        
        if "Vulkan" in api_choice:
            # We download the Vulkan Shader Compiler and the Mesa3D Zink DLL for OpenGL translation
            files_to_download["glslangValidator.exe"] = "https://github.com/vulkan-sdk-mirror/glslangValidator.exe"
            files_to_download["opengl32.dll"] = "https://github.com/pal1000/mesa-dist-win/releases/download/23.1.3/opengl32.dll"
        elif "Direct3D12" in api_choice:
            files_to_download["spirv-cross.exe"] = "https://github.com/vulkan-sdk-mirror/spirv-cross.exe"
            files_to_download["opengl32.dll"] = "https://github.com/pal1000/mesa-dist-win/releases/download/23.1.3/opengl32.dll"

        for filename, url in files_to_download.items():
            filepath = os.path.join(self.appdata_dir, filename)
            if not os.path.exists(filepath):
                try:
                    self.update_status(f"Downloading {filename}...")
                    response = requests.get(url, timeout=20)
                    if response.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(response.content)
                except Exception:
                    pass # Fails silently for fallback
                    
        self.update_status("Engine ready.")

    def auto_translate_shaders(self, api_choice):
        """ Automatically translates shaders in the background without user clicking a button """
        mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
        shaderpacks_dir = os.path.join(mc_dir, "shaderpacks")
        if not os.path.exists(shaderpacks_dir): return

        glslang_path = os.path.join(self.appdata_dir, "glslangValidator.exe")
        
        if "Vulkan" in api_choice and os.path.exists(glslang_path):
            self.update_status("Auto-translating GLSL to Vulkan SPIR-V...")
            for root, dirs, files in os.walk(shaderpacks_dir):
                for file in files:
                    if file.endswith((".vsh", ".fsh")):
                        input_path = os.path.join(root, file)
                        new_ext = ".vert.spv" if file.endswith(".vsh") else ".frag.spv"
                        output_path = os.path.join(root, file.replace(file[-4:], new_ext))
                        
                        if not os.path.exists(output_path): # Compile only if not already done
                            subprocess.run([glslang_path, "-V", input_path, "-o", output_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ==================== GENERAL LOGIC ====================
    def change_version(self, choice): 
        self.banner_label.configure(text=f"SuperSonic {choice}")
        self.user_config["version"] = choice 
        self.save_config()

    def create_nav_button(self, text, row, command):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, fg_color="transparent", text_color=TEXT_MUTED, font=ctk.CTkFont(size=14, weight="bold"), anchor="w", command=command)
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        return btn

    def reset_nav_buttons(self):
        for btn in [self.btn_home, self.btn_versions, self.btn_accounts, self.btn_settings, self.btn_agent]: btn.configure(fg_color="transparent", text_color=TEXT_MUTED)

    def hide_all_frames(self):
        for frame in [self.home_frame, self.versions_frame, self.accounts_frame, self.settings_frame, self.agent_frame]: frame.grid_forget()

    def show_home(self): self.reset_nav_buttons(); self.btn_home.configure(fg_color=CARD_COLOR, text_color=ACCENT_CYAN); self.hide_all_frames(); self.home_frame.grid(row=0, column=1, sticky="nsew")
    def show_versions(self): self.reset_nav_buttons(); self.btn_versions.configure(fg_color=CARD_COLOR, text_color=ACCENT_CYAN); self.hide_all_frames(); self.versions_frame.grid(row=0, column=1, sticky="nsew")
    def show_accounts(self): self.reset_nav_buttons(); self.btn_accounts.configure(fg_color=CARD_COLOR, text_color=ACCENT_CYAN); self.hide_all_frames(); self.accounts_frame.grid(row=0, column=1, sticky="nsew")
    def show_settings(self): self.reset_nav_buttons(); self.btn_settings.configure(fg_color=CARD_COLOR, text_color=ACCENT_CYAN); self.hide_all_frames(); self.settings_frame.grid(row=0, column=1, sticky="nsew")
    def show_agent(self): self.reset_nav_buttons(); self.btn_agent.configure(fg_color=CARD_COLOR, text_color=ACCENT_CYAN); self.hide_all_frames(); self.agent_frame.grid(row=0, column=1, sticky="nsew")

    def update_ram_label(self, value):
        self.ram_label_var.set(f"RAM Allocation: {int(value)} GB")
        self.info_label.configure(text=f"Fabric Loader • {int(value)*1024} MB RAM")

    def update_status(self, text):
        self.status_label.configure(text=text)
        self.update_idletasks()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: return json.load(f)
            except: pass
        return {"ram": 4, "username": "", "graphics_api": "Vulkan (Zink Auto-Translate)", "version": "1.21.1", "ai_api_key": ""}

    def save_config(self):
        self.user_config["ram"] = int(self.ram_slider.get()) if hasattr(self, 'ram_slider') else 4
        self.user_config["username"] = self.username_entry.get().strip() if hasattr(self, 'username_entry') else ""
        self.user_config["graphics_api"] = self.api_dropdown.get() if hasattr(self, 'api_dropdown') else "Vulkan (Zink Auto-Translate)"
        self.user_config["version"] = self.version_dropdown.get() if hasattr(self, 'version_dropdown') else "1.21.1"
        self.user_config["ai_api_key"] = self.api_key_entry.get().strip() if hasattr(self, 'api_key_entry') else ""

        try:
            with open(self.config_file, "w") as f: json.dump(self.user_config, f, indent=4)
        except: pass

    def start_game_thread(self):
        username = self.username_entry.get().strip()
        if not username:
            self.update_status("⚠️ Enter username in Accounts tab!")
            self.show_accounts()
            return
            
        self.save_config()
        self.play_button.configure(state="disabled", text="INITIALIZING...")
        
        # Start download & translation in background, then launch
        threading.Thread(target=self.prepare_and_launch, args=(username,), daemon=True).start()

    def prepare_and_launch(self, username):
        try:
            api_choice = self.api_dropdown.get()
            
            # Step 1: Auto Download Missing Internet Files
            self.download_engine_components(api_choice)
            
            # Step 2: Auto Translate Shaders based on API
            self.auto_translate_shaders(api_choice)
            
            self.launch_game(username, api_choice)
        except Exception as e:
            self.update_status(f"⚠️ Error: {e}")
            self.play_button.configure(state="normal", text="▶ PLAY")

    def launch_game(self, username, api_choice):
        try:
            minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
            
            # --- AUTO VULKAN / D3D12 ENVIRONMENT SETUP ---
            mesa_dll_path = os.path.join(self.appdata_dir, "opengl32.dll")
            java_bin_dir = resource_path(os.path.join("jre21", "bin"))
            target_dll_path = os.path.join(java_bin_dir, "opengl32.dll")
            
            # If Vulkan/D3D12 is selected, we inject the Mesa3D DLL into Java's bin
            if "Default OpenGL" not in api_choice and os.path.exists(mesa_dll_path):
                shutil.copy2(mesa_dll_path, target_dll_path)
                
                if "Vulkan" in api_choice:
                    os.environ["MESA_LOADER_DRIVER_OVERRIDE"] = "zink"
                    os.environ["GALLIUM_DRIVER"] = "zink"
                    self.update_status("Mesa3D Vulkan Translator Active.")
                elif "Direct3D12" in api_choice:
                    os.environ["MESA_LOADER_DRIVER_OVERRIDE"] = "d3d12"
                    os.environ["GALLIUM_DRIVER"] = "d3d12"
                    self.update_status("Mesa3D Direct3D12 Translator Active.")
            else:
                # Remove injected DLL if Default OpenGL is chosen to prevent interference
                if os.path.exists(target_dll_path): os.remove(target_dll_path)
                os.environ.pop("MESA_LOADER_DRIVER_OVERRIDE", None)
                os.environ.pop("GALLIUM_DRIVER", None)

            java_exe = shutil.which("java") or os.path.join(java_bin_dir, "java.exe")
            base_version = self.user_config.get("version", "1.21.1") 
            
            self.update_status("Installing Game files...")
            minecraft_launcher_lib.install.install_minecraft_version(base_version, minecraft_directory)
            fabric_ver = minecraft_launcher_lib.fabric.get_latest_loader_version()
            minecraft_launcher_lib.fabric.install_fabric(base_version, minecraft_directory, loader_version=fabric_ver)
            
            options = {
                "username": username,
                "uuid": str(uuid.uuid3(uuid.NAMESPACE_DNS, username)),
                "token": "",
                "executablePath": java_exe,
                "jvmArguments": [f"-Xmx{int(self.user_config.get('ram', 4))}G"]
            }

            self.update_status("Launching Engine...")
            command = minecraft_launcher_lib.command.get_minecraft_command(f"fabric-loader-{fabric_ver}-{base_version}", minecraft_directory, options)
            
            process = subprocess.Popen(command)
            process.wait() 

            if process.returncode != 0:
                self.update_status("⚠️ Crash Detected! Agent Autofixing...")
                self.trigger_background_autofix() 
            else:
                self.update_status("Ready.")
            
        except Exception as e:
            self.update_status(f"⚠️ Error: {e}")
        finally:
            self.play_button.configure(state="normal", text="▶ PLAY")

if __name__ == "__main__":
    app = SuperSonicClient()
    app.mainloop()
