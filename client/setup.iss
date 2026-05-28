; 法律大模型 — Windows 安装包
; 使用 Inno Setup 6 编译
; 下载: https://jrsoftware.org/isinfo.php

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
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.\dist-installer
OutputBaseFilename=LegalAI-Setup-v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
WizardImageFile=.\installer-bg.bmp
WizardSmallImageFile=.\installer-icon.bmp
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\legal-ai.ico
SetupIconFile=.\legal-ai.ico

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "其他:"; Flags: checkedonce

[Files]
; 主程序
Source: ".\dist-exe\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Python 运行时 (嵌入版)
Source: ".\python-embed\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs
; 应用代码
Source: "..\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs
; 前端
Source: "..\frontend\dist\*"; DestDir: "{app}\client\dist"; Flags: ignoreversion recursesubdirs
; 启动器
Source: ".\run_client.py"; DestDir: "{app}\client"; Flags: ignoreversion
Source: ".\app_client.py"; DestDir: "{app}\client"; Flags: ignoreversion
; 依赖
Source: ".\requirements-client.txt"; DestDir: "{app}"; Flags: ignoreversion
; 图标
Source: ".\legal-ai.ico"; DestDir: "{app}"; Flags: ignoreversion
; 配置文件
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: ignoreversion

[Dirs]
Name: "{app}\data"
Name: "{app}\data\files"
Name: "{app}\logs"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/f /im {#MyAppExeName}"; Flags: runhidden

[Code]
function InitializeSetup: Boolean;
begin
  Result := True;
end;
