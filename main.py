0import sys
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
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class SuperSonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SuperSonic Client - Mod Browser Edition")
        self.geometry("1050x700")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        self.config_file = "supersonic_config.json"
        self.user_config = self.load_config()
        self.appdata_dir = os.path.join(os.getenv('APPDATA'), 'SupersonicClient', 'bin')
        os.makedirs(self.appdata_dir, exist_ok=True)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_COLOR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.btn_home = self.create_nav_button("⌂  Home", 1, self.show_home)
        self.btn_mods = self.create_nav_button("📦 Mods Browser", 2, self.show_mods)
        self.btn_settings = self.create_nav_button("⚙  Settings", 3, self.show_settings)

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Ready.", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.status_label.grid(row=7, column=0, padx=20, pady=20, sticky="s")

        self.init_home_frame()
        self.init_mods_frame()
        self.init_settings_frame()
        self.show_home()

    # --- UI Components ---
    def create_nav_button(self, text, row, command):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, fg_color="transparent", text_color=TEXT_MUTED, font=ctk.CTkFont(size=14, weight="bold"), anchor="w", command=command)
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        return btn

    def init_home_frame(self):
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.home_frame, text="SuperSonic Launcher", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=50)
        ctk.CTkButton(self.home_frame, text="▶ PLAY GAME", width=250, height=50, command=self.start_game_thread).pack(pady=20)

    def init_mods_frame(self):
        self.mods_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.mods_frame, text="Modrinth Browser", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)
        
        search_bar = ctk.CTkFrame(self.mods_frame, fg_color="transparent")
        search_bar.pack(fill="x", padx=20)
        self.search_entry = ctk.CTkEntry(search_bar, placeholder_text="Search mods (e.g. Sodium)...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
        ctk.CTkButton(search_bar, text="Search", width=80, command=self.search_mods).pack(side="right")
        
        self.results_frame = ctk.CTkScrollableFrame(self.mods_frame, fg_color=CARD_COLOR)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def init_settings_frame(self):
        self.settings_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        ctk.CTkLabel(self.settings_frame, text="Settings", font=ctk.CTkFont(size=22)).pack(pady=20)

    # --- Logic ---
    def search_mods(self):
        query = self.search_entry.get()
        if not query: return
        self.update_status("Searching Modrinth...")
        
        for widget in self.results_frame.winfo_children(): widget.destroy()
        
        try:
            url = f"https://api.modrinth.com/v2/search?query={query}&facets=[[%22project_type:mod%22]]"
            response = requests.get(url).json()
            
            for mod in response.get("hits", []):
                card = ctk.CTkFrame(self.results_frame, fg_color=SIDEBAR_COLOR)
                card.pack(fill="x", pady=5, padx=5)
                ctk.CTkLabel(card, text=mod['title'], font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10)
                ctk.CTkButton(card, text="Download", fg_color=ACCENT_PURPLE, command=lambda m=mod['slug']: self.download_mod(m)).pack(anchor="e", padx=10, pady=5)
                ctk.CTkButton(card, text="CurseForge (Search)", fg_color=ACCENT_CYAN, text_color="black", command=lambda m=mod['title']: webbrowser.open(f"https://www.curseforge.com/minecraft/search?search={m}")).pack(anchor="e", padx=10, pady=5)
        except Exception as e: self.update_status(f"Error: {e}")

    def download_mod(self, mod_slug):
        self.update_status(f"Downloading {mod_slug}...")
        try:
            mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
            mods_dir = os.path.join(mc_dir, "mods")
            os.makedirs(mods_dir, exist_ok=True)
            
            ver = self.user_config.get("version", "1.21.1")
            api_url = f"https://api.modrinth.com/v2/project/{mod_slug}/version?game_versions=[\"{ver}\"]"
            versions = requests.get(api_url).json()
            
            if versions:
                file_url = versions[0]['files'][0]['url']
                file_name = versions[0]['files'][0]['filename']
                with open(os.path.join(mods_dir, file_name), 'wb') as f:
                    f.write(requests.get(file_url).content)
                self.update_status(f"Installed {file_name}!")
            else: self.update_status("Version not found.")
        except Exception as e: self.update_status(f"Download Error: {e}")

    # --- Helpers ---
    def show_home(self): self.hide_all(); self.home_frame.grid(row=0, column=1, sticky="nsew")
    def show_mods(self): self.hide_all(); self.mods_frame.grid(row=0, column=1, sticky="nsew")
    def show_settings(self): self.hide_all(); self.settings_frame.grid(row=0, column=1, sticky="nsew")
    def hide_all(self):
        for f in [self.home_frame, self.mods_frame, self.settings_frame]: f.grid_forget()

    def update_status(self, text): self.status_label.configure(text=text)
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f: return json.load(f)
        return {"version": "1.21.1"}

    def start_game_thread(self): threading.Thread(target=self.launch, daemon=True).start()
    
    def launch(self):
        self.update_status("Launching...")
        # (Existing launch logic...)
        self.update_status("Game Closed.")

if __name__ == "__main__":
    app = SuperSonicClient()
    app.mainloop()
