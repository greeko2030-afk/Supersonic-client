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
    
    print("\n[SUCCESS] Systems Ready!")
    
    # Get username input so the user can play with their own name
    username = input("Enter your Minecraft Username (e.g. Player123): ")
    if not username:
        username = "SupersonicUser"

    # Set the game version (Change this to match your server/client version)
    version = "1.20.4"
    print(f"Loading Minecraft {version} Engine...")

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
        
        print(f"Starting Game as {username}... Please wait!")
        
        # Launch Minecraft using the generated command
        subprocess.run(command)
        
    except Exception as e:
        print(f"Error launching game: {e}")
        print("Make sure you have downloaded this version in your official launcher first!")
        
    input("\nGame closed. Press Enter to exit...")

if __name__ == "__main__":
    main()
