# Nexra

**English** | [中文](./README.zh-CN.md)

Nexra is an open-source full-stack platform for AI skill discovery, scoring, and recommendation.

Instead of forwarding requests or running third-party skills for agents, Nexra focuses on the first-step problem: helping users and agents find the right skill, compare quality signals, understand how a skill should be called, and decide whether it is trustworthy enough to use.

Current public demo:

- Web: [https://nexra-one.vercel.app](https://nexra-one.vercel.app)
- API: [https://nexra-one.vercel.app/api/dashboard](https://nexra-one.vercel.app/api/dashboard)

## Why Nexra

The AI tooling ecosystem is getting crowded. There are more skills, MCP servers, wrappers, APIs, and agent plugins than most teams can realistically evaluate by hand.

Nexra turns that chaos into a searchable marketplace with trust signals:

- Find skills by keyword, function, category, invocation style, and readiness
- Separate user ratings from system-generated agent scores
- Rank skills by match, trust, popularity, and cost efficiency
- Show provider guidance, auth requirements, and call examples
- Let users submit new skills and let admins review them before approval

Nexra does not proxy or execute third-party skills in this phase. It helps agents discover the right skill, then call the provider directly.

## Who this is for

- AI product teams building skill-based agents
- Agent platform builders who need a marketplace and review workflow
- Operations teams that want a governed internal skill catalog
- Developers exploring MCP-style skills and external tool ecosystems

## What Nexra does

- Searches skills by keyword, function, category, invocation style, and readiness
- Separates quality scoring into user ratings and system-generated agent scores
- Ranks skills with trust, match, popularity, and cost efficiency signals
- Supports paginated marketplace browsing with configurable page size
- Lets normal users submit new skills for review
- Gives administrators a dedicated audit workflow to approve, edit, or remove skills
- Shows provider details, auth guidance, and call examples so agents can call the skill provider directly
- Supports local JSON state for development and Postgres state for cloud deployment

## Product positioning

Nexra is a skill search and recommendation system.

Example use cases:

- An agent builder wants to find the best summarization or writing skill for a new workflow
- A team wants users to rate the real usefulness of external skills after trying them
- An admin wants to review user-submitted skills before they appear in the marketplace
- A platform wants a trust layer before letting agents adopt third-party capabilities

Current scope:

- Skill search
- Skill detail and recommendation
- User reviews
- Admin review workflow
- User registration and token-based authentication
- Marketplace tutorial and multilingual onboarding

Out of scope for this phase:

- Route forwarding
- Proxy execution of third-party skills
- Running external skills inside the platform

## Tech stack

- Frontend: static HTML, CSS, and JavaScript
- Backend: Python service structured by business layers
- API hosting: Vercel Python Function
- Cloud storage: Postgres via Neon or any compatible PostgreSQL instance
- Local storage: JSON snapshot file

## Repository structure

- `frontend/`: user-facing web application
- `backend_py/`: layered Python backend
- `api/`: Vercel serverless entrypoint
- `docs/`: usage, deployment, and product documents
- `Start-Nexra.ps1`: one-click local start script
- `Stop-Nexra.ps1`: one-click local stop script
- `vercel.json`: frontend and API routing for Vercel

## Quick start

### 1. Prepare local config

Copy the example config and adjust it if needed:

```powershell
Copy-Item backend_py\config.example.json backend_py\config.json
Copy-Item .env.example .env.local
```

By default, the example config already works for local development.

### 2. Start the project

```powershell
.\Start-Nexra.ps1
```

After startup:

- Frontend: `http://127.0.0.1:4173`
- Backend API: `http://localhost:8080/api`

Stop the project with:

```powershell
.\Stop-Nexra.ps1
```

## Demo deployment

Current public deployment:

- Web: [https://nexra-one.vercel.app](https://nexra-one.vercel.app)
- API: [https://nexra-one.vercel.app/api/dashboard](https://nexra-one.vercel.app/api/dashboard)

Important note:

- Vercel does not provide fixed `IP + port` access
- Production access is domain-based

## Configuration and data policy

This repository is prepared for open-source publishing:

- Local secrets are ignored through `.gitignore`
- Local runtime snapshots are ignored
- Local private config is ignored
- Public sample code and seed catalog remain versioned so contributors can run the platform

Files you should create locally but not commit:

- `.env.local`
- `backend_py/config.json`
- `backend_py/data/nexra-state.json`
- `.runtime/`
- `logs/`
- `硬件参数.png`

Templates included in the repo:

- `.env.example`
- `backend_py/config.example.json`

The backend now automatically loads:

1. `backend_py/config.json` if it exists
2. `backend_py/config.example.json` otherwise

## Main API surface

Public and authenticated user flows:

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
- `GET /api/users/me`
- `GET /api/billing/summary`
- `GET /api/billing/transactions`
- `GET /api/keys`
- `POST /api/keys`

Admin flows:

- `GET /api/admin/skills/pending`
- `POST /api/admin/skills/{id}/approve`
- `PUT /api/admin/skills/{id}`
- `DELETE /api/admin/skills/{id}`
- `GET /api/admin/skills/sync/status`
- `POST /api/admin/skills/sync`

## Storage modes

Local development:

- Uses `backend_py/data/nexra-state.json` for runtime state

Cloud deployment:

- Uses `POSTGRES_URL` or `DATABASE_URL`
- Recommended on Vercel and other production environments

Seed skill catalog:

- `backend/src/main/resources/data/skills.json`

That seed file is intentionally versioned as public sample content so the marketplace can run after clone.

## Open-source usage docs

- `docs/usage-guide.md`
- `docs/cloud-deployment.md`
- `docs/vercel-deployment.md`
- `docs/product-spec.md`

## Recommended GitHub Description

If you want the repository homepage to look stronger, use this description:

`Open-source AI skill marketplace for discovery, scoring, recommendation, and governance.`

## Recommended GitHub Topics

Use these repository topics on GitHub:

- `ai`
- `agent`
- `ai-agents`
- `marketplace`
- `mcp`
- `skill-discovery`
- `recommendation-system`
- `python`
- `vercel`
- `postgres`

## Contributing

Contributions are welcome.

Good first contribution areas:

- Better ranking strategies for skill recommendation
- Better admin moderation workflows
- Additional language support in the frontend
- Better skill import quality and deduplication
- Improved onboarding and tutorial UX

See [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution notes.

## License

This project is released under the MIT License. See `LICENSE`.
