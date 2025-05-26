; Inno Setup Script for OpenSuperWhisper

#define MyAppName "OpenSuperWhisper"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "OpenSuperWhisper"
#define MyAppURL "https://github.com/jsjones80/OpenSuperWhisper"
#define MyAppExeName "OpenSuperWhisper.exe"
#define MyAppDescription "Real-time Speech Transcription for Windows"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{A8E5F3C2-9A7B-4D6E-8F1C-2B3A4D5E6F7A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; License and info files
LicenseFile=LICENSE
InfoBeforeFile=README.md
; Output settings
OutputDir=installer_output
OutputBaseFilename=OpenSuperWhisper_Setup_{#MyAppVersion}_x64
; Icon
SetupIconFile=opensuperwhisper.ico
; Compression
Compression=lzma2/max
SolidCompression=yes
; Architecture
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; Privileges
PrivilegesRequired=admin
; Wizard
WizardStyle=modern
; Comment these out if you don't have the images
; WizardImageFile=installer_banner.bmp
; WizardSmallImageFile=installer_small.bmp
; Uninstall
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main application files (exclude recordings directory and database file)
Source: "dist\OpenSuperWhisper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "recordings,recordings.db"
; Additional files
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Dirs]
; Create user data directory in AppData (this is where the app actually stores data)
Name: "{userappdata}\OpenSuperWhisper"; Permissions: users-full
Name: "{userappdata}\OpenSuperWhisper\recordings"; Permissions: users-full

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppDescription}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "{#MyAppDescription}"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Launch application after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up data files on uninstall (only clean up user data if user confirms)
Type: filesandordirs; Name: "{userappdata}\OpenSuperWhisper"

[Registry]
; File associations (optional - for audio files)
Root: HKCR; Subkey: ".wav\OpenSuperWhisper"; ValueType: string; ValueName: ""; ValueData: "Transcribe with {#MyAppName}"; Flags: uninsdeletekey
Root: HKCR; Subkey: ".mp3\OpenSuperWhisper"; ValueType: string; ValueName: ""; ValueData: "Transcribe with {#MyAppName}"; Flags: uninsdeletekey
Root: HKCR; Subkey: ".m4a\OpenSuperWhisper"; ValueType: string; ValueName: ""; ValueData: "Transcribe with {#MyAppName}"; Flags: uninsdeletekey

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;

  // Check for .NET Framework or Visual C++ Redistributables if needed
  // This is a placeholder - add actual checks if required
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Post-installation tasks
    // For example, creating default config files
  end;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;

  // Check if application is running
  if FindWindowByClassName('Qt5QWindowIcon') <> 0 then
  begin
    MsgBox('Please close OpenSuperWhisper before uninstalling.', mbError, MB_OK);
    Result := False;
  end;
end;