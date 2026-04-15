# Contributing to Nexra

Thanks for contributing to Nexra.

Nexra is an open-source project focused on AI skill discovery, scoring, recommendation, and governance. We welcome product improvements, bug fixes, documentation updates, frontend polish, backend refactors, and better recommendation logic.

## Good first contributions

- Improve marketplace search and filtering
- Improve recommendation explanations and ranking logic
- Improve admin review workflows
- Improve localization and translations
- Improve onboarding content and tutorials
- Improve deployment docs
- Add tests around core scoring and moderation flows

## Local setup

1. Copy the local config templates:

```powershell
Copy-Item backend_py\config.example.json backend_py\config.json
Copy-Item .env.example .env.local
```

2. Start the project:

```powershell
.\Start-Nexra.ps1
```

3. Open:

- Frontend: `http://127.0.0.1:4173`
- API: `http://localhost:8080/api`

## Contribution guidelines

- Do not commit local secrets, local config, runtime logs, or database snapshots
- Keep changes scoped and explain the user-facing impact clearly
- Prefer improving docs when behavior changes
- Preserve the product direction: discovery, recommendation, and trust first
- Do not reintroduce route forwarding or proxy execution into the first-phase product without discussion

## Before opening a pull request

- Make sure the app still starts locally
- Verify the main user flow you touched
- Update docs if setup, behavior, or deployment changed
- Keep commits readable and focused

## Areas where help is especially welcome

- Better ranking models
- Better skill data quality
- Better moderation tooling
- Better frontend usability
- Better test coverage

Thanks for helping make Nexra more useful for agent builders and teams.
