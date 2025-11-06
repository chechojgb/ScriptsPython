[Setup]
AppName=Activity Tracker
AppVersion=1.0
AppPublisher=Sergio Ortiz
AppPublisherURL=https://example.com
; Carpeta de instalación predeterminada (AppData del usuario)
DefaultDirName={userappdata}\ActivityTracker
; Ocultar todas las páginas del instalador
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=yes
DisableFinishedPage=yes
DisableWelcomePage=yes
; No permitir cambiar la carpeta de instalación
UninstallDisplayIcon={app}\ActivityTracker.exe
; Salida del instalador
OutputDir=.
OutputBaseFilename=ActivityTrackerSetup
Compression=lzma
SolidCompression=yes
; Evita mostrar la página de tareas o autostart
DisableStartupPrompt=yes
; No preguntar idioma ni permisos
ShowLanguageDialog=no

[Files]
Source: "..\dist\ActivityTracker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Activity Tracker"; Filename: "{app}\ActivityTracker.exe"
Name: "{userstartup}\Activity Tracker"; Filename: "{app}\ActivityTracker.exe"; Tasks: autostart

[Tasks]
Name: autostart; Description: "Run Activity Tracker at Windows startup"; GroupDescription: "Startup options:"; Flags: unchecked

[Run]
Filename: "{app}\ActivityTracker.exe"; Description: "Launch Activity Tracker"; Flags: nowait postinstall skipifsilent
