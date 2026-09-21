; -----------------------------------------------------------------------------
; CleanGuard Professional — Official Inno Setup Installer Script
; Multi-lingual (Uzbek, Russian, English) Modern Windows Setup Package
; Target OS: Windows 7 SP1, Windows 8, 8.1, Windows 10, Windows 11 (x86/x64)
; -----------------------------------------------------------------------------

#define MyAppName "CleanGuard"
#define MyAppDisplayName "CleanGuard Professional"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "CleanGuard Team"
#define MyAppURL "https://github.com/Valijon21/cleaner_win"
#define MyAppExeName "CleanGuard.exe"

[Setup]
; Unique application GUID for updates and clean uninstallation
AppId={{A35B9B7E-7F8C-4D2A-98C3-5F1B9C7E2D10}}
AppName={#MyAppDisplayName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppDisplayName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppDisplayName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir=..\dist\installer
OutputBaseFilename=CleanGuard_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\cleanguard.ico
UninstallDisplayIcon={app}\assets\cleanguard.ico
UninstallDisplayName={#MyAppDisplayName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes
RestartApplications=no
MinVersion=6.1sp1

[Languages]
Name: "uzbek"; MessagesFile: "compiler:Default.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
; --- Uzbek Messages ---
uzbek.CreateDesktopIcon=Ish stolida yorliq yaratish
uzbek.AutoCareStartup=Windows bilan birga avtomatik rejalashtirish xizmatini yoqish
uzbek.LaunchProgram={#MyAppDisplayName} dasturini ishga tushirish
uzbek.AdditionalIcons=Qo'shimcha sozlamalar:
uzbek.CleanUserDataPrompt=CleanGuard tozalash tarixi va jurnallarini ham o'chirishni xohlaysizmi?

; --- English Messages ---
english.CreateDesktopIcon=Create a desktop shortcut
english.AutoCareStartup=Enable automatic scheduled care with Windows
english.LaunchProgram=Launch {#MyAppDisplayName}
english.AdditionalIcons=Additional shortcuts:
english.CleanUserDataPrompt=Do you also want to remove CleanGuard cleanup history and logs?

; --- Russian Messages ---
russian.CreateDesktopIcon=Создать ярлык на Рабочем столе
russian.AutoCareStartup=Включить авто-обслуживание при запуске Windows
russian.LaunchProgram=Запустить {#MyAppDisplayName}
russian.AdditionalIcons=Дополнительные параметры:
russian.CleanUserDataPrompt=Желаете также удалить историю очистки и журналы CleanGuard?

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Main Standalone Application
Source: "..\dist\CleanGuard.exe"; DestDir: "{app}"; Flags: ignoreversion
; Metadata and Brand Assets
Source: "..\assets\cleanguard.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\assets\cleanguard.png"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppDisplayName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\cleanguard.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppDisplayName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppDisplayName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\cleanguard.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\CleanGuard\logs"
Type: files; Name: "{localappdata}\CleanGuard\cleanguard.log*"

[Code]
// Optional clean removal of user database and config on uninstall
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    DataDir := ExpandConstant('{localappdata}\CleanGuard');
    if DirExists(DataDir) then
    begin
      if MsgBox(CustomMessage('CleanUserDataPrompt'), mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;
