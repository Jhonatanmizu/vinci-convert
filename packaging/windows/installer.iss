; Inno Setup installer for vinci-convert (Windows x86_64).
;
; Expects the PyInstaller one-dir builds at:
;   dist\vinci-convert\      (CLI)
;   dist\vinci-convert-gui\  (GUI)
;
; Build (version is injected by CI):
;   iscc /DAppVersion=0.1.0 packaging\windows\installer.iss

#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

#define AppName "Vinci Convert"
#define AppPublisher "jhonatanmizu"
#define AppURL "https://github.com/jhonatanmizu/vinci-convert"
#define AppId "{{B7E3A1C2-4F5D-4E6A-9C8B-2D1F0A3E5B77}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases

; Per-user install into %LOCALAPPDATA%\Programs — no UAC prompt.
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\Vinci Convert
DefaultGroupName={#AppName}

OutputDir=..\..\dist\installer
OutputBaseFilename=vinci-convert-{#AppVersion}-windows-x86_64-setup
SetupIconFile=..\assets\vinci-convert.ico
UninstallDisplayIcon={app}\gui\vinci-convert-gui.exe

Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesEnvironment=no
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\..\dist\vinci-convert-gui\*"; DestDir: "{app}\gui"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\dist\vinci-convert\*"; DestDir: "{app}\cli"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\gui\vinci-convert-gui.exe"; IconFilename: "{app}\gui\vinci-convert-gui.exe"
Name: "{group}\{#AppName} CLI"; Filename: "{cmd}"; Parameters: "/K set ""PATH={app}\cli;%PATH%"" && vinci-convert --help"; Comment: "Open a terminal with vinci-convert on PATH"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\gui\vinci-convert-gui.exe"; Tasks: desktopicon

[Registry]
; App Paths — makes the executables resolvable by name (Run dialog, shell).
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\vinci-convert-gui.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\gui\vinci-convert-gui.exe"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\vinci-convert-gui.exe"; ValueType: string; ValueName: "Path"; ValueData: "{app}\gui"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\vinci-convert.exe"; ValueType: string; ValueName: ""; ValueData: "{app}\cli\vinci-convert.exe"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\App Paths\vinci-convert.exe"; ValueType: string; ValueName: "Path"; ValueData: "{app}\cli"; Flags: uninsdeletekey

[Run]
Filename: "{app}\gui\vinci-convert-gui.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
