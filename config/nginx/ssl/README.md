# SSL 证书目录
#
# 请将以下文件放入此目录：
#
# - fullchain.pem    (SSL 证书 + 中间证书)
# - privkey.pem      (私钥)
#
# 获取 Let's Encrypt 免费证书：
#   certbot --nginx -d your-domain.com -d www.your-domain.com
#
# 或使用自签名证书（仅用于测试）：
#   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
#     -keyout privkey.pem -out fullchain.pem \
#     -subj "/C=CN/ST=Beijing/L=Beijing/O=LegalAI/CN=your-domain.com"

# 启用 HTTPS Nginx 配置：
#   docker compose -f docker-compose.prod.yml -f docker-compose.prod.https.yml up -d nginx

# 部署前预检：
#   powershell -ExecutionPolicy Bypass -File scripts\production-preflight.ps1 -RequireTls -RequireExternalApis
