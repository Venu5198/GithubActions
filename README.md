# CI/CD Demo — FastAPI Backend

A **sample FastAPI backend** purpose-built to demonstrate every stage of a
professional CI/CD quality-gate pipeline — run locally before code ever reaches
GitHub Actions.

---

## Project Structure

```
CI-CD/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app factory
│   ├── models.py      # Pydantic request/response schemas
│   ├── database.py    # In-memory CRUD store
│   └── routes.py      # All API route handlers
├── tests/
│   ├── conftest.py    # Shared fixtures (TestClient, store reset)
│   ├── test_health.py # Health / utility endpoint tests
│   ├── test_items.py  # Item CRUD tests
│   └── test_users.py  # User CRUD tests
├── main.py            # Uvicorn entry-point
├── pyproject.toml     # Tool config (black, isort, mypy, pytest, coverage, build)
├── .flake8            # Flake8 config
├── .bandit            # Bandit config
└── requirements.txt   # All dependencies
```

---

## API Endpoints

| Method | Path            | Description               |
|--------|-----------------|---------------------------|
| GET    | `/`             | Welcome / root            |
| GET    | `/health`       | Health check              |
| POST   | `/echo`         | Echo with transformations |
| GET    | `/items`        | List items (filterable)   |
| GET    | `/items/{id}`   | Get item by ID            |
| POST   | `/items`        | Create item               |
| PUT    | `/items/{id}`   | Update item               |
| DELETE | `/items/{id}`   | Delete item               |
| GET    | `/users`        | List users                |
| GET    | `/users/{id}`   | Get user by ID            |
| POST   | `/users`        | Create user               |
| DELETE | `/users/{id}`   | Delete user               |

Interactive docs → **http://localhost:8000/docs**

---

## CI/CD Pipeline — Stage-by-Stage Commands

Activate the virtual environment first:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### Stage 1 — Run the Application Manually

```powershell
python main.py
# OR
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** to interact with the API.

---

### Stage 2 — Unit Tests with pytest

```powershell
pytest tests/ -v
```

**What it does:** Runs all 40 test cases across three test files.  
**Pass criteria:** All tests green.

---

### Stage 3 — Code Formatting with Black

```powershell
# Check (CI mode — no changes)
black --check app/ tests/ main.py

# Auto-fix (local dev)
black app/ tests/ main.py
```

**What it does:** Enforces consistent code style (line length 100, Python 3.11 target).  
**Pass criteria:** Exit code 0 — "All done! ✨ 🍰 ✨"

---

### Stage 4 — Import Sorting with isort

```powershell
# Check (CI mode)
isort --check-only app/ tests/ main.py

# Auto-fix (local dev)
isort app/ tests/ main.py
```

**What it does:** Sorts and groups imports (stdlib → third-party → local) using the Black-compatible profile.  
**Pass criteria:** Exit code 0, no output.

---

### Stage 5 — Linting with flake8

```powershell
flake8 app/ tests/ main.py
```

**What it does:** Checks PEP 8 compliance, detects unused imports, and flags complexity issues.  
**Pass criteria:** No output, exit code 0.

---

### Stage 6 — Type Checking with mypy

```powershell
mypy app/
```

**What it does:** Performs static analysis in strict mode — catches type mismatches before runtime.  
**Pass criteria:** "Success: no issues found in N source files"

---

### Stage 7 — Security Scan with bandit

```powershell
bandit -r app/ -c .bandit
```

**What it does:** Scans source code for common security vulnerabilities (hardcoded passwords, SQL injection, etc.).  
**Pass criteria:** "No issues identified."

---

### Stage 8 — Dependency Vulnerability Scan with pip-audit

```powershell
pip-audit
```

**What it does:** Checks every installed package against the PyPI Advisory Database for known CVEs.  
**Pass criteria:** "No known vulnerabilities found"

---

### Stage 9 — Test Coverage with pytest-cov

```powershell
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80
```

**What it does:** Measures line coverage of the `app/` package and fails if under 80%.  
**Pass criteria:** ≥ 80% total coverage (this project achieves **100%**).

---

### Stage 10 — Build / Package Validation with build

```powershell
python -m build
```

**What it does:** Produces a source distribution (`.tar.gz`) and a wheel (`.whl`) in the `dist/` folder.  
**Pass criteria:** "Successfully built cicd-demo-1.0.0.tar.gz and cicd-demo-1.0.0-py3-none-any.whl"

---

## Quick Reference — Run All Stages

```powershell
# Stage 2: Tests
pytest tests/ -v

# Stage 3: Black
black --check app/ tests/ main.py

# Stage 4: isort
isort --check-only app/ tests/ main.py

# Stage 5: flake8
flake8 app/ tests/ main.py

# Stage 6: mypy
mypy app/

# Stage 7: bandit
bandit -r app/ -c .bandit

# Stage 8: pip-audit
pip-audit

# Stage 9: Coverage
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80

# Stage 10: Build
python -m build
```

---

## License

MIT
