[; Inno Setup Script for Supersonic Client
[Setup]
AppName=MinecraftD3D12Launcher
AppVersion=1.0.0
DefaultDirName={pf}\MinecraftD3D12Launcher
DefaultGroupName=MinecraftD3D12Launcher
OutputDir=installer_output
OutputBaseFilename=Supersonic-Client-Installer

[Files]
Source: "dist\Supersonic-Client-Full.exe"; DestDir: "{app}"; DestName: "Supersonic.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\MinecraftD3D12Launcher"; Filename: "{app}\Supersonic.exe"
Name: "{commondesktop}\MinecraftD3D12Launcher"; Filename: "{app}\Supersonic.exe"

[Run]
Filename: "{app}\Supersonic.exe"; Description: "Launch MinecraftD3D12Launcher"; Flags: nowait postinstall skipifsilent
