# Local File Search MCP Agent

LangChain CLI agent that combines an in-process **Local File Search** MCP (FastMCP) with the remote **Microsoft Learn** MCP.

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
# Set OPENAI_API_KEY in .env for agent E2E
```

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Required for agent E2E |
| `OPENAI_MODEL` | `openai:gpt-5.4` | LangChain model id |
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

## Tests

```bash
pytest -v
```

Unit tests for local MCP tools and `output_guard` run without an API key.

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
