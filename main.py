import sys
import os
import subprocess
import uuid
import threading
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
        self.status_label.pack(side="bottom", pady=20)

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

    def launch_game(self, username):
        try:
            # Graphics Environment Variables
            os.environ["__GL_THREADED_OPTIMIZATIONS"] = "1"
            
            java_exe = resource_path(os.path.join("jre21", "bin", "java.exe"))
            if not os.path.exists(java_exe):
                self.update_status("Error: Bundled Java 21 not found!")
                self.play_button.configure(state="normal")
                return

            minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
            version = "1.20.4"
            
            # Callbacks for download progress
            def print_status(status_text):
                self.update_status(f"Downloading: {status_text}")
                
            callback_dict = {
                "setStatus": print_status,
                "setProgress": lambda p: None,
                "setMax": lambda m: None
            }

            self.update_status(f"Checking files for {version}...")
            minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_directory, callback=callback_dict)
            
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
                    "-Dsun.java2d.d3d=true",
                    "-Dsun.java2d.opengl=false",
                ]
            }

            self.update_status("Launching Game... You can close this window.")
            command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directory, options)
            
            # Start game and close launcher
            subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
            self.destroy() # Closes the UI after the game starts
            
        except Exception as e:
            self.update_status(f"Error: {e}")
            self.play_button.configure(state="normal")

if __name__ == "__main__":
    app = SupersonicLauncher()
    app.mainloop()
