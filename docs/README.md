# Documentation

Guides for the Local File Search MCP Agent ù architecture, LLM provider migration, deployment, and day-2 operations.

## Audience

| Reader | Start here |
|--------|------------|
| Reviewer / new contributor | [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) |
| **Abin (assessment reviewer)** | **[INSTRUCTIONS_FOR_ABIN.md](INSTRUCTIONS_FOR_ABIN.md)** ù `install.py` walkthrough |
| Operator switching MiniMax ? OpenAI | [LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md) |
| DevOps / deploy engineer | [DEPLOYMENT.md](DEPLOYMENT.md) |
| On-call / maintainer | [OPERATIONS.md](OPERATIONS.md) + [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |

## Recommended reading order

1. **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** ù What was built, architecture, compliance, tests, sample data.
2. **[LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md)** ù MiniMax default vs OpenAI migration, env profiles, verification.
3. **[DEPLOYMENT.md](DEPLOYMENT.md)** ù End-to-end deploy: local, Docker, Linux VM + systemd, GitHub.
4. **[OPERATIONS.md](OPERATIONS.md)** ù Key rotation, corpus updates, upgrades, CI suggestions.
5. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** ù Symptom ? cause ? fix from project history.

## Related documents

| Document | Purpose |
|----------|---------|
| [../README.md](../README.md) | Quickstart, env table, QA matrix |
| [COMPLIANCE_REPORT.md](COMPLIANCE_REPORT.md) | Assignment audit (40 pytest, E2E 5/5, spot-check 3/3) |
| [SUBMISSION_EMAIL_TO_ABIN.html](SUBMISSION_EMAIL_TO_ABIN.html) | AOT submission email (HTML, copy/paste) |
| [SUBMISSION_EMAIL_TO_ABIN.md](SUBMISSION_EMAIL_TO_ABIN.md) | Plain-text version |
| [INSTRUCTIONS_FOR_ABIN.md](INSTRUCTIONS_FOR_ABIN.md) | Step-by-step `install.py` guide for Abin |
| [../.env.example](../.env.example) | MiniMax profile template |
| [../.env.openai.example](../.env.openai.example) | OpenAI profile template |

## Quick links

```bash
# Lint + unit tests (no API key)
ruff check src tests scripts && pytest -v

# E2E (requires OPENAI_API_KEY in .env)
python -u scripts/e2e_verify.py

# Assignment spot-check (3 queries)
python -u scripts/spotcheck_assignment.py
```
