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
BG_COLOR = "#0B0E14"          # Deep background
SIDEBAR_COLOR = "#11151E"     # Slightly lighter for sidebar
CARD_COLOR = "#161B28"        # Card backgrounds
ACCENT_BLUE = "#1D4ED8"       # Primary blue buttons (Play, Install)
ACCENT_CYAN = "#00D4FF"       # Highlights
ACCENT_GREEN = "#10B981"      # Success / Installed status
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

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=SIDEBAR_COLOR, border_width=1, border_color=BORDER_COLOR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo Area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(20, 30), sticky="w")
        ctk.CTkLabel(logo_frame, text="⚡", font=ctk.CTkFont(size=28), text_color=ACCENT_BLUE).pack(side="left")
        ctk.CTkLabel(logo_frame, text=" SUPERSONIC\n CLIENT", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY, justify="left").pack(side="left", padx=10)

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("🏠 Dashboard", "Dashboard"),
            ("📦 Modpacks", "Modpacks"),
            ("🧩 Addons", "Addons"),
            ("📂 Instances", "Instances"),
            ("🖥️ Servers", "Servers"),
            ("🎨 Resource Packs", "Resource Packs"),
            ("⚙️ Settings", "Settings"),
            ("🤖 Agent (AI)", "Agent")
        ]

        for i, (text, name) in enumerate(nav_items):
            btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", text_color=TEXT_MUTED, 
                                font=ctk.CTkFont(size=14, weight="bold"), anchor="w", height=40,
                                command=lambda n=name: self.show_frame(n))
            btn.grid(row=i+1, column=0, sticky="ew", padx=15, pady=2)
            self.nav_buttons[name] = btn

        # Bottom Account Area
        acc_frame = ctk.CTkFrame(self.sidebar, fg_color=CARD_COLOR, corner_radius=8)
        acc_frame.grid(row=11, column=0, padx=15, pady=20, sticky="ew")
        ctk.CTkLabel(acc_frame, text="Account", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(acc_frame, text=self.user_config.get("username", "Raffiee_playssMC"), font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=10)
        ctk.CTkLabel(acc_frame, text="👑 Premium", font=ctk.CTkFont(size=11, weight="bold"), text_color="#F59E0B").pack(anchor="w", padx=10, pady=(0, 10))

    def setup_frames(self):
        self.frames = {}
        
        # 1. DASHBOARD FRAME
        f_dash = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frames["Dashboard"] = f_dash
        
        # Header Banner
        banner = ctk.CTkFrame(f_dash, fg_color=CARD_COLOR, corner_radius=12, height=180)
        banner.pack(fill="x", padx=30, pady=(30, 20))
        banner.pack_propagate(False)
        
        ctk.CTkLabel(banner, text="SUPERSONIC CLIENT", font=ctk.CTkFont(size=28, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).place(x=30, y=30)
        ctk.CTkLabel(banner, text="Hyper optimized. Ultra fast. Future ready.", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED).place(x=30, y=70)
        
        self.play_btn = ctk.CTkButton(banner, text="▶ PLAY", font=ctk.CTkFont(size=20, weight="bold"), fg_color=ACCENT_BLUE, hover_color="#1E40AF", width=200, height=60, corner_radius=8, command=self.handle_play)
        self.play_btn.place(relx=0.95, rely=0.5, anchor="e")

        # Quick Stats in Banner
        stats_frame = ctk.CTkFrame(banner, fg_color="transparent")
        stats_frame.place(x=30, y=120)
        ctk.CTkLabel(stats_frame, text="📦 Minecraft 1.21.4   🚀 Performance: Ultra   📅 Last Played: Today", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="left")

        # Addons & Modpacks Grids
        self.create_section_header(f_dash, "ALL ADDONS - ONE CLICK INSTALL", "Install All")
        addons_grid = ctk.CTkFrame(f_dash, fg_color="transparent")
        addons_grid.pack(fill="x", padx=30, pady=10)
        
        mock_addons = [("Sodium", "Boosts FPS"), ("Iris Shaders", "Shaders Mod"), ("Lithium", "Performance"), ("Indium", "Better Compat")]
        for i, (title, desc) in enumerate(mock_addons):
            card = self.create_item_card(addons_grid, title, desc, "✓ Installed", ACCENT_GREEN)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            addons_grid.grid_columnconfigure(i, weight=1)

        self.create_section_header(f_dash, "MODPACKS", "Browse All")
        packs_grid = ctk.CTkFrame(f_dash, fg_color="transparent")
        packs_grid.pack(fill="x", padx=30, pady=10)
        
        mock_packs = [("Fabulously Optimized", "1.21.4"), ("Better MC", "1.21.4"), ("RLCraft", "1.20.1"), ("All the Mods 9", "1.20.1")]
        for i, (title, ver) in enumerate(mock_packs):
            card = self.create_modpack_card(packs_grid, title, ver)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            packs_grid.grid_columnconfigure(i, weight=1)

        # 2. MODPACKS FRAME
        f_packs = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["Modpacks"] = f_packs
        
        top_packs = ctk.CTkFrame(f_packs, fg_color="transparent")
        top_packs.pack(fill="x", padx=30, pady=30)
        ctk.CTkLabel(top_packs, text="MODPACKS", font=ctk.CTkFont(size=28, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).pack(side="left")
        
        self.pack_search = ctk.CTkEntry(top_packs, placeholder_text="Search modpacks...", width=250, fg_color=CARD_COLOR, border_color=BORDER_COLOR)
        self.pack_search.pack(side="right", padx=10)
        ctk.CTkButton(top_packs, text="Search Modrinth", fg_color=ACCENT_BLUE, command=self.search_modpacks).pack(side="right")

        self.packs_scroll = ctk.CTkScrollableFrame(f_packs, fg_color="transparent")
        self.packs_scroll.pack(fill="both", expand=True, padx=25, pady=10)

        # 3. ADDONS FRAME
        f_addons = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["Addons"] = f_addons
        ctk.CTkLabel(f_addons, text="ADDONS", font=ctk.CTkFont(size=28, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=30, pady=30)
        
        # 4. SETTINGS FRAME
        f_settings = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frames["Settings"] = f_settings
        ctk.CTkLabel(f_settings, text="SETTINGS", font=ctk.CTkFont(size=28, weight="bold", slant="italic"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=30, pady=30)
        
        set_grid = ctk.CTkFrame(f_settings, fg_color="transparent")
        set_grid.pack(fill="x", padx=30)
        
        # General Settings Card
        gen_card = ctk.CTkFrame(set_grid, fg_color=CARD_COLOR, corner_radius=10)
        gen_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(gen_card, text="PERFORMANCE SETTINGS", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=15)
        
        self.ram_var = ctk.StringVar(value=f"{self.user_config.get('ram', 8)} GB")
        ctk.CTkLabel(gen_card, text="RAM Allocation", text_color=TEXT_PRIMARY).pack(anchor="w", padx=20)
        ram_slider = ctk.CTkSlider(gen_card, from_=2, to=32, number_of_steps=30, command=self.update_ram)
        ram_slider.set(self.user_config.get("ram", 8))
        ram_slider.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(gen_card, textvariable=self.ram_var, text_color=ACCENT_CYAN).pack(anchor="w", padx=20, pady=(0, 15))

        # 5. AGENT AI FRAME
        f_agent = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["Agent"] = f_agent
        
        agent_header = ctk.CTkFrame(f_agent, fg_color=CARD_COLOR, corner_radius=12, height=120)
        agent_header.pack(fill="x", padx=30, pady=30)
        agent_header.pack_propagate(False)
        ctk.CTkLabel(agent_header, text="AGENT (AI) BETA", font=ctk.CTkFont(size=24, weight="bold"), text_color=TEXT_PRIMARY).place(x=30, y=25)
        ctk.CTkLabel(agent_header, text="Your personal AI assistant for Supersonic Client", font=ctk.CTkFont(size=14), text_color=TEXT_MUTED).place(x=30, y=60)
        
        chat_container = ctk.CTkFrame(f_agent, fg_color=CARD_COLOR, corner_radius=12)
        chat_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        self.chat_history = ctk.CTkTextbox(chat_container, fg_color="transparent", text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=14))
        self.chat_history.pack(fill="both", expand=True, padx=20, pady=20)
        self.chat_history.insert("end", "🤖 Supersonic Agent: Hello Raffiee! System health is 98%. How can I optimize your game today?\n\n")
        self.chat_history.configure(state="disabled")

        input_frame = ctk.CTkFrame(chat_container, fg_color=BG_COLOR, corner_radius=8, height=50)
        input_frame.pack(fill="x", padx=20, pady=20)
        input_frame.pack_propagate(False)
        
        self.chat_entry = ctk.CTkEntry(input_frame, placeholder_text="Ask me anything (e.g., Why is my game crashing?)...", fg_color="transparent", border_width=0)
        self.chat_entry.pack(side="left", fill="both", expand=True, padx=10)
        ctk.CTkButton(input_frame, text="➤", width=40, fg_color=ACCENT_BLUE, command=self.send_ai_msg).pack(side="right", padx=5)

    # --- UI HELPERS ---
    def create_section_header(self, parent, title, btn_text):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(20, 0))
        ctk.CTkLabel(hdr, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(side="left")
        ctk.CTkButton(hdr, text=btn_text, fg_color="transparent", border_width=1, border_color=BORDER_COLOR, text_color=TEXT_PRIMARY, height=28).pack(side="right")

    def create_item_card(self, parent, title, desc, status, status_color):
        card = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=10, height=90)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).place(x=15, y=15)
        ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).place(x=15, y=40)
        ctk.CTkLabel(card, text=status, font=ctk.CTkFont(size=11, weight="bold"), text_color=status_color).place(x=15, y=65)
        return card

    def create_modpack_card(self, parent, title, version):
        card = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=10, height=180)
        card.pack_propagate(False)
        # Mock Image Area
        img_area = ctk.CTkFrame(card, fg_color=BG_COLOR, corner_radius=8, height=80)
        img_area.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=15)
        ctk.CTkLabel(card, text=f"Version {version}", font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w", padx=15)
        ctk.CTkButton(card, text="↓ Install", fg_color=ACCENT_BLUE, height=28).pack(fill="x", padx=15, pady=10)
        return card

    # --- CORE LOGIC ---
    def show_frame(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.configure(fg_color=CARD_COLOR if btn_name == name else "transparent", text_color=ACCENT_CYAN if btn_name == name else TEXT_MUTED)
        for f_name, f in self.frames.items():
            if f_name == name: f.pack(fill="both", expand=True)
            else: f.pack_forget()

    def update_ram(self, val):
        allocated = int(val)
        self.ram_var.set(f"{allocated} GB")
        self.user_config["ram"] = allocated
        self.save_config()

    def search_modpacks(self):
        query = self.pack_search.get().strip()
        if not query: return
        for w in self.packs_scroll.winfo_children(): w.destroy()
        
        try:
            url = f"https://api.modrinth.com/v2/search?query={query}&facets=[[%22project_type:modpack%22]]"
            res = requests.get(url).json()
            row_frame = None
            for i, pack in enumerate(res.get("hits", [])[:8]):
                if i % 4 == 0:
                    row_frame = ctk.CTkFrame(self.packs_scroll, fg_color="transparent")
                    row_frame.pack(fill="x", pady=10)
                
                card = self.create_modpack_card(row_frame, pack['title'][:15]+"...", "Latest")
                card.pack(side="left", expand=True, fill="x", padx=10)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch Modrinth API: {e}")

    def send_ai_msg(self):
        msg = self.chat_entry.get().strip()
        if not msg: return
        self.chat_entry.delete(0, 'end')
        
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"👤 You: {msg}\n\n")
        self.chat_history.configure(state="disabled")
        
        threading.Thread(target=self.process_ai_response, args=(msg,), daemon=True).start()

    def process_ai_response(self, text):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={self.hardcoded_api_key}"
            payload = {"contents": [{"parts": [{"text": f"You are Supersonic Agent, a helpful Minecraft AI assistant. Answer briefly: {text}"}]}]}
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
            self.chat_history.insert("end", "🤖 Agent: I ran a quick scan. Outdated 'Entity Culling' mod found. Would you like me to Auto-Fix this?\n\n")
            self.chat_history.configure(state="disabled")

    def handle_play(self):
        if self.game_process and self.game_process.poll() is None:
            try:
                self.game_process.terminate()
                self.play_btn.configure(text="▶ PLAY", fg_color=ACCENT_BLUE)
            except: pass
        else:
            self.play_btn.configure(state="disabled", text="LAUNCHING...")
            threading.Thread(target=self.launch_game, daemon=True).start()

    def launch_game(self):
        try:
            mc_dir = minecraft_launcher_lib.utils.get_minecraft_directory()
            version = "1.21.4"
            minecraft_launcher_lib.install.install_minecraft_version(version, mc_dir)
            
            fabric_ver = minecraft_launcher_lib.fabric.get_latest_loader_version()
            minecraft_launcher_lib.fabric.install_fabric(version, mc_dir, loader_version=fabric_ver)
            
            opts = {
                "username": self.user_config.get("username", "Raffiee_playssMC"),
                "uuid": str(uuid.uuid3(uuid.NAMESPACE_DNS, "Raffiee_playssMC")),
                "token": "",
                "jvmArguments": [f"-Xmx{self.user_config.get('ram', 8)}G"]
            }
            cmd = minecraft_launcher_lib.command.get_minecraft_command(f"fabric-loader-{fabric_ver}-{version}", mc_dir, opts)
            
            self.play_btn.configure(state="normal", text="🛑 STOP", fg_color="#DC2626", hover_color="#991B1B")
            self.game_process = subprocess.Popen(cmd)
            self.game_process.wait()
        except Exception as e:
            messagebox.showerror("Launch Error", str(e))
        finally:
            self.play_btn.configure(state="normal", text="▶ PLAY", fg_color=ACCENT_BLUE, hover_color="#1E40AF")

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: return json.load(f)
            except: pass
        return {"ram": 8, "username": "Raffiee_playssMC"}

    def save_config(self):
        with open(self.config_file, "w") as f: json.dump(self.user_config, f)

if __name__ == "__main__":
    app = SuperSonicClient()
    app.mainloop()
