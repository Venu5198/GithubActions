# CI/CD Error Guide — All 10 Stages

> Every stage, every common failure, exact error output, root cause, and how to fix it.

---

## ⚡ Before You Start — Activate Virtual Environment

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` in your prompt. All commands below assume the venv is active.

---

## Stage 1 — Run the Application Manually

```powershell
python main.py
# OR
uvicorn app.main:app --reload
```

### ❌ Error: `ModuleNotFoundError: No module named 'fastapi'`
**Cause:** Virtual environment not activated or dependencies not installed.  
**Fix:**
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### ❌ Error: `Address already in use` / `[WinError 10048]`
**Cause:** Port 8000 is already occupied by another process.  
**Fix:**
```powershell
# Find and kill the process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
# Then restart
uvicorn app.main:app --reload
```

### ❌ Error: `ImportError: cannot import name 'app' from 'app.main'`
**Cause:** The FastAPI `app` object is missing or misnamed in `app/main.py`.  
**Fix:** Ensure `app/main.py` contains:
```python
from fastapi import FastAPI
app = FastAPI()
```

---

## Stage 2 — Unit Tests with pytest

```powershell
pytest tests/ -v
```

### ❌ Error: `FAILED tests/test_items.py::test_create_item - AssertionError: assert 422 == 201`
**Cause:** Request body doesn't match the Pydantic schema (validation error).  
**Fix:** Check the model fields in `app/models.py`. Ensure your test sends all required fields:
```python
# Wrong — missing required field
{"name": "Widget"}

# Correct
{"name": "Widget", "price": 9.99, "quantity": 5}
```

### ❌ Error: `FAILED tests/test_users.py - assert 404 == 200`
**Cause:** Route not registered or URL path typo in test.  
**Fix:** Verify the route exists in `app/routes.py` and the test uses the correct path:
```python
# Wrong
response = client.get("/user/1")

# Correct
response = client.get("/users/1")
```

### ❌ Error: `fixture 'client' not found`
**Cause:** `conftest.py` is missing or the fixture is not defined correctly.  
**Fix:** Ensure `tests/conftest.py` exists with:
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)
```

### ❌ Error: `ModuleNotFoundError: No module named 'app'`
**Cause:** Running pytest from the wrong directory.  
**Fix:** Always run from the project root (`CI-CD/`):
```powershell
cd c:\devops\CI-CD
pytest tests/ -v
```

---

## Stage 3 — Code Formatting with Black

```powershell
# Check only (CI mode — fails if formatting needed)
black --check app/ tests/ main.py

# Auto-fix (local dev)
black app/ tests/ main.py
```

### ❌ Error: `would reformat app/routes.py` / exit code 1
**Cause:** Code is not formatted according to Black's style rules.  
**Example bad code:**
```python
# Unformatted (too long, inconsistent quotes)
def create_item(name:str,price:float,quantity:int)->dict:
    return {"name":name,"price":price,"quantity":quantity}
```
**Fix:** Run Black to auto-format:
```powershell
black app/ tests/ main.py
```
**Expected success output:**
```
All done! ✨ 🍰 ✨
3 files left unchanged.
```

### ❌ Error: `black: command not found`
**Cause:** Black not installed or venv not active.  
**Fix:**
```powershell
pip install black
```

---

## Stage 4 — Import Sorting with isort

```powershell
# Check only (CI mode)
isort --check-only app/ tests/ main.py

# Auto-fix (local dev)
isort app/ tests/ main.py
```

### ❌ Error: `ERROR: app/routes.py Imports are incorrectly sorted and/or formatted.`
**Cause:** Imports are not in the correct order (stdlib → third-party → local).  
**Example bad import order:**
```python
# Wrong order
from app.database import store
import os
from fastapi import FastAPI
```
**Fix:** Run isort to auto-fix:
```powershell
isort app/ tests/ main.py
```
**Expected success output:**
```
(no output — exit code 0)
```

### ❌ Error: isort and Black conflict with each other
**Cause:** isort not using Black-compatible profile.  
**Fix:** Ensure `pyproject.toml` has:
```toml
[tool.isort]
profile = "black"
line_length = 100
```

---

## Stage 5 — Linting with flake8

```powershell
flake8 app/ tests/ main.py
```

### ❌ Error: `app/routes.py:10:1: F401 'os' imported but unused`
**Cause:** An import exists that is never used in the file.  
**Fix:** Remove the unused import from the file.

### ❌ Error: `app/routes.py:25:101: E501 line too long (120 > 100 characters)`
**Cause:** A line exceeds the configured max line length (100).  
**Fix:** Break the line:
```python
# Too long
response = {"status": "ok", "message": "This is a very long message that exceeds the line limit set by flake8"}

# Fixed
response = {
    "status": "ok",
    "message": "This is a very long message that exceeds the line limit set by flake8",
}
```

### ❌ Error: `app/routes.py:5:1: E302 expected 2 blank lines, got 1`
**Cause:** Function/class definitions need 2 blank lines between them at module level.  
**Fix:** Add the correct number of blank lines, or just run Black which handles this automatically.

### ❌ Error: `app/routes.py:8:5: F811 redefinition of unused 'router' from line 5`
**Cause:** A variable or import is defined twice.  
**Fix:** Remove the duplicate definition.

---

## Stage 6 — Type Checking with mypy

```powershell
mypy app/
```

### ❌ Error: `app/routes.py:12: error: Argument 1 to "get_item" has incompatible type "str"; expected "int"`
**Cause:** A function is called with the wrong type.  
**Fix:** Convert or annotate correctly:
```python
# Wrong
item_id = request.query_params["id"]  # This is a str
get_item(item_id)

# Correct
item_id = int(request.query_params["id"])
get_item(item_id)
```

### ❌ Error: `error: Function is missing a return type annotation`
**Cause:** mypy strict mode requires return type hints on all functions.  
**Fix:**
```python
# Missing annotation
def get_health():
    return {"status": "ok"}

# Fixed
def get_health() -> dict:
    return {"status": "ok"}
```

### ❌ Error: `error: Cannot find implementation or library stub for module named 'fastapi'`
**Cause:** mypy can't find type stubs.  
**Fix:**
```powershell
pip install types-requests
# mypy usually handles fastapi stubs automatically via fastapi[all]
```

### ❌ Error: `error: Item "None" of "Optional[X]" has no attribute "Y"`
**Cause:** A value could be `None` but you're using it without a null check.  
**Fix:**
```python
# Risky
def get_item(item_id: int) -> dict:
    item = store.get(item_id)
    return item["name"]  # Error if item is None

# Safe
def get_item(item_id: int) -> dict | None:
    item = store.get(item_id)
    if item is None:
        return None
    return item["name"]
```

---

## Stage 7 — Security Scan with bandit

```powershell
bandit -r app/ -c .bandit
```

### ❌ Error: `[B105:hardcoded_password_string] Possible hardcoded password`
**Cause:** A string like `"password"`, `"secret"`, or `"token"` is assigned to a variable.  
**Example bad code:**
```python
SECRET_KEY = "mysecretpassword123"  # Bandit flags this
```
**Fix:** Use environment variables:
```python
import os
SECRET_KEY = os.environ.get("SECRET_KEY", "")
```

### ❌ Error: `[B608:hardcoded_sql_expressions] Possible SQL injection`
**Cause:** String formatting used to build SQL queries.  
**Example bad code:**
```python
query = "SELECT * FROM users WHERE name = '" + username + "'"
```
**Fix:** Use parameterised queries:
```python
query = "SELECT * FROM users WHERE name = ?"
cursor.execute(query, (username,))
```

### ❌ Error: `[B101:assert_used] Use of assert detected`
**Cause:** `assert` statements are removed when Python runs with `-O` flag.  
**Fix:** Replace with explicit `if/raise`:
```python
# Bad
assert user is not None

# Good
if user is None:
    raise ValueError("User not found")
```

**Expected success output:**
```
No issues identified.
```

---

## Stage 8 — Dependency Vulnerability Scan with pip-audit

```powershell
pip-audit
```

### ❌ Error: `Found X known vulnerabilities in Y packages`
**Example output:**
```
Name         Version  ID                  Fix Versions
-----------  -------  ------------------  ------------
requests     2.25.0   GHSA-j8r2-6x86-q33q 2.31.0
```
**Cause:** An installed package has a known CVE (security vulnerability).  
**Fix:** Upgrade the vulnerable package:
```powershell
pip install --upgrade requests
pip freeze > requirements.txt
```

### ❌ Error: `pip-audit: command not found`
**Fix:**
```powershell
pip install pip-audit
```

**Expected success output:**
```
No known vulnerabilities found
```

---

## Stage 9 — Test Coverage with pytest-cov

```powershell
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80
```

### ❌ Error: `FAIL Required test coverage of 80% not reached. Total coverage: 62%`
**Cause:** Not enough lines of `app/` code are exercised by your tests.  
**Fix:** Check the "Miss" column in the coverage report to see uncovered lines:
```
Name                Stmts   Miss  Cover   Missing
-------------------------------------------------
app/routes.py          45     17    62%   34-51
```
Add tests that hit lines 34–51 in `routes.py`.

### ❌ Error: `No data to report` or `CoverageWarning: No data was collected`
**Cause:** `--cov=app` points to the wrong module path, or tests didn't run.  
**Fix:**
```powershell
# Make sure you are in the project root
cd c:\devops\CI-CD
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80
```

### ❌ Error: `ModuleNotFoundError: No module named 'pytest_cov'`
**Fix:**
```powershell
pip install pytest-cov
```

**Expected success output:**
```
---------- coverage: platform win32, python 3.x ----------
Name                 Stmts   Miss  Cover
-----------------------------------------
app/__init__.py          2      0   100%
app/database.py         18      0   100%
app/main.py             12      0   100%
app/routes.py           55      0   100%
-----------------------------------------
TOTAL                   87      0   100%

Required test coverage of 80% reached. Total coverage: 100%
```

---

## Stage 10 — Build / Package Validation with build

```powershell
python -m build
```

### ❌ Error: `ERROR: Backend 'setuptools.build_meta' is not available`
**Cause:** `build` or `setuptools` not installed.  
**Fix:**
```powershell
pip install build setuptools wheel
```

### ❌ Error: `error: [Errno 2] No such file or directory: 'pyproject.toml'`
**Cause:** Running the command from the wrong directory.  
**Fix:**
```powershell
cd c:\devops\CI-CD
python -m build
```

### ❌ Error: `KeyError: 'name'` or `Missing required field 'name' in pyproject.toml`
**Cause:** `pyproject.toml` is missing required `[project]` metadata fields.  
**Fix:** Ensure `pyproject.toml` contains at minimum:
```toml
[project]
name = "cicd-demo"
version = "1.0.0"
```

**Expected success output:**
```
Successfully built cicd-demo-1.0.0.tar.gz and cicd-demo-1.0.0-py3-none-any.whl
```
Check the `dist/` folder for the generated files.

---

## 🚀 Quick Reference — Run All Stages

```powershell
# Activate venv first
.venv\Scripts\Activate.ps1

# Stage 2: Tests
pytest tests/ -v

# Stage 3: Black (check)
black --check app/ tests/ main.py

# Stage 4: isort (check)
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

## 🔧 Common Setup Fixes

| Problem | Command |
|---|---|
| venv not active | `.venv\Scripts\Activate.ps1` |
| Missing dependencies | `pip install -r requirements.txt` |
| Tool not found | `pip install <tool-name>` |
| Wrong directory | `cd c:\devops\CI-CD` |
| Port 8000 busy | `netstat -ano \| findstr :8000` then `taskkill /PID <N> /F` |

---

*This guide covers all 10 CI/CD quality gate stages for the FastAPI CI/CD Demo project.*
