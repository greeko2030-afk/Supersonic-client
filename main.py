import sys
import os
import uuid
import threading
import json
import shutil
import requests
import customtkinter as ctk
from tkinter import filedialog
import minecraft_launcher_lib

# --- THEME SETTINGS (Matching NarratorMC Web UI) ---
ctk.set_appearance_mode("dark")
BG_COLOR = "#07090E"        # Deep Dark Blue/Black
SIDEBAR_COLOR = "#0B0E14"   # Slightly lighter for sidebar
CARD_COLOR = "#121722"      # Card background
ACCENT_CYAN = "#00E5FF"     # Neon Cyan
ACCENT_PURPLE = "#8B5CF6"   # Vibrant Purple for Launch Button
TEXT_MUTED = "#8A93A6"      # Gray text

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class NarratorMCLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        # UI Window Setup
        self.title("NarratorMC Launcher")
        self.geometry("1000x650")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)

        self.config_file = "narratormc_config.json"
        self.user_config = self.load_config()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_COLOR)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="❖ Supersonic\sC L I E N T", 
                                       font=ctk.CTkFont(size=18, weight="bold"), text_color=ACCENT_CYAN)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 40))

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
        self.ready_label.pack(pady=(60, 0))

        self.banner_label = ctk.CTkLabel(self.home_frame, text="NarratorMC 1.20.4", font=ctk.CTkFont(size=28, weight="bold"), text_color="white")
        self.banner_label.pack(pady=(5, 20))

        self.play_button = ctk.CTkButton(self.home_frame, text="▶ LAUNCH GAME", width=250, height=50, 
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

        # Username Card
        self.acc_c
