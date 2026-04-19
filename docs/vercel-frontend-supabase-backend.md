# Vercel Frontend + Python Backend + Supabase Postgres

This deployment keeps:

- frontend on Vercel
- backend on a long-running Python server
- database on Supabase Postgres

## 1. Recommended Layout

- Frontend: `https://nexracat.com`
- Backend API: `https://api.nexracat.com/api`
- Database: Supabase Postgres

Why this layout:

- Vercel is good for static frontend hosting
- a long-running Python backend avoids serverless cold starts
- Supabase Postgres gives you managed Postgres plus connection pooling

## 2. Deploy The Backend Server

Prepare a Linux server and point a backend subdomain to it:

- `api.nexracat.com -> YOUR_SERVER_IP`

Then run:

```bash
cd /opt/nexra-src
sudo DOMAIN=api.nexracat.com \
  SUPABASE_DATABASE_URL='postgresql://...' \
  CORS_ALLOW_ORIGINS='https://nexracat.com' \
  bash ./deploy-backend-server.sh
```

This script:

- installs Python and nginx
- deploys `backend_py`
- creates a virtualenv
- configures the backend to use Supabase Postgres
- enables CORS for the Vercel frontend domain
- exposes the API at `https://api.nexracat.com/api`

## 3. Migrate Existing Data To Supabase

Set the source and target Postgres URLs:

```bash
export SOURCE_DATABASE_URL='postgresql://current-source-db'
export TARGET_DATABASE_URL='postgresql://supabase-db'
python scripts/migrate_postgres_to_postgres.py
```

If `SOURCE_DATABASE_URL` is omitted, the script will try to read the local private database config file.

The migration copies:

- `nexra_state_store`
- `nexra_auth_users`
- `nexra_auth_sessions`
- `nexra_auth_verifications`

That includes:

- skills
- reviews
- admin moderation data
- visit metrics snapshot
- auth users and sessions

## 4. Point The Vercel Frontend To The New Backend

Before deploying the frontend to Vercel, update the frontend API config:

```powershell
.\Set-NexraFrontendApi.ps1 -ApiBase "https://api.nexracat.com/api"
```

That writes:

- `frontend/config.js`

The frontend will then call the backend directly instead of assuming same-origin `/api`.

## 5. Deploy The Frontend To Vercel

Deploy as usual:

```bash
vercel --prod
```

The frontend loads:

- `frontend/config.js`
- `frontend/app.js`

So the static Vercel site can safely use the remote backend API.

## 6. Supabase Connection Advice

For a long-running Python backend, prefer a normal pooled Postgres connection string instead of a serverless transaction-only connection when possible.

Official reference:

- [Supabase connection strings](https://supabase.com/docs/reference/postgres/connection-strings)

## 7. What To Verify

After deployment:

1. Open the Vercel frontend domain.
2. Check that login and registration hit `https://api.nexracat.com/api`.
3. Check `GET /api/dashboard`.
4. Check `GET /api/admin/metrics`.
5. Check that skills, reviews, and admin moderation data match the old system.
