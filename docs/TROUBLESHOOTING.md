# Troubleshooting

Symptom ? cause ? fix reference consolidated from project development and QA history.

---

## Quick reference table

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| E2E appears stuck / no progress | Buffered stdout | Run with `python -u scripts/e2e_verify.py`; Dockerfile sets `PYTHONUNBUFFERED=1` |
| Invalid JSON from local query | Model wrapped tool JSON in prose | `output_guard` prefers last local tool JSON; verify `SKILL.md` routing; run `pytest tests/test_output_guard.py` |
| OpenAI HTTP 400 on `extra_body` | MiniMax params sent to OpenAI | Set `OPENAI_BASE_URL=https://api.openai.com/v1`; `_is_minimax_provider()` omits `extra_body` for non-MiniMax URLs |
| Learn MCP deprecation warning (SSE) | Old transport docs | Already on `streamable_http`; safe to ignore if tools load |
| E2E lists 5 files not 8 | Sample data not generated or legacy `.xlsx` duplicate | Run `./install.py` or `python scripts/generate_samples.py`; delete `species_count_2024.xlsx` if present |
| Excel sample won't open | Legacy misnamed `.xlsx` (xlwt binary) | Use `species_count_2024.xls`; regenerate samples |
| Fresh clone: `install.py` fails on dotenv | Deps not installed yet | Installer creates venv first; re-run after Phase 3 or use `--skip-e2e` |
| Path traversal / access denied | File outside `SEARCH_ROOT` | Use paths relative to sandbox; set `SEARCH_ROOT` correctly |
| `OPENAI_API_KEY is required` | Missing or empty `.env` | Copy `.env.example` or `.env.openai.example`, set key, restart |
| Agent create timeout (60s) | Network or MCP unreachable | Check outbound HTTPS to Learn MCP and LLM API |
| Query timeout (120s) | Slow model or tool loop | Retry; check provider status; reduce query complexity |
| Out-of-scope query returns prose | Routing miss | Expected JSON: `{"error":"Query out of scope..."}`; check E2E [5/5] and `routing.py` |
| MS answer exceeds 2000 chars | Guard not applied | Verify `guard_agent_output` in `main.py` / E2E; set `MS_ANSWER_MAX_CHARS` |
| `.env` accidentally committed | Git add oversight | Remove from index: `git rm --cached .env`; rotate keys; see `tests/test_security.py` |
| Docker can't find samples | Volume mount mismatch | Align `SEARCH_ROOT` in `.env` with compose volume path |
| systemd service exits immediately | Interactive REPL without TTY | Use batch `e2e_verify.py` ExecStart or run interactively over SSH with `-t` |
| pytest learn MCP failures | No network in CI | Expected in air-gapped CI; run learn tests locally or mark optional |
| Ruff E402 on scripts | Imports after path setup | Already ignored in `pyproject.toml` for `e2e_verify.py` and `spotcheck_assignment.py` |

---

## E2E appears stuck

**Symptoms:** Running `python scripts/e2e_verify.py` shows no output for a long time.

**Cause:** Python stdout buffering when not attached to a TTY.

**Fix:**

```bash
python -u scripts/e2e_verify.py
```

Progress lines `[1/5]` through `[5/5]` should appear within seconds of agent creation (~1–2 min total runtime with API calls).

---

## Invalid JSON from local file query

**Symptoms:** Local search returns markdown fences or explanatory text instead of raw JSON.

**Cause:** LLM paraphrased tool output instead of returning tool JSON verbatim.

**Fix:**

1. Confirm `output_guard.py` is active (`guard_agent_output` with `messages=` in `main.py` and `e2e_verify.py`).
2. The guard extracts JSON from tool messages when `used_local_tools` is true.
3. Re-run: `pytest tests/test_output_guard.py tests/test_agent_routing.py -v`

---

## OpenAI 400 on `extra_body`

**Symptoms:** Error mentioning unknown or unsupported parameter when using OpenAI.

**Cause:** MiniMax-specific `reasoning_split` / `thinking` sent to OpenAI API.

**Fix:**

1. Set `OPENAI_BASE_URL=https://api.openai.com/v1` (must **not** contain `minimax`).
2. Confirm `agent_factory._is_minimax_provider()` returns `False` for your URL.
3. Run `pytest tests/test_agent_factory.py -v`

See [LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md).

---

## Learn MCP warnings

**Symptoms:** Deprecation notice about SSE transport.

**Cause:** Historical assignment text referenced SSE; this repo uses `streamable_http` in `agent_factory.py`.

**Fix:** No action required if Learn tools load and E2E [4/5] passes.

---

## Wrong file count in list_all_files

**Symptoms:** E2E check [2/5] expects 8 files but finds fewer.

**Cause:** `data/samples/zoology/` not populated.

**Fix:**

```bash
python scripts/generate_samples.py
ls data/samples/zoology/ | wc -l   # expect 8
```

---

## Path traversal errors

**Symptoms:** Tool error when reading/searching files; security test failures.

**Cause:** Requested path escapes `SEARCH_ROOT` sandbox.

**Fix:**

- Use filenames or paths relative to the sandbox root.
- Set `SEARCH_ROOT` to the directory containing your corpus.
- Run `pytest tests/test_security.py -v`

---

## API key and auth failures

**Symptoms:** `401` / `403` from LLM API; `ValueError: OPENAI_API_KEY is required`.

**Fix:**

1. Verify `.env` exists at project root and is loaded (`config.py` calls `load_dotenv()`).
2. Match key to provider (MiniMax key for MiniMax URL, OpenAI key for OpenAI URL).
3. Rotate key if exposed; never commit `.env`.

---

## Docker-specific issues

| Symptom | Fix |
|---------|-----|
| `.env` not loaded | Ensure `env_file: .env` in `docker-compose.yml` and file exists beside compose file |
| Empty search results | Mount host directory: `volumes: - ./data/samples/zoology:/app/data/samples/zoology:ro` |
| E2E script not found | Rebuild image after adding `scripts/` to Dockerfile context |

---

## Getting help

1. Run the verification gate from [DEPLOYMENT.md](DEPLOYMENT.md) Phase 3.
2. Check [COMPLIANCE_REPORT.md](COMPLIANCE_REPORT.md) for expected behavior baseline.
3. Review recent git commits (`6b2d449` … `4c26bd0`) for context on fixes.
