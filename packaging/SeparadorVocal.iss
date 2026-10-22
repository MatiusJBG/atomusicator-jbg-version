#define AppName "Separador Vocal"
#define AppVersion "0.4.0"
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
Source: "..\build\ffmpeg-runtime\LICENSE"; DestDir: "{app}\docs\ffmpeg"; Flags: ignoreversion
Source: "..\build\ffmpeg-runtime\README.txt"; DestDir: "{app}\docs\ffmpeg"; Flags: ignoreversion
Source: "..\build\ffmpeg-runtime\runtime-manifest.json"; DestDir: "{app}\docs\ffmpeg"; Flags: ignoreversion

[Icons]
Name: "{group}\Separador Vocal"; Filename: "{app}\SeparadorVocal.exe"
Name: "{autodesktop}\Separador Vocal"; Filename: "{app}\SeparadorVocal.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SeparadorVocal.exe"; Description: "Iniciar Separador Vocal"; Flags: postinstall nowait skipifsilent

[Code]
function IsDriveRoot(Directory: String): Boolean;
var
  NormalizedDirectory: String;
begin
  NormalizedDirectory := RemoveBackslashUnlessRoot(ExpandFileName(Directory));
  Result := CompareText(NormalizedDirectory, ExtractFileDrive(NormalizedDirectory) + '\') = 0;
end;

function InitializeSetup(): Boolean;
var
  RequestedDirectory: String;
begin
  Result := True;
  RequestedDirectory := ExpandConstant('{param:DIR|}');
  if (RequestedDirectory <> '') and IsDriveRoot(RequestedDirectory) then
  begin
    MsgBox('No se puede instalar en la raíz de una unidad. Elige una subcarpeta, por ejemplo Archivos de programa.', mbError, MB_OK);
    Result := False;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    if IsDriveRoot(WizardDirValue) then
    begin
      MsgBox('Instala Separador Vocal en una subcarpeta, no en la raíz de la unidad. El destino predeterminado es Archivos de programa y requiere permisos de administrador.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;
