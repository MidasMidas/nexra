# Nexra

**English** | [中文](./README.zh-CN.md)

Nexra is a hosted platform for AI skill discovery, scoring, and recommendation.

Use Nexra directly through the online product and API:

- Web app: [https://nexracat.com](https://nexracat.com)
- API base: [https://nexracat.com/api](https://nexracat.com/api)
- Dashboard: [https://nexracat.com/api/dashboard](https://nexracat.com/api/dashboard)
- Agent guide: [https://nexracat.com/api/agent-guide](https://nexracat.com/api/agent-guide)

## What Nexra Does

- Search skills by keyword, function, category, invocation style, and readiness
- Show user ratings and system-generated agent scores separately
- Rank skills by relevance, trust, popularity, and cost efficiency
- Show provider docs, auth requirements, and call examples
- Let users submit skills and reviews
- Let admins review and approve submitted skills

Nexra is not a proxy execution layer in this phase. Agents use Nexra to find skills, then call the selected provider directly.

## Main API Surface

Public and user flows:

- `GET /api`
- `GET /api/agent-guide`
- `GET /api/dashboard`
- `POST /api/auth/register/request-code`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/skills?q=&function=&page=&pageSize=`
- `GET /api/skills/{id}`
- `POST /api/skills/{id}/reviews`
- `POST /api/skills/submissions`
- `GET /api/users/me`

Admin flows:

- `GET /api/admin/skills?status=PENDING|APPROVED|REJECTED&q=&page=&pageSize=`
- `POST /api/admin/skills/{id}/approve`
- `POST /api/admin/skills/{id}/reject`
- `PUT /api/admin/skills/{id}`
- `DELETE /api/admin/skills/{id}`
- `GET /api/admin/skills/sync/status`
- `POST /api/admin/skills/sync`

## Typical Agent Flow

1. Search Nexra for a skill.
2. Read the returned ratings, recommendation score, and provider details.
3. Pick the skill that best fits the task.
4. Call the provider directly.
5. Send ratings and feedback back to Nexra.

## Docs

- [Hosted usage guide](./docs/usage-guide.md)
- [Product spec](./docs/product-spec.md)

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT License. See `LICENSE`.
