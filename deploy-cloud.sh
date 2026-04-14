#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-_}"
SOURCE_DIR="${SOURCE_DIR:-$(pwd)}"
APP_DIR="${APP_DIR:-/opt/nexra}"
WEB_DIR="${WEB_DIR:-/var/www/nexra}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8080}"
ENABLE_HTTPS="${ENABLE_HTTPS:-false}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run this script as root: sudo bash deploy-cloud.sh"
  exit 1
fi

if [[ ! -f "${SOURCE_DIR}/backend_py/server.py" ]]; then
  echo "SOURCE_DIR does not look like the Python Nexra repo: ${SOURCE_DIR}"
  exit 1
fi

echo "Installing system packages..."
apt-get update
apt-get install -y python3 nginx curl rsync

echo "Preparing directories..."
mkdir -p "${APP_DIR}/backend_py" "${APP_DIR}/data" "${APP_DIR}/logs" "${WEB_DIR}"

echo "Publishing Python backend..."
rsync -a --delete \
  --exclude "__pycache__" \
  --exclude "data" \
  "${SOURCE_DIR}/backend_py/" "${APP_DIR}/backend_py/"

echo "Publishing frontend..."
rsync -a --delete \
  --exclude "__pycache__" \
  --exclude "server.py" \
  "${SOURCE_DIR}/frontend/" "${WEB_DIR}/"

cp "${SOURCE_DIR}/backend/src/main/resources/data/skills.json" "${APP_DIR}/data/skills.json"

cat > "${APP_DIR}/backend_py/config.json" <<EOF
{
  "host": "${BACKEND_HOST}",
  "port": ${BACKEND_PORT},
  "databasePath": "${APP_DIR}/data/nexra-state.json",
  "skillDataFile": "${APP_DIR}/data/skills.json",
  "skillSync": {
    "enabled": true,
    "targetCount": 3000,
    "initialDelaySeconds": 900,
    "intervalSeconds": 43200
  }
}
EOF

cat > /etc/systemd/system/nexra-backend.service <<EOF
[Unit]
Description=Nexra Python Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/python3 ${APP_DIR}/backend_py/server.py
Restart=always
RestartSec=5
StandardOutput=append:${APP_DIR}/logs/backend.log
StandardError=append:${APP_DIR}/logs/backend-error.log

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/nginx/sites-available/nexra <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    root ${WEB_DIR};
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT}/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location = /api {
        proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT}/api;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/nexra /etc/nginx/sites-enabled/nexra
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl daemon-reload
systemctl enable --now nexra-backend
systemctl enable --now nginx
systemctl restart nginx

if [[ "${ENABLE_HTTPS}" == "true" ]]; then
  if [[ -z "${CERTBOT_EMAIL}" || "${DOMAIN}" == "_" ]]; then
    echo "Skipping HTTPS setup because CERTBOT_EMAIL or DOMAIN is missing."
  else
    apt-get install -y certbot python3-certbot-nginx
    certbot --nginx -d "${DOMAIN}" -m "${CERTBOT_EMAIL}" --agree-tos --redirect --non-interactive
  fi
fi

echo "Waiting for backend to answer..."
for _ in {1..20}; do
  if curl -fsS "http://${BACKEND_HOST}:${BACKEND_PORT}/api/dashboard" >/dev/null; then
    break
  fi
  sleep 2
done

echo
echo "Deployment complete."
echo "Backend service: systemctl status nexra-backend"
echo "Nginx service: systemctl status nginx"
echo "Backend health: http://${BACKEND_HOST}:${BACKEND_PORT}/api/dashboard"
if [[ "${DOMAIN}" == "_" ]]; then
  echo "Open the server IP in your browser."
else
  echo "Open: http://${DOMAIN}"
fi
