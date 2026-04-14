# Nexra Full-Stack MVP

Nexra is a separated full-stack MVP for AI skill search, rating, and recommendation.

## Structure

- [backend](C:\Workspace\nexra\backend): Spring Boot REST API
- [frontend](C:\Workspace\nexra\frontend): standalone HTML, CSS, and JS console
- [product-spec.md](C:\Workspace\nexra\docs\product-spec.md): product and platform spec
- [usage-guide.md](C:\Workspace\nexra\docs\usage-guide.md): run and usage guide

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
- Built-in scheduled skill sync that refreshes the local skill library from a public MCP directory

## Run Backend

Build once before first script-based startup:

```bash
cd backend
mvn package
```

Then run:

```bash
cd backend
mvn spring-boot:run
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

## Main API Endpoints

Public and user-facing:

- `GET /api`
- `GET /api/agent-guide`
- `GET /api/dashboard`
- `GET /api/skills?q=&function=&page=&pageSize=`
- `GET /api/skills/{id}`
- `POST /api/skills/{id}/reviews`
- `POST /api/skills/submissions`
- `GET /api/users`
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
