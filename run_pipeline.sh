#!/usr/bin/env bash
# =============================================================================
#  run_pipeline.sh  —  Local CI/CD Quality Gate Runner
#  Runs all 10 pipeline stages in sequence and prints a final summary.
#
#  Usage (Git Bash / WSL):
#      bash run_pipeline.sh          # run all stages, stop on first failure
#      bash run_pipeline.sh --no-fail-fast   # run all stages, show full summary
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ---------------------------------------------------------------------------
# Config — auto-detect Windows (Git Bash) vs Linux (WSL / native bash)
# ---------------------------------------------------------------------------
VENV="$(pwd)/.venv"

if [[ -f "$VENV/Scripts/python.exe" ]]; then
  # Windows venv — tools have .exe extension (Git Bash called from PowerShell)
  BIN="$VENV/Scripts"
  EXT=".exe"
elif [[ -f "$VENV/Scripts/python" ]]; then
  # Windows venv — no extension (rare)
  BIN="$VENV/Scripts"
  EXT=""
else
  # Linux / WSL / macOS venv
  BIN="$VENV/bin"
  EXT=""
fi

PYTHON="$BIN/python$EXT"
PIP="$BIN/pip$EXT"
FAIL_FAST=true

# Parse --no-fail-fast flag
for arg in "$@"; do
  [[ "$arg" == "--no-fail-fast" ]] && FAIL_FAST=false
done

# ---------------------------------------------------------------------------
# Tracking arrays
# ---------------------------------------------------------------------------
declare -a STAGE_NAMES=()
declare -a STAGE_STATUS=()   # "PASS" | "FAIL" | "SKIP"
FAILED=0

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

header() {
  local num="$1" name="$2"
  echo ""
  echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo -e "${CYAN}${BOLD}  Stage $num — $name${RESET}"
  echo -e "${CYAN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

run_stage() {
  local num="$1"
  local name="$2"
  shift 2
  local cmd=("$@")

  header "$num" "$name"
  STAGE_NAMES+=("Stage $num: $name")

  echo -e "${YELLOW}▶ Running:${RESET} ${cmd[*]}"
  echo ""

  if "${cmd[@]}"; then
    echo ""
    echo -e "${GREEN}${BOLD}✅  Stage $num PASSED${RESET}"
    STAGE_STATUS+=("PASS")
  else
    echo ""
    echo -e "${RED}${BOLD}❌  Stage $num FAILED${RESET}"
    STAGE_STATUS+=("FAIL")
    FAILED=$((FAILED + 1))

    if $FAIL_FAST; then
      echo ""
      echo -e "${RED}${BOLD}🛑  Stopping pipeline (use --no-fail-fast to continue on errors)${RESET}"
      print_summary
      exit 1
    fi
  fi
}

print_summary() {
  echo ""
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo -e "${BOLD}  Pipeline Summary${RESET}"
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

  for i in "${!STAGE_NAMES[@]}"; do
    local status="${STAGE_STATUS[$i]}"
    if [[ "$status" == "PASS" ]]; then
      echo -e "  ${GREEN}✅ PASS${RESET}  ${STAGE_NAMES[$i]}"
    elif [[ "$status" == "FAIL" ]]; then
      echo -e "  ${RED}❌ FAIL${RESET}  ${STAGE_NAMES[$i]}"
    else
      echo -e "  ${YELLOW}⏭  SKIP${RESET}  ${STAGE_NAMES[$i]}"
    fi
  done

  echo ""
  local total="${#STAGE_NAMES[@]}"
  local passed=$(( total - FAILED ))

  if [[ $FAILED -eq 0 ]]; then
    echo -e "  ${GREEN}${BOLD}🎉 All $total stages passed! Pipeline is GREEN.${RESET}"
  else
    echo -e "  ${RED}${BOLD}💥 $FAILED/$total stages failed. Fix the issues above and re-run.${RESET}"
  fi
  echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

# ---------------------------------------------------------------------------
# Pre-flight: activate venv check
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}🚀 CI/CD Local Pipeline Runner${RESET}"
echo -e "   Working dir : $(pwd)"
echo -e "   Fail fast   : $FAIL_FAST"
echo -e "   Python      : $("$PYTHON" --version 2>&1)"
echo ""

if [[ ! -f "$PYTHON" ]]; then
  echo -e "${RED}ERROR: Virtual environment not found at $VENV${RESET}"
  echo "  Run:  python -m venv .venv && .venv/Scripts/pip install -r requirements.txt"
  exit 1
fi

# ---------------------------------------------------------------------------
# Stage 1 — Application starts (smoke test only — server not kept running)
# ---------------------------------------------------------------------------
header "1" "Application Smoke Test (import check)"
STAGE_NAMES+=("Stage 1: Application Smoke Test")
echo -e "${YELLOW}▶ Running:${RESET} $PYTHON -c 'from app.main import app; print(\"App imported OK\")'"
echo ""
if "$PYTHON" -c 'from app.main import app; print("  [OK] FastAPI app imported successfully")'; then
  echo ""
  echo -e "${GREEN}${BOLD}✅  Stage 1 PASSED${RESET}"
  STAGE_STATUS+=("PASS")
else
  echo -e "${RED}${BOLD}❌  Stage 1 FAILED${RESET}"
  STAGE_STATUS+=("FAIL")
  FAILED=$((FAILED + 1))
  if $FAIL_FAST; then print_summary; exit 1; fi
fi

# ---------------------------------------------------------------------------
# Stage 2 — Unit Tests
# ---------------------------------------------------------------------------
run_stage 2 "Unit Tests (pytest)" \
  "$BIN/pytest$EXT" tests/ -v

# ---------------------------------------------------------------------------
# Stage 3 — Code Formatting
# ---------------------------------------------------------------------------
run_stage 3 "Code Formatting (black)" \
  "$BIN/black$EXT" --check app/ tests/ main.py

# ---------------------------------------------------------------------------
# Stage 4 — Import Sorting
# ---------------------------------------------------------------------------
run_stage 4 "Import Sorting (isort)" \
  "$BIN/isort$EXT" --check-only app/ tests/ main.py

# ---------------------------------------------------------------------------
# Stage 5 — Linting
# ---------------------------------------------------------------------------
run_stage 5 "Linting (flake8)" \
  "$BIN/flake8$EXT" app/ tests/ main.py

# ---------------------------------------------------------------------------
# Stage 6 — Type Checking
# ---------------------------------------------------------------------------
run_stage 6 "Type Checking (mypy)" \
  "$BIN/mypy$EXT" app/

# ---------------------------------------------------------------------------
# Stage 7 — Security Scan
# ---------------------------------------------------------------------------
run_stage 7 "Security Scan (bandit)" \
  "$BIN/bandit$EXT" -r app/ -c .bandit -q

# ---------------------------------------------------------------------------
# Stage 8 — Dependency Vulnerability Scan
# ---------------------------------------------------------------------------
run_stage 8 "Dependency Vulnerability Scan (pip-audit)" \
  "$BIN/pip-audit$EXT"

# ---------------------------------------------------------------------------
# Stage 9 — Test Coverage
# ---------------------------------------------------------------------------
run_stage 9 "Test Coverage (pytest-cov)" \
  "$BIN/pytest$EXT" tests/ \
    --cov=app \
    --cov-report=term-missing \
    --cov-fail-under=80

# ---------------------------------------------------------------------------
# Stage 10 — Build / Package
# ---------------------------------------------------------------------------
run_stage 10 "Build & Package (build)" \
  "$PYTHON" -m build

# ---------------------------------------------------------------------------
# Final Summary
# ---------------------------------------------------------------------------
print_summary

[[ $FAILED -eq 0 ]] && exit 0 || exit 1
