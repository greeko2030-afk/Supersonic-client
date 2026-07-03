[Setup]
AppName=Supersonic Client
AppVersion=1.0.0
DefaultDirName={autopf}\Supersonic Client
DefaultGroupName=Supersonic Client
UninstallDisplayIcon={app}\Supersonic-Client-Full.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer_output
OutputBaseFilename=Supersonic-Client-Installer

[Files]
Source: "dist\Supersonic-Client-Full.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Supersonic Client"; Filename: "{app}\Supersonic-Client-Full.exe"
Name: "{autodesktop}\Supersonic Client"; Filename: "{app}\Supersonic-Client-Full.exe"
