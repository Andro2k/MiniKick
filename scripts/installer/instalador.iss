; Script de Inno Setup profesional para MiniKick

#define MyAppName "MiniKick"
#define MyAppVersion "1.6.8"
#define MyAppPublisher "Andro2k"
#define MyAppURL "https://github.com/Andro2k/MiniKick"
#define MyAppExeName "MiniKick.exe"
#define MyAppCopyright "Copyright (C) 2026 Andro2k"

[Setup]
AppId={{0B90FD30-82D2-4660-AA96-BBCF1ED53312}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright={#MyAppCopyright}

DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\Output
OutputBaseFilename=MiniKick_Installer_v{#MyAppVersion}
SetupIconFile=..\..\assets\icons\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

LicenseFile=..\..\license.txt
CloseApplications=force
WizardImageFile=install_bg.png
WizardSmallImageFile=install_small.png

VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoCopyright={#MyAppCopyright}
VersionInfoProductVersion={#MyAppVersion}.0

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[InstallDelete]
Type: filesandordirs; Name: "{app}\docs"
Type: filesandordirs; Name: "{app}\_internal\docs"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\MiniKick\*"; DestDir: "{app}"; Excludes: "\docs\*,\_internal\docs\*"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall

[UninstallDelete]
Type: files; Name: "{app}\.install_lang"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  LangCode: String;
begin
  if CurStep = ssPostInstall then
  begin
    LangCode := ActiveLanguage;
    if LangCode = 'spanish' then
      SaveStringToFile(ExpandConstant('{app}\.install_lang'), 'es', False)
    else
      SaveStringToFile(ExpandConstant('{app}\.install_lang'), 'en', False);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    DeleteFile(ExpandConstant('{app}\.install_lang'));
  end;
end;
