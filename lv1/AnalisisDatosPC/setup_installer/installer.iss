[Setup]
AppName=Activity Tracker
AppVersion=1.0
DefaultDirName={pf}\ActivityTracker
DefaultGroupName=ActivityTracker
UninstallDisplayIcon={app}\ActivityTracker.exe
OutputDir=.
OutputBaseFilename=ActivityTrackerSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\dist\ActivityTracker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Activity Tracker"; Filename: "{app}\ActivityTracker.exe"
Name: "{userstartup}\Activity Tracker"; Filename: "{app}\ActivityTracker.exe"; Tasks: autostart

[Tasks]
Name: autostart; Description: "Run Activity Tracker at Windows startup"; GroupDescription: "Startup options:"; Flags: unchecked
