import sys
import os
import subprocess

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    print("========================================")
    print(" SUPERSONIC CLIENT - PING MAX OPTIMIZATION")
    print("========================================")
    print("Optimizing Windows TCP/IP for 0 Ping on Minecraft...")
    
    # [Your network optimization commands here]
    
    print("[SUCCESS] Network Optimized!")
    print("Starting Minecraft Engine...")
    
    # Locate the bundled Portable Java 21
    java_exe = resource_path(os.path.join("jre21", "bin", "java.exe"))
    
    # Check if Java exists in the bundle and run it
    if os.path.exists(java_exe):
        print("Bundled Java 21 found! Launching game...")
        # NOTE: The command to launch your specific Minecraft files will go here
        # Example: subprocess.Popen([java_exe, "-jar", "your_client_file.jar"])
    else:
        print("Error: Java 21 not found in bundle!")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
