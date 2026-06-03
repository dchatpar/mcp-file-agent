# Operations Guide

Day-2 operations for the Local File Search MCP Agent: key rotation, corpus changes, upgrades, and CI suggestions.

---

## Rotate API keys

1. Generate a new key in your provider console (MiniMax or OpenAI).
2. Update `OPENAI_API_KEY` in `.env` (or orchestrator secret store).
3. Revoke the old key after verifying the new one works.
4. Restart the running instance:
   - **CLI:** exit and re-run `file-search-agent`
   - **Docker:** `docker compose run --rm file-search-agent` (picks up new `.env`)
   - **systemd:** `sudo systemctl restart file-search-agent`
5. Run verification:

```bash
python -u scripts/e2e_verify.py
```

See [LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md) for provider-specific key sources.

---

## Change search corpus (`SEARCH_ROOT`)

1. Set `SEARCH_ROOT` to the new directory (use **absolute paths** on servers):

   ```bash
   SEARCH_ROOT=/var/lib/file-search/production-corpus
   ```

2. Populate the directory with allowed files (PDF, docx, xls, txt, jpg, etc.).
3. Or regenerate sample data for dev/test:

   ```bash
   python scripts/generate_samples.py
   ```

4. Verify listing:

   ```bash
   pytest tests/test_local_mcp.py -v -k list_all_files
   python -u scripts/e2e_verify.py   # check [2/5] lists expected count
   ```

5. For Docker, update the volume mount in `docker-compose.yml` or set `SEARCH_ROOT` env to match the mounted path inside the container (`/app/data/samples/zoology` by default).

---

## Upgrade dependencies

```bash
source .venv/bin/activate
pip install -e ".[dev]" --upgrade
pip freeze > requirements.txt   # optional: refresh lock snapshot
```

**Post-upgrade gate:**

```bash
ruff check src tests scripts
pytest -v
python -u scripts/e2e_verify.py        # requires API key
python -u scripts/spotcheck_assignment.py
```

Pin major versions in `pyproject.toml` if a regression appears after upgrade.

---

## Regenerate sample data

```bash
python scripts/generate_samples.py
```

Expected output: 8 files in `data/samples/zoology/` covering 5 extensions (.pdf, .docx, .xls, .txt, .jpg).

---

## Run QA scripts

| Script | Purpose | API key |
|--------|---------|---------|
| `pytest -v` | Unit + integration tests | No (except learn MCP live tests may skip) |
| `ruff check src tests scripts` | Lint | No |
| `python -u scripts/e2e_verify.py` | 5-check E2E | Yes |
| `python -u scripts/spotcheck_assignment.py` | 3-query assignment check | Yes |

Always use `python -u` for E2E and spot-check so progress lines flush immediately.

---

## Logs and exit codes

| Context | Logs | Exit code |
|---------|------|-----------|
| CLI REPL | stdout (guarded responses) | 0 on clean exit; Ctrl+C |
| `e2e_verify.py` | `[1/5]` ù `[5/5]` progress | 0 = all pass; non-zero = failure |
| `spotcheck_assignment.py` | PASS/FAIL per query | 0 = 3/3 pass |
| systemd | `journalctl -u file-search-agent` | Per service config |

---

## CI suggestion (GitHub Actions)

Document-only sample ù lint + pytest on every push; optional E2E on manual workflow with secret.

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: python scripts/generate_samples.py
      - run: ruff check src tests scripts
      - run: pytest -v

  e2e-manual:
    if: github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: python scripts/generate_samples.py
      - run: python -u scripts/e2e_verify.py
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          OPENAI_BASE_URL: ${{ secrets.OPENAI_BASE_URL }}
          OPENAI_MODEL: ${{ secrets.OPENAI_MODEL }}
```

Store `OPENAI_API_KEY` (and optional base URL / model) in repository secrets. Do not run E2E on every PR unless you accept API cost and flakiness from rate limits.

---

## Related

- [DEPLOYMENT.md](DEPLOYMENT.md) ù Initial deploy
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) ù Common failures
- [LLM_PROVIDER_GUIDE.md](LLM_PROVIDER_GUIDE.md) ù Provider migration
