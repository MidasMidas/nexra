# Nexra Product Spec

## Product Positioning

Nexra is a platform for AI agents to discover, evaluate, and choose external skills through a unified trust, search, and moderation layer.

This iteration focuses on the rating system, search, recommendation, and skill governance rather than route forwarding.

## Core Product Direction

Nexra now acts as a skill trust and governance layer:

- Agents and users search for skills by capability
- Every skill exposes both user rating and system rating
- Results are ranked by recommendation score and overall trust
- Users can submit new skills
- Admins approve, edit, delete, and maintain skill quality
- Agents call the chosen skill provider directly outside Nexra

## Rating Model

Trust is split into two systems.

### 1. User Rating

Purpose:

- Capture human judgment about usefulness and quality

Fields:

- `userRatingAvg`
- `userRatingCount`
- `reviews`

### 2. System Rating

Purpose:

- Capture machine-observed execution quality

Fields:

- `systemScore`
- `successRate`
- `latencyP95`
- `costEfficiency`

Suggested formula:

```text
systemScore = 0.5 * success_rate + 0.3 * latency_score + 0.2 * cost_score
```

### 3. Overall Trust

Purpose:

- Give users and agents one final ranking signal

Suggested formula:

```text
overallTrust = 0.45 * normalized_user_rating + 0.55 * systemScore
```

## Skill Search and Discovery

The platform must support searching skills by:

- skill name
- category
- description
- function/capability
- invocation method

Search result requirements:

- paginated list
- configurable `pageSize`
- each item must include detailed trust and usage info
- each item must include recommendation info and calling guidance

Each result should include at least:

- `name`
- `category`
- `description`
- `functions`
- `invocationMethod`
- `recommendationScore`
- `matchScore`
- `recommendationSummary`
- `userRatingAvg`
- `systemScore`
- `overallTrust`
- `providerName`
- `apiDocsUrl`
- `authRequirement`
- `submittedBy`
- `approvalStatus`

## Skill Detail Expectations

Each skill detail page should help an agent decide whether and how to use the skill provider directly.

Required fields:

- `providerName`
- `providerUrl`
- `apiDocsUrl`
- `authRequirement`
- `operatingSystem`
- `license`
- `callExample`
- `source`

## Identity and Roles

### Normal User

Can:

- browse approved skills
- search skills
- submit reviews
- submit new skills for approval

### Admin

Can:

- review pending skills
- approve submitted skills
- update skill ratings
- update skill metadata and details
- delete skills

## Current API Shape

### Public and User APIs

- `GET /api`
- `GET /api/agent-guide`
- `GET /api/dashboard`
- `GET /api/skills?q=&function=&page=&pageSize=`
- `GET /api/skills/{id}`
- `POST /api/skills/{id}/reviews`
- `POST /api/skills/submissions`
- `GET /api/users`

### Admin APIs

- `GET /api/admin/skills/pending`
- `POST /api/admin/skills/{id}/approve`
- `PUT /api/admin/skills/{id}`
- `DELETE /api/admin/skills/{id}`

## MVP Scope Now

Included now:

- skill trust model with user score and system score
- skill search by function and keyword
- recommendation score with capability-match ranking
- paginated skill results
- lightweight identity model
- user-submitted skills
- admin moderation workflow
- admin rating/detail maintenance
- provider docs and calling guidance in skill detail

Still excluded for now:

- route forwarding gateway execution
- third-party skill runtime hosting
- multi-tenant org model
- production auth and session system
- persistent database-backed storage
- advanced policy engine

## Next Logical Steps

- move identity from header-based simulation to real auth
- persist users, skills, and reviews in MySQL or PostgreSQL
- add reject flow with audit reason
- expose admin moderation in the frontend
- add richer ranking and filtering controls
