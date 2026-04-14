# Nexra Full-Stack MVP

Nexra is a separated full-stack MVP for AI skill search, rating, and recommendation.

## Structure

- [backend_py](C:\Workspace\nexra\backend_py): Python REST API
- [frontend](C:\Workspace\nexra\frontend): standalone HTML, CSS, and JS console
- [product-spec.md](C:\Workspace\nexra\docs\product-spec.md): product and platform spec
- [usage-guide.md](C:\Workspace\nexra\docs\usage-guide.md): run and usage guide
- [cloud-deployment.md](C:\Workspace\nexra\docs\cloud-deployment.md): Ubuntu cloud deployment guide

## Current Focus

This version does not do route forwarding or remote execution. Nexra helps agents find the right external skill, evaluate trust, and read provider guidance before calling the skill directly.

Key capabilities now include:

- User rating plus system rating on every skill
- Search and recommendation by skill function, category, name, and description
- Paginated skill list with configurable `page` and `pageSize`
- Skill detail pages with provider docs, auth notes, and call examples
- User identity model with normal users and admins
- User-submitted skills with admin approval flow
- Admin update/delete of skill ratings and detailed metadata
- Built-in scheduled skill sync that refreshes the local skill library from the local skill seed file

## Run Backend

```bash
cd backend_py
python server.py
```

Backend base URL:

- `http://localhost:8080/api`

## Run Frontend

```bash
cd frontend
python server.py
```

Frontend URL:

- `http://127.0.0.1:4173`

## One-Click Scripts

- [Start-Nexra.ps1](C:\Workspace\nexra\Start-Nexra.ps1)
- [Stop-Nexra.ps1](C:\Workspace\nexra\Stop-Nexra.ps1)
- [start-nexra.bat](C:\Workspace\nexra\start-nexra.bat)
- [stop-nexra.bat](C:\Workspace\nexra\stop-nexra.bat)
- [Configure-NexraDatabase.ps1](C:\Workspace\nexra\Configure-NexraDatabase.ps1)
- [deploy-cloud.sh](C:\Workspace\nexra\deploy-cloud.sh)

## Main API Endpoints

Public and user-facing:

- `GET /api`
- `GET /api/agent-guide`
- `GET /api/dashboard`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/skills?q=&function=&page=&pageSize=`
- `GET /api/skills/{id}`
- `POST /api/skills/{id}/reviews`
- `POST /api/skills/submissions`
- `GET /api/users`
- `GET /api/users/me`
- `GET /api/billing/summary`
- `GET /api/billing/transactions`
- `GET /api/keys`
- `POST /api/keys`

Admin-only:

- `GET /api/admin/skills/pending`
- `POST /api/admin/skills/{id}/approve`
- `PUT /api/admin/skills/{id}`
- `DELETE /api/admin/skills/{id}`
- `GET /api/admin/skills/sync/status`
- `POST /api/admin/skills/sync`

## Storage

The current Python backend persists runtime state into:

- `backend_py/data/nexra-state.json`

The initial imported skill library still comes from:

- `backend/src/main/resources/data/skills.json`

## Default Accounts

If you have not registered a new account yet, the seeded accounts are:

- User: `alice@nexra.local / alice123`
- Admin: `admin@nexra.local / admin123`
