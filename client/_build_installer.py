"""构建真正的 Windows 安装包"""
import os, sys, shutil, subprocess
from pathlib import Path

ROOT = Path(r"D:\重要\www\www\法律大模型")
CLIENT = ROOT / "client"

os.chdir(str(CLIENT))
print("=" * 50)
print("法律大模型 - Windows 安装包构建")
print("=" * 50)

# Step 1: Clean
print("\n[1/4] 清理...")
for d in [CLIENT / "dist-exe", CLIENT / "build", CLIENT / "dist-installer", CLIENT / "__pycache__"]:
    if d.exists(): shutil.rmtree(d)
for f in CLIENT.glob("*.spec"):
    f.unlink()

# Step 2: Copy files
print("[2/4] 准备文件...")
client_dist = CLIENT / "dist"
if client_dist.exists(): shutil.rmtree(client_dist)
shutil.copytree(ROOT / "frontend" / "dist", client_dist)
client_app = CLIENT / "app"
if client_app.exists(): shutil.rmtree(client_app)
shutil.copytree(ROOT / "app", client_app)
shutil.copy(ROOT / ".env.example", CLIENT / ".env")
(CLIENT / "data" / "files").mkdir(parents=True, exist_ok=True)

# Step 3: PyInstaller --onefile
print("[3/4] PyInstaller 打包 (onefile)...")
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--name", "LegalAI",
    "--icon", str(CLIENT / "legal-ai.ico"),
    "--add-data", f"{client_dist}{os.pathsep}client/dist",
    "--add-data", f"{client_app}{os.pathsep}app",
    "--add-data", f"{CLIENT / '.env'}{os.pathsep}.",
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "fastapi",
    "--hidden-import", "sqlalchemy",
    "--hidden-import", "pydantic",
    "--hidden-import", "webview",
    "--hidden-import", "multipart",
    "--hidden-import", "aiofiles",
    "--hidden-import", "jinja2",
    "--noconsole",
    "--clean",
    str(CLIENT / "run_client.py"),
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
if result.returncode != 0:
    print("PyInstaller failed:", result.stderr[-500:])
    sys.exit(1)
print("   PyInstaller OK")

# Copy EXE
exe_src = CLIENT / "dist" / "LegalAI.exe"
exe_dst = CLIENT / "dist-exe" / "LegalAI.exe"
exe_dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy(exe_src, exe_dst)
size = exe_dst.stat().st_size / 1024 / 1024
print(f"   EXE: {size:.1f} MB")

# Step 4: Inno Setup
print("[4/4] Inno Setup 安装包...")
# Simplify setup.iss for onefile mode
iss = CLIENT / "setup_simple.iss"
iss_content = '''
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
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=.\\dist-installer
OutputBaseFilename=LegalAI-Setup-v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\\{#MyAppExeName}
SetupIconFile=.\\legal-ai.ico

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "其他:"; Flags: checkedonce

[Files]
Source: ".\\dist-exe\\LegalAI.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\\legal-ai.ico"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\\data"
Name: "{app}\\data\\files"

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autoprograms}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/f /im LegalAI.exe"; Flags: runhidden
'''
iss.write_text(iss_content, encoding="utf-8")

iscc = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
result = subprocess.run([iscc, str(iss)], capture_output=True, text=True, timeout=120)
print(result.stdout[-500:] if result.stdout else "")
if result.returncode != 0:
    print("STDERR:", result.stderr[-300:])
    sys.exit(1)

# Output
setup = CLIENT / "dist-installer" / "LegalAI-Setup-v2.1.0.exe"
if setup.exists():
    size = setup.stat().st_size / 1024 / 1024
    print(f"\nDone! {setup}")
    print(f"Size: {size:.1f} MB")
else:
    print("Setup not found!")
