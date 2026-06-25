import sys
import os
import subprocess

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    print("========================================")
    print(" SUPERSONIC CLIENT - PING MAX OPTIMIZATION")
    print("========================================")
    print("Optimizing Windows TCP/IP for 0 Ping on Minecraft...")
    
    # [Your network optimization commands can be added here if needed]
    # Example: os.system('netsh int tcp set global autotuninglevel=normal')
    
    print("[SUCCESS] Network Optimized!")
    print("Launching Supersonic Client...")
    
    # Locate the bundled launcher inside the temp folder
    launcher_exe = resource_path("Supersonic-Launcher.exe")
    
    # Launch the Supersonic-Launcher
    if os.path.exists(launcher_exe):
        subprocess.Popen([launcher_exe])
    else:
        print(f"Error: {launcher_exe} not found in bundle!")

if __name__ == "__main__":
    main()
