# Nexra

**English** | [中文](./README.zh-CN.md)

Nexra is an open platform for AI skill discovery, scoring, and recommendation.

The main way to use Nexra is through the hosted Nexra platform and API, not by cloning this repository first.

## Use Nexra Online

Start here:

- Web app: [https://nexra-one.vercel.app](https://nexra-one.vercel.app)
- API base: [https://nexra-one.vercel.app/api](https://nexra-one.vercel.app/api)
- Dashboard example: [https://nexra-one.vercel.app/api/dashboard](https://nexra-one.vercel.app/api/dashboard)
- Agent guide: [https://nexra-one.vercel.app/api/agent-guide](https://nexra-one.vercel.app/api/agent-guide)

If you want your agent to use Nexra, the normal flow is:

1. Call Nexra's API to search skills.
2. Read the returned ratings, recommendation signals, and provider details.
3. Choose a skill.
4. Let your agent call the skill provider directly.
5. Send ratings and feedback back to Nexra.

Nexra is not a proxy execution layer in this phase. It is a discovery, recommendation, and governance platform.

## What Nexra helps you do

- Search skills by keyword, function, category, invocation style, and readiness
- Separate user ratings from system-generated agent scores
- Rank skills by match, trust, popularity, and cost efficiency
- Read provider guidance, auth requirements, and call examples
- Submit new skills for review
- Review and approve skills through an admin workflow

## Main API surface

Public and user flows:

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

Admin flows:

- `GET /api/admin/skills/pending`
- `POST /api/admin/skills/{id}/approve`
- `PUT /api/admin/skills/{id}`
- `DELETE /api/admin/skills/{id}`
- `GET /api/admin/skills/sync/status`
- `POST /api/admin/skills/sync`

## Example use cases

- An agent builder wants to find the best summarization or writing skill for a new workflow
- A team wants users to rate the real usefulness of external skills after trying them
- An admin wants to review user-submitted skills before they appear in the marketplace
- A platform wants a trust layer before letting agents adopt third-party capabilities

## Who this is for

- AI product teams building skill-based agents
- Agent platform builders who need a marketplace and review workflow
- Operations teams that want a governed internal skill catalog
- Developers exploring MCP-style skills and external tool ecosystems

## Self-hosting and development

This repository is for contributors, self-hosting, and local development.

Use the source code directly only if you want to:

- contribute to Nexra
- self-host your own Nexra instance
- modify the frontend or backend
- run the full stack locally for development

Local developer setup:

```powershell
Copy-Item backend_py\config.example.json backend_py\config.json
Copy-Item .env.example .env.local
.\Start-Nexra.ps1
```

After startup:

- Frontend: `http://127.0.0.1:4173`
- Local API: `http://localhost:8080/api`

## Architecture

- `frontend/`: user-facing web application
- `backend_py/`: layered Python backend
- `api/`: Vercel Python Function entrypoint
- `docs/`: usage, deployment, and product documents

Tech stack:

- Frontend: HTML, CSS, and JavaScript
- Backend: Python
- Hosting: Vercel
- Persistence: JSON locally, Postgres in cloud environments

## Deployment

This repository is prepared for Vercel deployment:

- `api/index.py`
- `vercel.json`
- `requirements.txt`
- `runtime.txt`

Recommended environment variables:

- `POSTGRES_URL`
- `NEXRA_STATE_BACKEND=postgres`
- `NEXRA_STATE_KEY=primary`

Important note:

- Vercel does not expose a fixed `IP + port`
- Production access is domain-based

## Open-source and privacy notes

This repository has been cleaned for open-source publishing:

- Local secrets are ignored
- Local private config is ignored
- Runtime logs and snapshots are ignored
- The local image `硬件参数.png` is ignored and not uploaded

Files that should stay local:

- `.env.local`
- `backend_py/config.json`
- `backend_py/data/nexra-state.json`
- `.runtime/`
- `logs/`
- `硬件参数.png`

## Docs

- `docs/usage-guide.md`
- `docs/vercel-deployment.md`
- `docs/cloud-deployment.md`
- `docs/product-spec.md`

## Recommended GitHub Description

`Open-source AI skill marketplace for discovery, scoring, recommendation, and governance.`

## Recommended GitHub Topics

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

Contributions are welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT License. See `LICENSE`.
