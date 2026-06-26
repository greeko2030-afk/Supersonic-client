import sys
import os
import subprocess
import minecraft_launcher_lib

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    print("========================================")
    print(" SUPERSONIC CLIENT - D3D12 OPTIMIZED")
    print("========================================")
    
    print("Optimizing Network and Graphics...")
    # Direct3D / Graphics Environment Variables
    os.environ["__GL_THREADED_OPTIMIZATIONS"] = "1"
    
    # Locate the bundled Java 21 folder
    java_exe = resource_path(os.path.join("jre21", "bin", "java.exe"))
    if not os.path.exists(java_exe):
        print("Error: Bundled Java 21 not found!")
        input("Press Enter to exit...")
        return

    # Set the user's default Minecraft directory
    minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
    
    # Get username input so the user can play with their own name
    username = input("\nEnter your Minecraft Username (e.g. Player123): ")
    if not username:
        username = "SupersonicUser"

    # Set the game version
    version = "1.20.4"
    
    print(f"\nChecking local files for Minecraft {version}...")
    print("If files are missing, they will be downloaded automatically.")
    print("Please do not close this window. This may take a few minutes depending on your internet speed...\n")

    # Callback functions to show download progress in the console
    def print_status(status_text):
        print(f"Downloading: {status_text}")
        
    def print_progress(progress):
        pass # Ignored to prevent console spam
        
    def print_max(max_progress):
        pass # Ignored to prevent console spam

    callback_dict = {
        "setStatus": print_status,
        "setProgress": print_progress,
        "setMax": print_max
    }

    try:
        # This will install/download the game if it doesn't exist
        minecraft_launcher_lib.install.install_minecraft_version(version, minecraft_directory, callback=callback_dict)
        print("\n[SUCCESS] All Minecraft files are ready!")
    except Exception as e:
        print(f"\nError downloading game files: {e}")
        input("Press Enter to exit...")
        return

    # JVM Arguments for Direct3D and performance boost
    options = {
        "username": username,
        "uuid": "",
        "token": "",
        "executablePath": java_exe,
        "jvmArguments": [
            "-Xmx4G",                     # Allocate 4GB RAM for the game
            "-XX:+UseZGC",                # ZGC garbage collector to reduce lag spikes
            "-Dsun.java2d.d3d=true",      # Enable Windows Direct3D (D3D)
            "-Dsun.java2d.opengl=false",  # Disable default OpenGL to prioritize D3D
        ]
    }

    try:
        # Generate the command to run Minecraft
        command = minecraft_launcher_lib.command.get_minecraft_command(version, minecraft_directory, options)
        
        print(f"\nStarting Game as {username}... Please wait!")
        
        # Launch Minecraft using the generated command
        subprocess.run(command)
        
    except Exception as e:
        print(f"Error launching game: {e}")
        
    input("\nGame closed. Press Enter to exit...")

if __name__ == "__main__":
    main()
