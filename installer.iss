#define MyAppName "KickMonitor"
; Si la variable no viene desde el comando (fallback), usar valor por defecto:
#ifndef MyAppVersion
  #define MyAppVersion "2.5.1"
#endif

#define MyAppPublisher "TheAndro2K"
#define MyAppExeName "KickMonitor.exe"

[Setup]
AppId={{3E28ED4F-E3D1-466D-8140-E080992D5092}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
CloseApplications=yes
RestartApplications=no

; Configuración de Salida
OutputDir=installer
OutputBaseFilename=KickMonitor_Setup_v{#MyAppVersion}
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; Permisos de Administrador
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

; --- PERSONALIZACIÓN VISUAL (Opcional) ---
WizardImageFile=assets\install_bg.png
WizardSmallImageFile=assets\install_small.png
WizardImageStretch=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Cambio: IconFilename apunta al EXE en lugar del archivo .ico
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; --- LIMPIEZA AL DESINSTALAR (NUEVO) ---
; Esto asegura que si borran la app, también se borre la base de datos de AppData
[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\{#MyAppName}"