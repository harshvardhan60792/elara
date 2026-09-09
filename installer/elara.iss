; Per-user Inno Setup script for Elara. No admin rights needed - installs
; under the current user's AppData, matching the "no admin prompt" QA item
; in docs/TESTING.md. Run scripts\build.ps1 first so dist\elara\ exists.

#define MyAppName "Elara"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Harshvardhan"
#define MyAppURL "https://github.com/harshvardhan60792/elara"
#define MyAppExeName "elara.exe"

[Setup]
AppId={{C1D8E6C4-6E76-4C9C-9E2A-9B1B7B2E7B4F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Per-user install - no admin prompt (docs/TESTING.md Setup checklist).
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=elara-{#MyAppVersion}-setup-win64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icon_armed.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\elara\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
// Uninstall genuinely *asks* before touching user data, rather than
// silently deleting it (or silently leaving it behind) - matches the
// "offers to remove settings" QA item in docs/TESTING.md.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  SettingsDir: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    SettingsDir := ExpandConstant('{localappdata}\Elara');
    if DirExists(SettingsDir) then
    begin
      if MsgBox('Also remove your Elara settings and models? This deletes ' + SettingsDir,
                mbConfirmation, MB_YESNO) = IDYES then
        DelTree(SettingsDir, True, True, True);
    end;
  end;
end;
