# LLM Provider Guide — MiniMax ? OpenAI

This agent uses LangChain's `ChatOpenAI` against an **OpenAI-compatible HTTP API**. The repo defaults to **MiniMax**; you can switch to **OpenAI** by changing environment variables only (plus one code behavior: MiniMax-specific `extra_body` is applied conditionally in `agent_factory.py`).

---

## Current defaults

From `config.py` and `.env.example`:

| Variable | Default |
|----------|---------|
| `OPENAI_BASE_URL` | `https://api.minimax.io/v1` |
| `OPENAI_MODEL` | `MiniMax-M2.7` |
| `OPENAI_API_KEY` | (required, no default) |

MiniMax requires extra API parameters to disable thinking/reasoning split. The agent passes these **only when** `"minimax"` appears in `OPENAI_BASE_URL` (see `_is_minimax_provider()` in `agent_factory.py`).

---

## Side-by-side comparison

| Aspect | MiniMax (default) | OpenAI |
|--------|-------------------|--------|
| Base URL | `https://api.minimax.io/v1` | `https://api.openai.com/v1` |
| Model example | `MiniMax-M2.7` | `gpt-4o`, `gpt-4.1`, or account-specific GPT-5.x id |
| API key | MiniMax platform key | OpenAI platform key |
| `extra_body` | Yes (`reasoning_split`, `thinking: disabled`) | **Omitted** (unsupported on OpenAI) |
| Env template | `.env.example` | `.env.openai.example` |
| Typical latency | ~1–2 min for full E2E | Varies by model/tier |

---

## Migrate to OpenAI (step-by-step)

| Step | Action |
|------|--------|
| 1 | Obtain an OpenAI API key; **never commit** `.env` |
| 2 | Copy the OpenAI profile: `cp .env.openai.example .env` (or edit existing `.env`) |
| 3 | Set `OPENAI_BASE_URL=https://api.openai.com/v1` |
| 4 | Set `OPENAI_MODEL` to your model id (e.g. `gpt-4o`) |
| 5 | Set `OPENAI_API_KEY` to your OpenAI key |
| 6 | Restart CLI or re-run verification scripts |

### OpenAI `.env` block (copy-paste)

```bash
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o
SEARCH_ROOT=data/samples/zoology
MICROSOFT_LEARN_MCP_URL=https://learn.microsoft.com/api/mcp
MS_ANSWER_MAX_CHARS=2000
```

### MiniMax `.env` block (rollback reference)

```bash
OPENAI_API_KEY=sk-your-minimax-key-here
OPENAI_BASE_URL=https://api.minimax.io/v1
OPENAI_MODEL=MiniMax-M2.7
SEARCH_ROOT=data/samples/zoology
MICROSOFT_LEARN_MCP_URL=https://learn.microsoft.com/api/mcp
MS_ANSWER_MAX_CHARS=2000
```

---

## Environment variable reference

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes (for E2E/CLI) | API key for the configured provider |
| `OPENAI_BASE_URL` | No | OpenAI-compatible endpoint; defaults to MiniMax |
| `OPENAI_API_BASE_URL` | No | Alias for `OPENAI_BASE_URL` |
| `OPENAI_MODEL` | No | Model id; default `MiniMax-M2.7` |
| `SEARCH_ROOT` | No | Sandboxed search directory |
| `FILE_SEARCH_ROOT` | No | Alias for `SEARCH_ROOT` |
| `MICROSOFT_LEARN_MCP_URL` | No | Learn MCP endpoint |
| `MS_ANSWER_MAX_CHARS` | No | Max chars for MS answers (default 2000) |

---

## Code behavior: conditional `extra_body`

In `agent_factory.py`:

```python
def _is_minimax_provider(base_url: str = OPENAI_BASE_URL) -> bool:
    return "minimax" in base_url.lower()
```

When `_is_minimax_provider()` is true, `ChatOpenAI` receives:

```python
extra_body={
    "reasoning_split": True,
    "thinking": {"type": "disabled"},
}
```

For OpenAI (`api.openai.com`), `extra_body` is **not** passed — avoiding HTTP 400 "unsupported parameter" errors.

Unit tests in `tests/test_agent_factory.py` assert this behavior.

---

## Verification checklist

After changing provider settings:

```bash
source .venv/bin/activate
pip install -e ".[dev]"

# Fast unit checks (no live API for factory tests if mocked; routing/guard need no key)
pytest tests/test_agent_factory.py tests/test_agent_routing.py tests/test_output_guard.py -v

# Full unit suite
pytest -v

# Live E2E (requires OPENAI_API_KEY in .env)
python -u scripts/e2e_verify.py

# Assignment spot-check (3 queries)
python -u scripts/spotcheck_assignment.py

# Interactive smoke
file-search-agent
```

**Success criteria:**

- All pytest pass (34 total)
- E2E reports 5/5 PASSED
- Spot-check reports 3/3 PASSED
- Local queries return valid JSON; MS queries return prose ? 2000 chars

---

## Rollback to MiniMax

1. Restore MiniMax values in `.env` (see block above) or `cp .env.example .env` and re-enter your key.
2. Ensure `OPENAI_BASE_URL` contains `minimax` so `extra_body` is re-enabled.
3. Re-run `python -u scripts/e2e_verify.py`.

No code changes needed for rollback — only env vars.

---

## Security

- **Never commit `.env`** — it is listed in `.gitignore`; verified by `tests/test_security.py`.
- **Rotate keys** if exposed in chat, logs, or screenshots.
- Use **restricted keys** where your provider supports them.
- On servers, set `.env` permissions to `600` and owned by the service user.

See also [OPERATIONS.md](OPERATIONS.md) for key rotation and [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for provider-specific errors.

---

## When to change code vs env only

| Change | Env only | Code change |
|--------|----------|-------------|
| Switch MiniMax ? OpenAI | Yes | No (conditional `extra_body` already handles this) |
| New OpenAI model id | Yes (`OPENAI_MODEL`) | No |
| Custom OpenAI-compatible proxy | Yes (`OPENAI_BASE_URL`) | Maybe — if URL doesn't contain `minimax`, `extra_body` is skipped automatically |
| New provider with different extra params | Maybe | Yes — extend `_is_minimax_provider()` or add provider-specific branches |

---

## Related

- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) — Architecture and compliance
- [DEPLOYMENT.md](DEPLOYMENT.md) — Deploy with either provider
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — OpenAI 400 on `extra_body`, E2E hangs, JSON issues
