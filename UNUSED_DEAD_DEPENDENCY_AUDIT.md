# Unused Variables, Dead Code, and Redundant Dependency Audit

## Scope

Repository: `/home/runner/work/gate-control/gate-control`

Audit inputs:
- Python source scan across `backend/**/*.py`
- Frontend/package manifest review across `frontend/package.json` and `frontend/src/**/*`
- Dependency-reference checks against:
  - `/home/runner/work/gate-control/gate-control/backend/requirements.txt`
  - `/home/runner/work/gate-control/gate-control/frontend/package.json`

---

## 1) Unused variables

### Confirmed

- No confirmed unused local variables were found in backend Python source during static scan.

### Notes

- This finding is based on an AST-based assignment/read pass across `backend/**/*.py`.
- Existing repository lint flow (`ruff`) is also configured in `/home/runner/work/gate-control/gate-control/scripts/check-all.sh` and is the canonical way to catch unused imports/locals in backend code.

---

## 2) Dead code

### Confirmed

1. **Unused placeholder module**
   - File: `/home/runner/work/gate-control/gate-control/frontend/src/lib/index.ts`
   - Contents are only a template comment, and there are no imports referencing `$lib/index` in `frontend/src`.
   - Recommendation: remove the file if not needed, or export shared symbols from it and consume them to justify keeping it.

### Candidate (manual verification recommended)

- No other backend API handlers or core functions were marked as dead code with high confidence, because route handlers/middleware are often referenced by decorators/runtime wiring rather than direct symbol calls.

---

## 3) Redundant dependencies

### Strong candidate

1. **`bcrypt==4.0.1` in backend requirements may be redundant**
   - Declared in `/home/runner/work/gate-control/gate-control/backend/requirements.txt` (line 9)
   - `passlib[bcrypt]==1.7.4` is also declared (line 8) and already pulls bcrypt support.
   - No direct `import bcrypt` references were found in backend Python files.
   - Recommendation: test removing explicit `bcrypt` pin; keep only if you intentionally pin transitive bcrypt separately for security/compliance control.

### Not redundant (despite no direct imports)

These may appear as “no direct import” but are required by runtime/configuration/tooling:

- `uvicorn` — used by runtime startup commands:
  - `/home/runner/work/gate-control/gate-control/backend/Dockerfile` line 21
  - `/home/runner/work/gate-control/gate-control/scripts/run-backend.sh` line 28
- `asyncpg` and `aiosqlite` — required by configured SQLAlchemy database URLs:
  - `/home/runner/work/gate-control/gate-control/.env.example` line 4
  - `/home/runner/work/gate-control/gate-control/backend/tests/conftest.py` lines 9, 38
- `python-multipart` — needed for multipart webhook form handling in FastAPI (even without direct import):
  - multipart webhook endpoint in `/home/runner/work/gate-control/gate-control/backend/api/webhook.py`

### Frontend candidate

1. **`@vitest/coverage-v8` may be currently unused**
   - Declared in `/home/runner/work/gate-control/gate-control/frontend/package.json` line 27
   - No coverage script exists in the same file (`scripts` section has no `--coverage`)
   - Recommendation: remove if coverage is not used in CI/local workflow, or add an explicit `test:coverage` script to make usage intentional.

---

## Suggested cleanup order

1. Remove/justify `frontend/src/lib/index.ts`.
2. Trial removal of explicit `bcrypt` from backend requirements and run full backend validation.
3. Decide whether `@vitest/coverage-v8` should be removed or activated via a coverage script.
4. Re-run repository checks:
   - `/home/runner/work/gate-control/gate-control/scripts/check-all.sh`

