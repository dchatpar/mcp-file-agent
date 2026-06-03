# Instructions for Abin — Using `install.py`

Hi Abin,

This guide explains the **one-command installer** at the repo root (`install.py`). It takes a fresh clone from zero to a **production-verified** Local File Search MCP Agent without manual steps.

**Repository:** https://github.com/dchatpar/mcp-file-agent  
**Installer file:** `install.py` (repo root)

---

## What `install.py` does

`install.py` is a single Python script that automates the full setup and verification pipeline:

| Phase | What happens |
|-------|----------------|
| **1 — Auto-heal** | Removes a legacy broken `species_count_2024.xlsx` if present (old misnamed file that Excel cannot open) |
| **2 — Virtual environment** | Creates `.venv` if missing (Python 3.11+ required) |
| **3 — Dependencies** | Runs `pip install -e ".[dev]"` (retries once on failure) |
| **4 — Configuration** | Writes or updates `.env` (MiniMax or OpenAI profile, `SEARCH_ROOT`, API key) |
| **5 — Sample data** | Ensures exactly **8** zoology sample files exist under `data/samples/zoology/` |
| **6 — Production gate** | Runs lint, pytest (40 tests), security checks, and optionally live E2E + assignment spot-check |
| **7 — Docker** *(optional)* | Builds the Docker image if you choose yes and Docker is installed |

At the end you get a **summary block** showing venv path, sample count, provider, and gate result (`PASS` / `FAIL`).

---

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| **Python 3.11+** | 3.12 recommended. On Ubuntu/WSL: `sudo apt install python3.12 python3.12-venv` |
| **git** | To clone the repository |
| **Outbound HTTPS** | For pip packages; for full E2E also LLM API + Microsoft Learn MCP |
| **API key** *(optional for quick review)* | MiniMax or OpenAI — only needed if you run the full E2E gate |

You do **not** need Docker unless you opt in during the wizard.

---

## Step 1 — Clone and enter the repo

```bash
git clone https://github.com/dchatpar/mcp-file-agent.git
cd mcp-file-agent
```

Accept the GitHub collaborator invite if you have not already:  
https://github.com/dchatpar/mcp-file-agent/invitations

---

## Step 2 — Choose how to run the installer

Make the script executable once:

```bash
chmod +x install.py
```

### Option A — Quick review (no API key)

Use this to verify structure, tests, and sample data **without** calling the LLM:

```bash
./install.py --non-interactive --skip-e2e --yes
```

**What runs:** sample generation, ruff lint, 40 pytest tests, 4 security tests.  
**What is skipped:** E2E agent (5 checks) and assignment spot-check (3 live queries).  
**Expected result:** Summary shows `Gate: PASS` and `Samples: ... (8 files)`.

Typical runtime: **~10–15 seconds** (no network LLM calls).

---

### Option B — Interactive full setup (recommended for hands-on review)

```bash
./install.py
```

The wizard will ask:

1. **Existing `.env`?** — keep / merge / overwrite (if a key is already present)
2. **LLM provider** — `m` = MiniMax (default), `o` = OpenAI
3. **API key** — hidden prompt; press Enter to skip if you will not run E2E
4. **SEARCH_ROOT** — default `data/samples/zoology`
5. **Run E2E + spot-check?** — yes uses your API key (~1–2 minutes)
6. **Build Docker?** — only shown if `docker` is on PATH
7. **Proceed?** — confirm before install starts

---

### Option C — Full production verification (with API key)

If you have a MiniMax or OpenAI key and want the **complete** gate including live agent queries:

```bash
# After setting your key interactively, or with .env already present:
./install.py --yes
```

Or non-interactive if `.env` already contains `OPENAI_API_KEY`:

```bash
./install.py --non-interactive --yes
```

**Expected result:** All 6 production-gate steps PASS, including E2E and spot-check (~90 seconds total).

---

## Command-line flags reference

| Flag | Effect |
|------|--------|
| *(none)* | Interactive wizard (when run in a terminal) |
| `--yes` | Accept default answers for all prompts |
| `--non-interactive` | No prompts; uses defaults and existing `.env` |
| `--skip-e2e` | Skip E2E and spot-check (no API key required) |
| `--help` | Show argparse help |

**Common combinations:**

```bash
./install.py --non-interactive --skip-e2e --yes   # fastest review path
./install.py --skip-e2e --yes                     # interactive but no API
./install.py                                      # full interactive setup
```

---

## Configuration (`.env`)

The installer writes `.env` at the repo root (mode `600` where supported). **Never commit `.env`.**

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | MiniMax or OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.minimax.io/v1` (default) or `https://api.openai.com/v1` |
| `OPENAI_MODEL` | e.g. `MiniMax-M2.7` or `gpt-4o` |
| `SEARCH_ROOT` | Directory the local MCP searches (default: `data/samples/zoology`) |

Templates in the repo:

- **MiniMax:** `.env.example`
- **OpenAI:** `.env.openai.example`

To switch providers manually, copy the matching template or re-run `./install.py` and choose overwrite.

---

## Step 3 — Confirm success

After install completes, check the summary:

```
Production install summary
  Root:        .../mcp-file-agent
  Venv:        .../mcp-file-agent/.venv
  Samples:     .../data/samples/zoology (8 files)
  Provider:    minimax
  Gate:        PASS
```

**Sample files (8 total, 5 extensions):**

| File | Type |
|------|------|
| `african_elephant_study.pdf` | PDF |
| `marine_mammals_report.pdf` | PDF |
| `bird_migration_analysis.pdf` | PDF |
| `amphibian_survey_2023.pdf` | PDF |
| `coral_reef_observations.docx` | DOCX |
| `species_count_2024.xls` | XLS (Excel 97–2003; opens in Excel/LibreOffice) |
| `field_notes_borneo.txt` | TXT |
| `jaguar_photo_rainforest.jpg` | JPG |

> **Note:** If you see `species_count_2024.xlsx` in the samples folder, delete it and re-run `./install.py` — that was a legacy misnamed file. The correct spreadsheet is **`species_count_2024.xls`**.

---

## Step 4 — Run the agent

```bash
source .venv/bin/activate
file-search-agent
```

Example queries to try in the REPL:

```
List all PDF files in the zoology folder
Search PDFs for elephant population
What is Azure Functions?   # routes to Microsoft Learn MCP
```

Type `quit` or `exit` to leave.

---

## Re-run verification without reinstalling

From an activated venv:

```bash
# Full gate (needs API key in .env)
python -u scripts/production_gate.py

# Gate without live LLM calls
python -u scripts/production_gate.py --skip-e2e

# E2E only
python -u scripts/e2e_verify.py

# Assignment spot-check only
python -u scripts/spotcheck_assignment.py
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Python 3.11+ required` | Install Python 3.12 and venv support (see prerequisites) |
| `venv creation failed` | `sudo apt install python3-venv` |
| Gate fails on sample count (9 files) | Re-run `./install.py` — Phase 1 removes duplicate `.xlsx` |
| Excel sample won't open | Use `species_count_2024.xls`, not `.xlsx` |
| E2E skipped unexpectedly | Pass API key in wizard or set `OPENAI_API_KEY` in `.env`; do not use `--skip-e2e` |
| OpenAI HTTP 400 on `extra_body` | Set `OPENAI_BASE_URL=https://api.openai.com/v1` for OpenAI (MiniMax-only params are auto-omitted) |
| Install appears stuck during E2E | Normal — live LLM + MCP calls take 1–2 minutes |

More detail: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## What to review in the repo

After a successful install:

| Area | Path / command |
|------|----------------|
| Agent + MCP wiring | `src/file_search_agent/agent_factory.py` |
| Local search tools | `src/file_search_agent/mcp/local_file_search.py` |
| SKILL routing | `src/file_search_agent/SKILL.md` |
| Tests | `pytest -v` (40 tests) |
| Compliance sign-off | `docs/COMPLIANCE_REPORT.md` |
| Architecture | `docs/PROJECT_OVERVIEW.md` |
| Deployment (Docker/systemd) | `docs/DEPLOYMENT.md` |

---

## Suggested review workflow

1. **Clone** the repo and accept the collaborator invite.
2. **Quick verify:** `./install.py --non-interactive --skip-e2e --yes` — confirm gate PASS and 8 samples.
3. **Optional full verify:** Add your API key, run `./install.py --yes` with E2E enabled — confirm all 6 gate steps PASS.
4. **Try the CLI:** `file-search-agent` with the sample queries above.
5. **Read** `docs/COMPLIANCE_REPORT.md` and `docs/PROJECT_OVERVIEW.md` for assignment mapping.

If anything fails, paste the terminal output from the failing phase — the installer prints each command it runs.

---

## Questions

For issues with the assessment deliverable, reply to the submission thread or open a GitHub issue on the repo.
