# Nexra Cloud Deployment Guide

This guide deploys Nexra to an Ubuntu cloud server with:

- `nginx` serving the frontend
- `systemd` managing the Spring Boot backend
- `H2` file database stored on the server
- optional HTTPS via `certbot`

## What Database Is Used

The current deployment uses `H2` file storage.

- Database file: `/opt/nexra/data/nexra-db.mv.db`
- Imported skill source file: `/opt/nexra/data/skills.json`
- Runtime Spring config: `/opt/nexra/config/application-cloud.properties`

## Server Requirements

- Ubuntu 22.04 or 24.04
- 2 vCPU or above
- 4 GB RAM recommended
- one public IP
- a domain name if you want public access by domain

## 1. Upload The Project To The Server

You can use `git clone` or upload the folder directly.

Example with git:

```bash
ssh ubuntu@YOUR_SERVER_IP
cd /opt
git clone YOUR_REPO_URL nexra-src
cd nexra-src
```

If you are copying from local Windows:

```bash
scp -r C:/Workspace/nexra ubuntu@YOUR_SERVER_IP:/opt/nexra-src
```

## 2. Point Your Domain To The Server

In your domain provider DNS panel, create an `A` record:

- host: `@`
- value: `YOUR_SERVER_IP`

If you want a subdomain such as `nexra.example.com`, create:

- host: `nexra`
- value: `YOUR_SERVER_IP`

Wait until DNS is resolved before enabling HTTPS.

## 3. Run The One-Click Deploy Script

SSH into the server and run:

```bash
cd /opt/nexra-src
sudo DOMAIN=nexra.example.com bash ./deploy-cloud.sh
```

If you do not have a domain yet, you can still deploy by IP:

```bash
cd /opt/nexra-src
sudo bash ./deploy-cloud.sh
```

## 4. What The Script Does

The script:

- installs `OpenJDK 17`, `Maven`, `nginx`, `curl`, and `rsync`
- compiles the backend
- copies backend runtime files into `/opt/nexra`
- copies frontend static files into `/var/www/nexra`
- writes `/etc/systemd/system/nexra-backend.service`
- writes `/etc/nginx/sites-available/nexra`
- enables and starts `nexra-backend` and `nginx`

## 5. Optional HTTPS

After DNS is ready, run:

```bash
cd /opt/nexra-src
sudo DOMAIN=nexra.example.com ENABLE_HTTPS=true CERTBOT_EMAIL=you@example.com bash ./deploy-cloud.sh
```

That will install `certbot` and ask nginx to serve HTTPS with redirect.

## 6. Service Management

Check backend:

```bash
sudo systemctl status nexra-backend
```

Restart backend:

```bash
sudo systemctl restart nexra-backend
```

Check nginx:

```bash
sudo systemctl status nginx
```

Restart nginx:

```bash
sudo systemctl restart nginx
```

View backend logs:

```bash
sudo tail -f /opt/nexra/logs/backend.log
sudo tail -f /opt/nexra/logs/backend-error.log
```

## 7. Verify The Deployment

Backend from server:

```bash
curl http://127.0.0.1:8080/api/dashboard
```

Public site:

- `http://nexra.example.com`
- or your server IP if no domain is configured

## 8. Deploy Updated Code

When you update the project:

```bash
cd /opt/nexra-src
git pull
sudo DOMAIN=nexra.example.com bash ./deploy-cloud.sh
```

## 9. Important Paths

- source repo on server: `/opt/nexra-src`
- deployed backend runtime: `/opt/nexra/backend`
- deployed backend config: `/opt/nexra/config/application-cloud.properties`
- deployed backend database: `/opt/nexra/data/nexra-db.mv.db`
- deployed frontend files: `/var/www/nexra`
- backend systemd unit: `/etc/systemd/system/nexra-backend.service`
- nginx site config: `/etc/nginx/sites-available/nexra`

## 10. Notes

- The frontend now uses the current domain's `/api` path automatically in cloud deployment.
- You do not need a separate frontend service on the server because `nginx` serves the static files directly.
- The backend still runs as a standalone Java process managed by `systemd`.
