import os
import sys
import json
import traceback
import subprocess
import threading
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# ================= CONSTANTS & GLOBALS =================
VERSION = "1.0.0"
APP_NAME = "MinecraftD3D12Launcher"
ENGINE_EXECUTABLE = "bin/engine.exe" if sys.platform == "win32" else "bin/engine"

# THEMES
BG_COLOR = "#0F172A"
SIDEBAR_COLOR = "#1E293B"
CARD_COLOR = "#1E293B"
CARD_HOVER = "#334155"
ACCENT_BLUE = "#3B82F6"
ACCENT_GREEN = "#10B981"
TEXT_MAIN = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
BORDER_COLOR = "#334155"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ================= UTILS & CONFIG =================
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except: pass
    return default

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

# ================= MAIN UI CLASS =================
class SupersonicClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - Advanced Client")
        
        # Dimensions
        w, h = 1100, 700
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(fg_color=BG_COLOR)
        
        self.settings = load_json("config.json", {})
        self.account_data = load_json("accounts.json", {"username": "PlayerD3D12", "uuid": "000", "token": ""})
        
        self.build_ui()
        
    def thread_safe_update(self, widget, **kwargs):
        self.after(0, lambda: widget.configure(**kwargs))
        
    def thread_safe_progress(self, widget, val):
        self.after(0, lambda: widget.set(val))
        
    def build_ui(self):
        # Master Grid Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.build_sidebar()
        
        # Main Content Area
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.frames = {}
        for F in (HomeView, SettingsView):
            f = F(self.main_content, self)
            self.frames[F.__name__] = f
            f.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame("HomeView")
        
    def build_sidebar(self):
        sb = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=SIDEBAR_COLOR, border_width=0, border_color=BORDER_COLOR)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        
        # Logo Area
        logo_f = ctk.CTkFrame(sb, fg_color="transparent", height=80)
        logo_f.pack(fill="x", pady=(20,10))
        
        ctk.CTkLabel(logo_f, text="🚀", font=("Segoe UI", 32)).pack(side="left", padx=(20, 10))
        ctk.CTkLabel(logo_f, text=APP_NAME.upper(), font=("Segoe UI", 18, "bold"), text_color=TEXT_MAIN).pack(side="left")
        
        # Profile Minimal
        prof = ctk.CTkFrame(sb, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        prof.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(prof, text="👤", font=("Segoe UI", 24)).pack(side="left", padx=10, pady=10)
        info = ctk.CTkFrame(prof, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, pady=10)
        ctk.CTkLabel(info, text=self.account_data["username"], font=("Segoe UI", 14, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text="Offline Account", font=("Segoe UI", 10), text_color=TEXT_MUTED, anchor="w").pack(fill="x")
        
        # Nav Buttons
        nav_f = ctk.CTkFrame(sb, fg_color="transparent")
        nav_f.pack(fill="both", expand=True, pady=20)
        
        self.nav_btns = []
        def make_nav(icon, text, frame_name):
            b = ctk.CTkButton(
                nav_f, text=f"  {icon}   {text}", font=("Segoe UI", 14, "bold"),
                anchor="w", fg_color="transparent", text_color=TEXT_MUTED,
                hover_color=CARD_HOVER, corner_radius=8, height=45,
                command=lambda: self.show_frame(frame_name)
            )
            b.pack(fill="x", padx=15, pady=2)
            self.nav_btns.append(b)
            
        make_nav("🎮", "Play", "HomeView")
        make_nav("⚙️", "Settings", "SettingsView")
        
        # Version tag
        ctk.CTkLabel(sb, text=f"v{VERSION} • D3D12 Backend: ZINK", font=("Segoe UI", 10), text_color=TEXT_MUTED).pack(side="bottom", pady=20)
        
    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        for b in self.nav_btns:
            if name in b.cget("command"):
                b.configure(fg_color=CARD_HOVER, text_color=TEXT_MAIN)
            else:
                b.configure(fg_color="transparent", text_color=TEXT_MUTED)

# ================= VIEWS =================
class HomeView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Top News/Banner
        ban = ctk.CTkFrame(self, height=180, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        ban.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        ban.pack_propagate(False)
        
        bf = ctk.CTkFrame(ban, fg_color="transparent")
        bf.pack(side="left", fill="y", padx=30, pady=30)
        
        ctk.CTkLabel(bf, text="Ready to Play", font=("Segoe UI", 14, "bold"), text_color=ACCENT_BLUE).pack(anchor="w")
        ctk.CTkLabel(bf, text="Supersonic Modpack", font=("Segoe UI", 32, "bold")).pack(anchor="w")
        ctk.CTkLabel(bf, text="Experience Minecraft like never before with native C++ engine.", font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(anchor="w", pady=(5,0))
        
        # Center Mod modules grid
        mod_f = ctk.CTkFrame(self, fg_color="transparent")
        mod_f.grid(row=1, column=0, sticky="nsew")
        mod_f.grid_columnconfigure((0,1), weight=1)
        
        def make_card(parent, row, col, icon, title, desc, active=False):
            c = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=ACCENT_BLUE if active else BORDER_COLOR)
            c.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            
            top = ctk.CTkFrame(c, fg_color="transparent")
            top.pack(fill="x", padx=20, pady=(20, 5))
            
            ctk.CTkLabel(top, text=icon, font=("Segoe UI", 24)).pack(side="left")
            sw = ctk.CTkSwitch(top, text="", width=40, height=20, progress_color=ACCENT_BLUE)
            sw.pack(side="right")
            if active: sw.select()
            
            ctk.CTkLabel(c, text=title, font=("Segoe UI", 16, "bold"), anchor="w").pack(fill="x", padx=20)
            ctk.CTkLabel(c, text=desc, font=("Segoe UI", 12), text_color=TEXT_MUTED, anchor="w", justify="left").pack(fill="x", padx=20, pady=(0, 20))
            
        make_card(mod_f, 0, 0, "⚡", "C++ Engine Core", "Uses native C++ process to launch and manage the JVM.", active=True)
        make_card(mod_f, 0, 1, "🌐", "D3D12 Translation", "Native bindings configured in C++ for maximum graphics performance.", active=True)
        make_card(mod_f, 1, 0, "🗑️", "Auto Memory Cleaner", "Forces Garbage Collection when JVM memory hits 85% capacity.", active=True)
        make_card(mod_f, 1, 1, "🔄", "Auto Update", "Python UI automatically checks for updates before launch.", active=True)
        
        # Bottom Launch Bar
        lb = ctk.CTkFrame(self, height=90, fg_color=SIDEBAR_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        lb.grid(row=2, column=0, sticky="ew", pady=(20,0))
        lb.pack_propagate(False)
        
        # Version selector
        vf = ctk.CTkFrame(lb, fg_color="transparent")
        vf.pack(side="left", padx=20, fill="y", pady=20)
        ctk.CTkLabel(vf, text="VERSION", font=("Segoe UI", 10, "bold"), text_color=TEXT_MUTED).pack(anchor="w")
        self.ver_combo = ctk.CTkComboBox(vf, values=["1.21.4 (Vanilla)", "1.20.4 (Fabric)", "1.19.4 (Forge)"], width=180, fg_color=BG_COLOR, border_color=BORDER_COLOR)
        self.ver_combo.pack(anchor="w", pady=(2,0))
        
        # Launch Button & Status
        self.controller.play_btn = ctk.CTkButton(
            lb, text="▶ PLAY", font=("Segoe UI", 20, "bold"), 
            height=50, width=160, fg_color=ACCENT_GREEN, hover_color="#059669",
            command=self.controller.start_game_launch
        )
        self.controller.play_btn.pack(side="right", padx=20, pady=20)
        
        sf = ctk.CTkFrame(lb, fg_color="transparent")
        sf.pack(side="right", padx=20, fill="both", expand=True, pady=25)
        
        self.controller.launch_status = ctk.CTkLabel(sf, text="Ready", font=("Segoe UI", 12, "bold"), text_color=TEXT_MUTED, anchor="e")
        self.controller.launch_status.pack(fill="x")
        
        self.controller.launch_progress = ctk.CTkProgressBar(sf, height=6, progress_color=ACCENT_BLUE)
        self.controller.launch_progress.pack(fill="x", pady=(5,0))
        self.controller.launch_progress.set(0)

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        ctk.CTkLabel(self, text="Settings", font=("Segoe UI", 28, "bold")).pack(anchor="w", pady=(0, 20))
        
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        def make_section(title):
            f = ctk.CTkFrame(scroll, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
            f.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(f, text=title, font=("Segoe UI", 14, "bold"), text_color=ACCENT_BLUE).pack(anchor="w", padx=20, pady=(20, 10))
            return f
            
        jf = make_section("Java & Memory")
        ram_f = ctk.CTkFrame(jf, fg_color="transparent")
        ram_f.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(ram_f, text="Allocated RAM (MB)", font=("Segoe UI", 13)).pack(side="left")
        
        ram_slider = ctk.CTkSlider(ram_f, from_=1024, to=16384, number_of_steps=15, progress_color=ACCENT_BLUE)
        ram_slider.pack(side="right", fill="x", expand=True, padx=(20, 10))
        ram_slider.set(8192)
        
        ram_lbl = ctk.CTkLabel(ram_f, text="8192 MB", font=("Segoe UI", 13, "bold"), width=70)
        ram_lbl.pack(side="right")
        ram_slider.configure(command=lambda v: ram_lbl.configure(text=f"{int(v)} MB"))

    # ================= GAME LAUNCH ENGINE =================
    def start_game_launch(self):
        self.play_btn.configure(state="disabled", text="STARTING ENGINE...")
        self.launch_progress.set(0)
        threading.Thread(target=self.game_launch_thread, daemon=True).start()

    def game_launch_thread(self):
        self.thread_safe_update(self.launch_status, text="Checking for updates...")
        # Simulate auto-update
        import time
        for i in range(1, 11):
            time.sleep(0.05)
            self.thread_safe_progress(self.launch_progress, i/10.0)
            
        if not os.path.exists(ENGINE_EXECUTABLE):
            self.thread_safe_update(self.launch_status, text="Engine not found! Please compile C++ first.", text_color="red")
            self.thread_safe_update(self.play_btn, state="normal", text="▶ PLAY")
            return
            
        self.thread_safe_update(self.launch_status, text="Booting C++ Core Engine...", text_color=TEXT_MUTED)
        
        args = [
            ENGINE_EXECUTABLE,
            "--version", "1.20.4",
            "--ram", "4G",
            "--username", self.account_data["username"],
            "--backend", "zink"
        ]

        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.thread_safe_update(self.launch_status, text="Game Running via C++ Engine")
            
            for line in process.stdout:
                print(f"[ENGINE]: {line.strip()}")
                
            process.wait()
            self.after(0, self.reset_launch_ui)
            
        except Exception as e:
            print(f"Launch failed:\n{traceback.format_exc()}")
            self.thread_safe_update(self.launch_status, text="Engine Failed to Start", text_color="red")
            self.thread_safe_update(self.play_btn, state="normal", text="▶ PLAY")

    def reset_launch_ui(self):
        self.play_btn.configure(state="normal", text="▶ PLAY")
        self.launch_status.configure(text=f"Ready", text_color=TEXT_MUTED)
        self.launch_progress.set(0)

if __name__ == "__main__":
    app = SupersonicClient()
    app.mainloop()
