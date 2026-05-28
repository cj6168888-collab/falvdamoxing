"""
构建 Windows 桌面客户端安装包
- 客户端只负责连接服务器，大模型在服务器上运行
- 最终输出: LegalAI-Setup-v2.1.0.exe (~8MB)
"""
import os, sys, shutil, subprocess
from pathlib import Path

ROOT = Path(r"D:\重要\www\www\法律大模型")
CLIENT = ROOT / "client"

os.chdir(str(CLIENT))
print("=" * 50)
print("法律大模型 - Windows 安装包构建")
print("客户端模式: 连接服务器, 大模型在服务端")
print("=" * 50)

# Clean
print("\n[1/3] 清理...")
for d in [CLIENT / "dist-exe", CLIENT / "build", CLIENT / "dist-installer", CLIENT / "app", CLIENT / "dist"]:
    if d.exists():
        shutil.rmtree(d)
for f in CLIENT.glob("*.spec"):
    f.unlink()

# PyInstaller onefile
print("[2/3] 打包 EXE...")
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--name", "法律大模型",
    "--icon", str(CLIENT / "legal-ai.ico"),
    "--hidden-import", "webview",
    "--noconsole",
    "--clean",
    str(CLIENT / "run_client.py"),
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
if result.returncode != 0:
    print("PyInstaller failed:", result.stderr[-500:])
    sys.exit(1)

exe_src = CLIENT / "dist" / "法律大模型.exe"
exe_dst = CLIENT / "dist-exe" / "法律大模型.exe"
exe_dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy(exe_src, exe_dst)
size_mb = exe_dst.stat().st_size / 1024 / 1024
print(f"   EXE: {size_mb:.1f} MB")

# Inno Setup
print("[3/3] 构建安装包...")
iss = CLIENT / "setup.iss"
iss_text = r'''
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

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "其他:"; Flags: checkedonce

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
'''
iss.write_text(iss_text, encoding="utf-8")

iscc = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
result = subprocess.run([iscc, str(iss)], capture_output=True, text=True, timeout=120)
print(result.stdout.strip().split("\n")[-1] if result.stdout else "")
if result.returncode != 0:
    print(result.stderr[-300:])
    sys.exit(1)

setup = CLIENT / "dist-installer" / "LegalAI-Setup-v2.1.0.exe"
print(f"\nDone: {setup}")
print(f"Size: {setup.stat().st_size / 1024 / 1024:.1f} MB")
