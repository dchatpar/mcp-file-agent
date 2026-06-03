# Deployment Guide

End-to-end deployment for the Local File Search MCP Agent: prerequisites through GitHub publish, local/WSL production, Docker, and Linux VM with systemd.

---

## Phase 0 ù Prerequisites

| Requirement | Notes |
|-------------|-------|
| Python | 3.11+ (3.12 recommended; Docker image uses 3.12-slim) |
| git | Clone and version control |
| Outbound HTTPS | LLM API (MiniMax or OpenAI) + `learn.microsoft.com/api/mcp` |
| Disk | Sample data under `data/samples/zoology/` or custom `SEARCH_ROOT` |
| API key | MiniMax or OpenAI key in `.env` (never committed) |

---

## Phase 1 ù Clone and build

```bash
git clone <repo-url>
cd <repo>
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # MiniMax profile
# or: cp .env.openai.example .env   # OpenAI profile
python scripts/generate_samples.py
```

**Success:** 8 files in `data/samples/zoology/`, `pytest -v` passes without API key for unit tests.

---

## Phase 2 ù Configure secrets

Create `.env` at repo root (mode `600` on servers):

| Variable | Production guidance |
|----------|---------------------|
| `OPENAI_API_KEY` | Required for agent; use orchestrator secret injection in prod |
| `OPENAI_BASE_URL` | MiniMax: `https://api.minimax.io/v1`; OpenAI: `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Provider-specific model id |
| `SEARCH_ROOT` | **Absolute path** on servers (e.g. `/var/lib/file-search/zoology`) |
| `MICROSOFT_LEARN_MCP_URL` | Default Learn endpoint; change only if Microsoft updates URL |
| `MS_ANSWER_MAX_CHARS` | Default `2000`; adjust if assignment limits change |

Templates:

- MiniMax: `.env.example`
- OpenAI: `.env.openai.example`

See [LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md) for provider-specific values.

---

## Phase 3 ù Pre-deploy verification gate

Run before any production deploy (single command):

```bash
source .venv/bin/activate
python -u scripts/production_gate.py
```

Or run steps individually:

| Gate | Command | API key | Expected |
|------|---------|---------|----------|
| Samples | `python scripts/generate_samples.py` | No | 8 files |
| Lint | `ruff check src tests scripts` | No | All checks passed |
| Unit tests | `pytest -v` | No | 40 passed |
| Security | `pytest tests/test_security.py -v` | No | 4 passed |
| E2E | `python -u scripts/e2e_verify.py` | Yes | 5/5 PASSED |
| Spot-check | `python -u scripts/spotcheck_assignment.py` | Yes | 3/3 PASSED |

```bash
source .venv/bin/activate
python scripts/generate_samples.py
ruff check src tests scripts
pytest -v
pytest tests/test_security.py -v
python -u scripts/e2e_verify.py
python -u scripts/spotcheck_assignment.py
```

**Do not deploy** if lint or pytest fail. E2E/spot-check require a valid API key and outbound network.

---

## Phase 4 ù GitHub publish

```bash
cd /path/to/repo
git remote add origin https://github.com/YOUR_USERNAME/mcp-file-agent.git   # if not set

# Detect default branch
git branch --show-current   # e.g. master or main

git push -u origin $(git branch --show-current)
```

**Reviewer access:** GitHub ? Settings ? Collaborators ? add **`abin-aot`**.

**Never** `git add .env` ù confirm with `git status` before push.

---

## Phase 5 ù Local / WSL production run

### Dedicated venv (recommended)

```bash
cd /opt/file-search-agent   # or your install path
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env        # edit with production values
chmod 600 .env
python scripts/generate_samples.py
file-search-agent
```

### System-wide editable install (dev machine)

```bash
pip install -e .
file-search-agent
```

### Optional wrapper script

Document-only pattern (`bin/run-agent.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate
exec file-search-agent
```

The default CLI is an **interactive REPL**. For headless validation on servers, use batch scripts instead (Phase 7).

---

## Phase 6 ù Docker deployment

Artifacts in repo root:

| File | Role |
|------|------|
| `Dockerfile` | `python:3.12-slim`, `pip install -e .`, ENTRYPOINT `file-search-agent` |
| `.dockerignore` | Excludes `.venv`, `.git`, `__pycache__`, `.env` |
| `docker-compose.yml` | Service `file-search-agent`, `env_file: .env`, volume for search root |

### Build

```bash
docker compose build
```

### Run interactive CLI

```bash
docker compose run --rm file-search-agent
```

### Run one-shot E2E inside container

```bash
docker compose run --rm file-search-agent python -u scripts/e2e_verify.py
```

### Production notes

- **Do not bake secrets into the image.** Use `env_file: .env`, Docker secrets, or orchestrator env injection.
- Mount `SEARCH_ROOT` as a read-only volume when using custom corpora.
- Set `PYTHONUNBUFFERED=1` (already in Dockerfile) for visible E2E progress.

Example custom search root:

```bash
SEARCH_ROOT=/path/to/corpus docker compose run --rm file-search-agent
```

Update `docker-compose.yml` volume mapping if your host path differs.

---

## Phase 7 ù Linux VM + systemd

### 1. Create service user

```bash
sudo useradd --system --home-dir /opt/file-search-agent --shell /usr/sbin/nologin filesearch
```

### 2. Deploy application

```bash
sudo mkdir -p /opt/file-search-agent
sudo cp -r . /opt/file-search-agent/
sudo chown -R filesearch:filesearch /opt/file-search-agent
sudo -u filesearch bash -c 'cd /opt/file-search-agent && python3 -m venv .venv && .venv/bin/pip install -e .'
sudo -u filesearch cp /opt/file-search-agent/.env.example /opt/file-search-agent/.env
# Edit /opt/file-search-agent/.env with production values
sudo chmod 600 /opt/file-search-agent/.env
sudo -u filesearch /opt/file-search-agent/.venv/bin/python /opt/file-search-agent/scripts/generate_samples.py
```

### 3. Install systemd unit

Copy `deploy/file-search-agent.service.example` to `/etc/systemd/system/file-search-agent.service`, adjust paths, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now file-search-agent
sudo journalctl -u file-search-agent -f
```

**Important:** The default unit runs the **interactive REPL**, which needs a TTY. For headless servers:

- Use `ExecStart=.../python -u .../scripts/e2e_verify.py` for batch validation (see commented line in the example unit), or
- Run spot-check / E2E via cron after deploy.

A web API wrapper is out of scope for this assignment (document as future extension only).

---

## Phase 8 ù Network and MCP

### Outbound allowlist

| Host | Purpose |
|------|---------|
| `api.minimax.io` or `api.openai.com` | LLM API |
| `learn.microsoft.com` | Microsoft Learn MCP (`streamable_http`) |

### Local MCP

The local file search MCP runs **in-process** inside the agent ù no extra port or sidecar required.

### Firewall checklist

- [ ] Outbound HTTPS (443) to LLM provider
- [ ] Outbound HTTPS to `learn.microsoft.com`
- [ ] No inbound ports required for CLI-only deployment

---

## Post-deploy

- Day-2 operations: [OPERATIONS.md](OPERATIONS.md)
- Issues: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- LLM provider changes: [LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md)
