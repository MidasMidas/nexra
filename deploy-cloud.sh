#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-_}"
SOURCE_DIR="${SOURCE_DIR:-$(pwd)}"
APP_DIR="${APP_DIR:-/opt/nexra}"
WEB_DIR="${WEB_DIR:-/var/www/nexra}"
BACKEND_PORT="${BACKEND_PORT:-8080}"
ENABLE_HTTPS="${ENABLE_HTTPS:-false}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run this script as root: sudo bash deploy-cloud.sh"
  exit 1
fi

if [[ ! -f "${SOURCE_DIR}/backend/pom.xml" ]]; then
  echo "SOURCE_DIR does not look like the Nexra repo: ${SOURCE_DIR}"
  exit 1
fi

echo "Installing system packages..."
apt-get update
apt-get install -y openjdk-17-jre-headless maven nginx curl rsync

echo "Building backend..."
pushd "${SOURCE_DIR}/backend" >/dev/null
mvn -q -DskipTests compile
mvn -q dependency:copy-dependencies -DincludeScope=runtime -DoutputDirectory=target/dependency
popd >/dev/null

echo "Preparing directories..."
mkdir -p "${APP_DIR}/backend" "${APP_DIR}/config" "${APP_DIR}/data" "${APP_DIR}/logs" "${WEB_DIR}"

echo "Publishing backend runtime..."
rsync -a --delete "${SOURCE_DIR}/backend/target/classes/" "${APP_DIR}/backend/classes/"
rsync -a --delete "${SOURCE_DIR}/backend/target/dependency/" "${APP_DIR}/backend/dependency/"
cp "${SOURCE_DIR}/backend/src/main/resources/data/skills.json" "${APP_DIR}/data/skills.json"

echo "Publishing frontend..."
rsync -a --delete \
  --exclude "__pycache__" \
  --exclude "server.py" \
  "${SOURCE_DIR}/frontend/" "${WEB_DIR}/"

cat > "${APP_DIR}/config/application-cloud.properties" <<EOF
server.port=${BACKEND_PORT}
nexra.skills.data-file=${APP_DIR}/data/skills.json
spring.datasource.url=jdbc:h2:file:${APP_DIR}/data/nexra-db;DB_CLOSE_ON_EXIT=FALSE;FILE_LOCK=NO
spring.datasource.driver-class-name=org.h2.Driver
spring.datasource.username=sa
spring.datasource.password=
spring.jpa.hibernate.ddl-auto=update
spring.jpa.open-in-view=false
spring.jpa.database-platform=org.hibernate.dialect.H2Dialect
spring.h2.console.enabled=false
nexra.skill-sync.enabled=true
nexra.skill-sync.target-count=3000
nexra.skill-sync.initial-delay-ms=900000
nexra.skill-sync.fixed-delay-ms=43200000
EOF

cat > /etc/systemd/system/nexra-backend.service <<EOF
[Unit]
Description=Nexra Spring Boot Backend
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
ExecStart=/usr/bin/java -cp ${APP_DIR}/backend/classes:${APP_DIR}/backend/dependency/* com.nexra.console.NexraConsoleApplication --spring.config.additional-location=file:${APP_DIR}/config/application-cloud.properties
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
        proxy_pass http://127.0.0.1:${BACKEND_PORT}/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location = /api {
        proxy_pass http://127.0.0.1:${BACKEND_PORT}/api;
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
  if curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/dashboard" >/dev/null; then
    break
  fi
  sleep 2
done

echo
echo "Deployment complete."
echo "Backend service: systemctl status nexra-backend"
echo "Nginx service: systemctl status nginx"
echo "Backend health: http://127.0.0.1:${BACKEND_PORT}/api/dashboard"
if [[ "${DOMAIN}" == "_" ]]; then
  echo "Open the server IP in your browser."
else
  echo "Open: http://${DOMAIN}"
fi
