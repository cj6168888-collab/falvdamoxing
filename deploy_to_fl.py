#!/usr/bin/env python3
"""
法律大模型 — 一键部署到 数字员工 服务器
fl.jilinpc.com | 独立端口 | 不干扰已部署系统
"""
import os, sys, time, io, tarfile, paramiko
from pathlib import Path

SERVER_IP = "118.31.48.156"
SERVER_USER = "root"
SSH_KEY = r"C:\Users\Lenovo\.ssh\id_ed25519_jilin_aliyun_20260522"
PROJECT_DIR = Path(r"D:\重要\www\www\法律大模型")
REMOTE_DIR = "/opt/legal-ai"

# 需要上传的文件/目录
UPLOAD_ITEMS = [
    "Dockerfile.prod",
    "docker-compose.fl-prod.yml",
    ".env.fl-prod",
    "requirements.txt",
    "requirements-core.txt",
    "requirements-optional.txt",
    "requirements-worker.txt",
    "app",
    "scripts",
    "config",
    "migrations",
    "pytest.ini",
]

def ssh_connect():
    key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SERVER_IP, username=SERVER_USER, pkey=key, timeout=30)
    return client

def run(client, cmd, desc=""):
    if desc:
        print(f"  [{desc}]")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if err and "WARNING" not in err:
        print(f"  STDERR: {err[:200]}")
    return out

def upload_files(client):
    """打包并上传项目文件"""
    print("\n[1/5] 打包项目文件...")
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        for item in UPLOAD_ITEMS:
            src = PROJECT_DIR / item
            if src.exists():
                tar.add(src, arcname=item)
    tar_buffer.seek(0)
    size_mb = len(tar_buffer.getvalue()) / 1024 / 1024
    print(f"  打包完成: {size_mb:.1f}MB")

    print("[2/5] 上传到服务器...")
    sftp = client.open_sftp()
    run(client, f"mkdir -p {REMOTE_DIR}/data/config")
    sftp.putfo(tar_buffer, f"{REMOTE_DIR}/project.tar.gz")
    sftp.close()
    print("  上传完成")

def deploy(client):
    """启动 Docker 容器"""
    print("[3/5] 解压并启动...")
    run(client, f"cd {REMOTE_DIR} && tar xzf project.tar.gz --overwrite 2>/dev/null; cp docker-compose.fl-prod.yml docker-compose.yml 2>/dev/null; cp .env.fl-prod .env 2>/dev/null; echo OK")

    print("[4/5] Docker Compose 构建并启动...")
    out = run(client, f"cd {REMOTE_DIR} && docker compose -f docker-compose.fl-prod.yml build --quiet 2>&1 && docker compose -f docker-compose.fl-prod.yml up -d 2>&1")
    print(out[-500:] if len(out) > 500 else out)

    time.sleep(5)
    print("[5/5] 检查容器状态...")
    out = run(client, f"cd {REMOTE_DIR} && docker compose -f docker-compose.fl-prod.yml ps")
    print(out)

def setup_nginx(client):
    """配置 Nginx"""
    print("\n[Nginx] 配置域名 fl.jilinpc.com...")
    nginx_conf = (PROJECT_DIR / "config" / "nginx" / "fl.jilinpc.com.conf").read_text(encoding="utf-8")
    sftp = client.open_sftp()
    with sftp.file("/etc/nginx/conf.d/fl.jilinpc.com.conf", "w") as f:
        f.write(nginx_conf)
    sftp.close()
    out = run(client, "nginx -t 2>&1 && nginx -s reload 2>&1")
    print(out)

def init_db(client):
    """初始化数据库"""
    print("\n[DB] 运行迁移...")
    out = run(client, f"docker exec legal-ai-app python -m app.db.migrate_all 2>&1", "migrate_all")
    print(out[-300:] if len(out) > 300 else out)

    print("\n[Admin] 创建平台超管...")
    out = run(client, f'''docker exec legal-ai-app python -c "
from app.db.database import SessionLocal
from app.services.jwt_auth_service import jwt_auth_service
from app.models.user import User
db = SessionLocal()
result = jwt_auth_service.register_user(db=db, username='admin', email='admin@fl.jilinpc.com', password='admin123456', full_name='平台超管', tenant_name='法律大模型', tenant_type='law_firm', role='admin')
if result.get('success'):
    u = db.query(User).filter(User.username == 'admin').first()
    u.is_platform_admin = True
    db.commit()
    print('超管创建成功: admin / admin123456')
else:
    print('创建失败: ' + result.get('error',''))
db.close()
" 2>&1''', "create admin")
    print(out)

def main():
    print("=" * 60)
    print("法律大模型 — 部署到 数字员工 服务器")
    print(f"域名: fl.jilinpc.com")
    print(f"端口: 127.0.0.1:8089 (不干扰现有服务)")
    print("=" * 60)

    client = ssh_connect()
    try:
        upload_files(client)
        deploy(client)
        setup_nginx(client)
        init_db(client)
        print("\n" + "=" * 60)
        print("部署完成!")
        print(f"API 文档: http://fl.jilinpc.com/docs")
        print(f"API 健康: http://fl.jilinpc.com/health")
        print(f"超管账号: admin / admin123456")
        print("=" * 60)
    finally:
        client.close()

if __name__ == "__main__":
    main()
