#define MyAppName "法律大模型"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "法律大模型团队"
#define MyAppURL "https://fl.jilinpc.com"
#define MyAppExeName "法律大模型.exe"

[Setup]
AppId={{A8F3C9E2-7B4D-4F1A-9E6C-2D5B8F0A1C3E}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.\dist-installer
OutputBaseFilename=LegalAI-Setup-v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=.\legal-ai.ico
PrivilegesRequiredOverridesAllowed=dialog
; 安装向导标题
AppComments=AI驱动的智能法律案件管理系统
AppContact=法律大模型团队

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.AppNameLabel=法律大模型 - AI案件指挥台
english.WelcomeLabel2=即将安装 [name] v{#MyAppVersion} 到您的电脑。
english.ClickNext=点击"Next"继续安装。

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式 (&D)"; GroupDescription: "其他:"; Flags: checkedonce

[Files]
Source: ".\dist-exe\法律大模型.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\legal-ai.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/f /im 法律大模型.exe"; Flags: runhidden
