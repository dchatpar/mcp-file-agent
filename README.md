# Local File Search MCP Agent

LangChain CLI agent that combines an in-process **Local File Search** MCP (FastMCP) with the remote **Microsoft Learn** MCP. The LLM uses **MiniMax** via the [OpenAI-compatible API](https://platform.minimax.io/docs/api-reference/text-openai-api).

## Features

- `search_files` — metadata filters (name, folder, extension, dates, size)
- `search_pdf_content` — PDF full-text keyword search via `pypdf`
- Microsoft Learn MCP at `https://learn.microsoft.com/api/mcp` (`streamable_http`)
- SKILL-based routing with JSON-only local results and 2000-char MS answers
- Async REPL CLI

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

LangChain uses `ChatOpenAI` with `base_url` pointing at MiniMax. `OPENAI_API_BASE_URL` is accepted as an alias for `OPENAI_BASE_URL`.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required for agent E2E (MiniMax key) |
| `OPENAI_BASE_URL` | `https://api.minimax.io/v1` | MiniMax OpenAI-compatible endpoint |
| `OPENAI_MODEL` | `MiniMax-M2.7` | Model name on MiniMax |
| `SEARCH_ROOT` | `data/samples/zoology` | Sandboxed search directory |
| `MICROSOFT_LEARN_MCP_URL` | `https://learn.microsoft.com/api/mcp` | Learn MCP endpoint |

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

**Unit tests (no API key required):**
```bash
pytest -v
# 16 passed
```

**E2E (requires `OPENAI_API_KEY` in `.env`):**
```bash
file-search-agent
# Query 1 → What PDF files are available in our system?
#   → search_files(extension=".pdf") → 4 PDFs, raw JSON ✓
# Query 2 → What is Azure Blob Storage?
#   → microsoft_docs_search → Learn MCP, ≤2000 chars ✓
```

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
tests/
```

## License

MIT
