#define AppName "Separador Vocal"
#define AppVersion "0.3.2"
#define AppPublisher "Atomusicator JBG"

[Setup]
AppId={{6F4D832A-8CE9-4AA5-9E73-D3E94B9B0F48}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Separador Vocal
DefaultGroupName={#AppName}
OutputDir=..\dist
OutputBaseFilename=SeparadorVocal-Setup
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\SeparadorVocal.exe
PrivilegesRequired=admin
SetupLogging=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "..\dist\SeparadorVocal.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\third-party-notices.md"; DestDir: "{app}\docs"; Flags: ignoreversion

[Icons]
Name: "{group}\Separador Vocal"; Filename: "{app}\SeparadorVocal.exe"
Name: "{autodesktop}\Separador Vocal"; Filename: "{app}\SeparadorVocal.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SeparadorVocal.exe"; Description: "Iniciar Separador Vocal"; Flags: postinstall nowait skipifsilent
