# Unused Variables, Dead Code, and Redundant Dependency Audit (re-run)

## Scope

Repository: `/home/runner/work/gate-control/gate-control`  
Re-run against latest branch state at commit `d1bc72d`.

Inputs used:
- static Python AST scan of `backend/**/*.py` for assigned-vs-read local variables
- dependency/reference scan for:
  - `/home/runner/work/gate-control/gate-control/backend/requirements.txt`
  - `/home/runner/work/gate-control/gate-control/frontend/package.json`
- dead-code/reference checks in frontend source, especially `$lib` exports

Validation attempt:
- Ran `/home/runner/work/gate-control/gate-control/scripts/check-all.sh`
- Current environment lacks `ruff` (`/usr/bin/python3: No module named ruff`), so full lint/test flow did not complete here.

---

## 1) Unused variables

### Confirmed

- No confirmed unused local variables found in `backend/**/*.py` during AST scan.

### Notes

- Canonical lint path remains `/home/runner/work/gate-control/gate-control/scripts/check-all.sh`, which includes backend `ruff` checks.
- In this environment, `ruff` is not installed, so this report relies on static scan + manual review evidence.

---

## 2) Dead code

### Confirmed

1. **Unused frontend placeholder file**
   - File: `/home/runner/work/gate-control/gate-control/frontend/src/lib/index.ts`
   - File contains only template comment text.
   - No `$lib/index` (or direct `$lib`) imports found in `frontend/src`.
   - Recommendation: remove file if not intended for near-term exports.

### No additional high-confidence dead code found

- Backend route handlers and helpers are mostly wired by decorators/runtime, so absence of direct symbol references is not sufficient to mark them dead without deeper runtime trace data.

---

## 3) Redundant dependencies

### Strong candidate

1. **`bcrypt==4.0.1` may be redundant in backend**
   - Declared in `/home/runner/work/gate-control/gate-control/backend/requirements.txt` line 9.
   - `passlib[bcrypt]==1.7.4` is also declared (line 8).
   - No direct `import bcrypt` found in backend Python files.
   - Recommendation: remove explicit `bcrypt` only if your policy does not require pinning transitive security-sensitive packages separately.

### Explicitly not redundant (even if no direct import)

- **`uvicorn`**: used as runtime entrypoint in:
  - `/home/runner/work/gate-control/gate-control/backend/Dockerfile` line 21
  - `/home/runner/work/gate-control/gate-control/scripts/run-backend.sh` line 28
- **`python-multipart`**: required by FastAPI multipart form parsing used in webhook endpoint (`/home/runner/work/gate-control/gate-control/backend/api/webhook.py`).
- **`asyncpg` / `aiosqlite`**: both are used via SQLAlchemy connection URLs in environment/test paths (e.g. `/home/runner/work/gate-control/gate-control/backend/tests/conftest.py` lines 9 and 38).
- **`@vitest/coverage-v8`**: currently used with Vitest coverage provider (`provider: 'v8'`) in `/home/runner/work/gate-control/gate-control/frontend/vitest.config.ts` lines 13-15.

---

## Recommended follow-up

1. Remove `frontend/src/lib/index.ts` if no imminent `$lib` exports are planned.
2. Trial removal of backend explicit `bcrypt` pin, then run full checks in a provisioned environment:
   - `/home/runner/work/gate-control/gate-control/scripts/check-all.sh`
3. Keep `@vitest/coverage-v8` (it is actively referenced by Vitest config).
