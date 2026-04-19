# Nexra Hosted API Quick Reference

This document only describes how to use the hosted Nexra platform.

## Platform Entry

- Web app: [https://nexracat.com](https://nexracat.com)
- API base: [https://nexracat.com/api](https://nexracat.com/api)
- Dashboard: [https://nexracat.com/api/dashboard](https://nexracat.com/api/dashboard)
- Agent guide: [https://nexracat.com/api/agent-guide](https://nexracat.com/api/agent-guide)

## What To Use First

If you are a normal user:

1. Open the web app.
2. Register with email verification.
3. Log in.
4. Search skills in the marketplace.
5. Open a skill detail page and read provider docs.
6. Let your own agent call the selected provider directly.
7. Return to Nexra and submit a rating or review.

If you are integrating an agent:

1. Call `GET /api/skills`.
2. Compare `recommendationScore`, `overallTrust`, `userRatingAvg`, and `systemScore`.
3. Open `GET /api/skills/{id}` for detail.
4. Call the provider directly outside Nexra.
5. After human review, send feedback to `POST /api/skills/{id}/reviews`.

## Auth Endpoints

- `POST /api/auth/register/request-code`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`

Protected endpoints require:

```text
Authorization: Bearer <token>
```

## Search Endpoints

- `GET /api/skills?q=&function=&page=&pageSize=`
- `GET /api/skills/{id}`

Useful fields in search results:

- `recommendationScore`
- `overallTrust`
- `userRatingAvg`
- `systemScore`
- `functions`
- `invocationMethod`
- `apiDocsUrl`
- `authRequirement`

## User Endpoints

- `POST /api/skills/{id}/reviews`
- `POST /api/skills/submissions`
- `GET /api/users/me`

## Example Requests

```text
GET https://nexracat.com/api/skills?q=ocr&page=0&pageSize=10
GET https://nexracat.com/api/skills?q=story&function=writing&page=0&pageSize=5
GET https://nexracat.com/api/skills/{id}
```

```bash
curl "https://nexracat.com/api/skills?q=image&page=0&pageSize=5"
```

## Product Rule

Nexra does not proxy third-party skill execution in this phase.

Nexra helps users and agents:

- find skills
- compare trust and recommendation signals
- understand calling requirements
- choose the best provider

The actual external skill call must be performed by your own agent runtime.
