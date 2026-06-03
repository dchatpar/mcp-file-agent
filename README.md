# Local File Search MCP Agent

LangChain CLI agent that combines an in-process **Local File Search** MCP (FastMCP) with the remote **Microsoft Learn** MCP. The LLM uses **MiniMax** via the [OpenAI-compatible API](https://platform.minimax.io/docs/api-reference/text-openai-api).

## Features

- `search_files` — metadata filters (name, folder, extension, dates, size)
- `search_pdf_content` — PDF full-text keyword search via `pypdf`
- Microsoft Learn MCP at `https://learn.microsoft.com/api/mcp` (`streamable_http`)
- SKILL-based routing with JSON-only local results and 2000-char MS answers
- Async REPL CLI

## Documentation

| Guide | Description |
|-------|-------------|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) | Architecture and what was built |
| [docs/LLM_PROVIDER_GUIDE.md](docs/LLM_PROVIDER_GUIDE.md) | MiniMax ↔ OpenAI migration |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deploy: local, GitHub, Docker, systemd |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Operations and CI |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues |
| [docs/COMPLIANCE_REPORT.md](docs/COMPLIANCE_REPORT.md) | Assignment audit |

## Setup

```bash
cd /home/dchat/test
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Set OPENAI_API_KEY in .env (never commit .env)
```

## MiniMax (OpenAI-compatible)

Configure `.env`:

```bash
OPENAI_API_KEY=<your MiniMax API key>
OPENAI_BASE_URL=https://api.minimax.io/v1
OPENAI_MODEL=MiniMax-M2.7
```

LangChain uses `ChatOpenAI` with `base_url` pointing at MiniMax. MiniMax-only `extra_body` (thinking disabled) is applied automatically when the base URL contains `minimax`. `OPENAI_API_BASE_URL` is accepted as an alias for `OPENAI_BASE_URL`.

**Assignment / OpenAI GPT-5.x:** Defaults to **MiniMax-M2.7**. For OpenAI, copy `.env.openai.example` to `.env` or set `OPENAI_BASE_URL=https://api.openai.com/v1`, your GPT model id, and an OpenAI API key. Full steps: [docs/LLM_PROVIDER_GUIDE.md](docs/LLM_PROVIDER_GUIDE.md).

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required for agent E2E (MiniMax key) |
| `OPENAI_BASE_URL` | `https://api.minimax.io/v1` | MiniMax OpenAI-compatible endpoint |
| `OPENAI_MODEL` | `MiniMax-M2.7` | Model name on MiniMax |
| `SEARCH_ROOT` | `data/samples/zoology` | Sandboxed search directory |
| `FILE_SEARCH_ROOT` | (same as `SEARCH_ROOT`) | Alias for `SEARCH_ROOT` |
| `MICROSOFT_LEARN_MCP_URL` | `https://learn.microsoft.com/api/mcp` | Learn MCP endpoint |
| `MS_ANSWER_MAX_CHARS` | `2000` | Max length for Microsoft Learn answers |

## Run CLI

```bash
file-search-agent
# or
python -m file_search_agent.main
```

## Sample queries

- Local (JSON only): `What PDF files are available in our system?`
- Learn (≤2000 chars): `What is Azure Blob Storage?`
- PDF content search: `Find mentions of migration in the PDFs`
- Out-of-scope: `What is the capital of France?` → refusal JSON

## Test data

The [`data/samples/zoology/`](data/samples/zoology) directory holds 8 non-technical zoology files used for all local-search tests:

| File | Extension | Description |
|------|-----------|-------------|
| `african_elephant_study.pdf` | .pdf | Elephant population dynamics |
| `marine_mammals_report.pdf` | .pdf | Orca/dolphin hydrophone survey |
| `bird_migration_analysis.pdf` | .pdf | Arctic tern geolocator study |
| `amphibian_survey_2023.pdf` | .pdf | Chytrid fungus impact assessment |
| `coral_reef_observations.docx` | .docx | Great Barrier Reef transect notes |
| `species_count_2024.xlsx` | .xlsx | Endangered species population counts |
| `field_notes_borneo.txt` | .txt | Borneo rainforest expedition diary |
| `jaguar_photo_rainforest.jpg` | .jpg | Camera-trap image placeholder |

Regenerate with: `python scripts/generate_samples.py`

## Verification

### QA matrix

| Check | Command | API key | Expected |
|-------|---------|---------|----------|
| Lint | `ruff check src tests scripts` | No | All checks passed |
| Unit tests | `pytest -v` | No | 40 passed |
| E2E agent | `python -u scripts/e2e_verify.py` | Yes | 5/5 PASSED (~1–2 min) |
| Production gate | `python -u scripts/production_gate.py` | Yes | All 6 steps PASS (~90s) |
| Sample data | `python scripts/generate_samples.py` | No | 8 files in `data/samples/zoology/` |

Run lint and unit tests in parallel:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
python scripts/generate_samples.py
ruff check src tests scripts & pytest -v & wait
```

**E2E (requires `OPENAI_API_KEY` in `.env`):**

Takes about **1–2 minutes**. Use unbuffered output so progress prints appear immediately (`[1/5]` … `[5/5]`):

```bash
python -u scripts/e2e_verify.py
```

Checks:

1. PDF files query → local tools, JSON with PDF entries
2. List all files → local tools, 8 files total
3. Elephant search → local tools, elephant match in JSON
4. Azure Blob Storage → Learn MCP only, answer ≤ 2000 chars
5. Out-of-scope (capital of France) → assignment error JSON, no tools

Interactive CLI smoke test:

```bash
file-search-agent
```

### Assignment compliance

| Requirement | Implementation | Verified by |
|-------------|----------------|-------------|
| Local File Search MCP (in-process) | `mcp/local_file_search.py` via FastMCP | `test_local_mcp.py`, E2E [1–3] |
| `search_files` metadata filters | name, folder, extension, dates, size | `test_search_files_*` |
| `search_pdf_content` full-text | pypdf keyword search | `test_search_pdf_content_keyword` |
| `list_all_files` | lists all sandboxed files | `test_list_all_files_returns_eight`, E2E [2] |
| `read_pdf_content` | read single PDF by path | `test_read_pdf_content_*` |
| Microsoft Learn MCP (remote) | `streamable_http` at learn.microsoft.com | `test_learn_mcp.py`, E2E [4] |
| SKILL routing (local JSON / MS prose / out-of-scope) | `SKILL.md`, `routing.py`, `output_guard.py` | `test_agent_routing.py`, E2E [5] |
| MiniMax via OpenAI-compatible API | `ChatOpenAI` + conditional `extra_body` | `agent_factory.py`, `test_agent_factory.py`, E2E all |
| Sandboxed `SEARCH_ROOT` | path traversal rejected | `test_security.py` |
| 8 sample zoology files | `data/samples/zoology/` | `generate_samples.py`, E2E [2] |

### Dependencies

Pinned full environment (after `pip install -e ".[dev]"`):

```bash
pip install -r requirements.txt
pip install -e .
```

Or install from project metadata only: `pip install -e ".[dev]"`.

## GitHub

The repo is initialized locally. To publish:

```bash
git remote add origin https://github.com/YOUR_USERNAME/mcp-file-agent.git
git push -u origin main
```

To share with the reviewer: GitHub → Settings → Collaborators → add **`abin-aot`**.

## Project layout

```
src/file_search_agent/
  main.py              # Async REPL
  config.py            # Env config
  models.py            # Pydantic tool models
  agent_factory.py     # create_agent + MCP clients
  output_guard.py      # JSON / truncation guards
  mcp/local_file_search.py
data/samples/zoology/  # Non-tech zoology sample files
docs/                  # Full deployment and LLM guides
deploy/                # systemd unit example
Dockerfile             # Container image
docker-compose.yml
tests/
```

## License

MIT
