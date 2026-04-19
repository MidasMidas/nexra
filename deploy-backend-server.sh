#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-api.nexracat.com}"
SOURCE_DIR="${SOURCE_DIR:-$(pwd)}"
APP_DIR="${APP_DIR:-/opt/nexra-backend}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8080}"
ENABLE_HTTPS="${ENABLE_HTTPS:-false}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"
SUPABASE_DATABASE_URL="${SUPABASE_DATABASE_URL:-}"
CORS_ALLOW_ORIGINS="${CORS_ALLOW_ORIGINS:-https://nexracat.com}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run this script as root: sudo bash deploy-backend-server.sh"
  exit 1
fi

if [[ ! -f "${SOURCE_DIR}/backend_py/server.py" ]]; then
  echo "SOURCE_DIR does not look like the Nexra Python backend repo: ${SOURCE_DIR}"
  exit 1
fi

if [[ -z "${SUPABASE_DATABASE_URL}" ]]; then
  echo "SUPABASE_DATABASE_URL is required."
  exit 1
fi

echo "Installing system packages..."
apt-get update
apt-get install -y python3 python3-venv nginx curl rsync

echo "Preparing directories..."
mkdir -p "${APP_DIR}/backend_py" "${APP_DIR}/data" "${APP_DIR}/logs"

echo "Publishing backend source..."
rsync -a --delete \
  --exclude "__pycache__" \
  --exclude "data" \
  "${SOURCE_DIR}/backend_py/" "${APP_DIR}/backend_py/"
cp "${SOURCE_DIR}/requirements.txt" "${APP_DIR}/requirements.txt"
cp "${SOURCE_DIR}/backend_py/data/skills.json" "${APP_DIR}/data/skills.json"

if [[ ! -d "${APP_DIR}/.venv" ]]; then
  python3 -m venv "${APP_DIR}/.venv"
fi

"${APP_DIR}/.venv/bin/pip" install --upgrade pip
"${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

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

cat > "${APP_DIR}/backend_py/database.private.json" <<EOF
{
  "DATABASE_URL": "${SUPABASE_DATABASE_URL}"
}
EOF

cat > /etc/systemd/system/nexra-backend.service <<EOF
[Unit]
Description=Nexra Python Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
Environment=NEXRA_STATE_BACKEND=postgres
Environment=NEXRA_CORS_ALLOW_ORIGINS=${CORS_ALLOW_ORIGINS}
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/backend_py/server.py
Restart=always
RestartSec=5
StandardOutput=append:${APP_DIR}/logs/backend.log
StandardError=append:${APP_DIR}/logs/backend-error.log

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/nginx/sites-available/nexra-backend <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://${BACKEND_HOST}:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/nexra-backend /etc/nginx/sites-enabled/nexra-backend
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl daemon-reload
systemctl enable --now nexra-backend
systemctl enable --now nginx
systemctl restart nginx

if [[ "${ENABLE_HTTPS}" == "true" ]]; then
  if [[ -z "${CERTBOT_EMAIL}" ]]; then
    echo "Skipping HTTPS setup because CERTBOT_EMAIL is missing."
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
echo "Backend deployment complete."
echo "Public API: https://${DOMAIN}/api"
echo "Local health: http://${BACKEND_HOST}:${BACKEND_PORT}/api/dashboard"
