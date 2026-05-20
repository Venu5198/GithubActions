# SonarQube & Trivy — Security & Quality Scanning Documentation

> **Project:** CI/CD Demo FastAPI  
> **Repository:** [Venu5198/GithubActions](https://github.com/Venu5198/GithubActions)  
> **Author:** K Venu  
> **Date:** May 2026  
> **Pipeline:** Jenkins (local) + GitHub Actions (cloud)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Objectives & Goals](#2-objectives--goals)
3. [Tools Comparison](#3-tools-comparison)
4. [Implementation — SonarQube](#4-implementation--sonarqube)
5. [Implementation — Trivy](#5-implementation--trivy)
6. [Pipeline Integration](#6-pipeline-integration)
7. [Challenges & Resolutions](#7-challenges--resolutions)
8. [Key Findings & Outcomes](#8-key-findings--outcomes)
9. [Files Created / Modified](#9-files-created--modified)
10. [Recommendations for Future Use](#10-recommendations-for-future-use)
11. [Quick Reference Commands](#11-quick-reference-commands)

---

## 1. Overview

### What is SonarQube?

SonarQube is an **open-source platform for continuous code quality and security inspection**. It analyzes your source code and produces a detailed report covering:

| Category | What it checks |
|---|---|
| 🐛 **Bugs** | Logic errors, null pointer dereferences |
| 🔒 **Security Vulnerabilities** | Injection flaws, hardcoded credentials, insecure patterns |
| 💩 **Code Smells** | Dead code, duplications, overly complex functions |
| 📊 **Coverage** | Which lines of code are not tested |
| 🏗️ **Technical Debt** | Estimated effort to fix all issues |

> **Analogy:** Think of SonarQube as a senior developer who reviews every line of your code and leaves comments — but automated, instant, and consistent.

SonarQube has two editions used in this project:
- **Self-hosted (Docker)** — runs locally, used by Jenkins
- **SonarCloud** — the cloud/SaaS version, used by GitHub Actions (free for public repos)

---

### What is Trivy?

Trivy (pronounced "Trivy") is an **open-source vulnerability scanner** created by Aqua Security. Unlike SonarQube (which scans source code), Trivy scans **built artifacts** — specifically Docker images and file systems — for known CVE (Common Vulnerabilities and Exposures) entries.

| Target | What Trivy finds |
|---|---|
| 🐳 **Docker Images** | Vulnerable OS packages (Debian, Alpine, etc.) |
| 📦 **Python/Node/Java packages** | Packages with known security advisories |
| 📁 **File System** | Embedded secrets, API keys, certificates |
| ☸️ **Kubernetes** | Misconfigured manifests |

Trivy checks against multiple vulnerability databases:
- NVD (National Vulnerability Database)
- GitHub Security Advisories
- OS vendor advisories (Debian, Ubuntu, RedHat)

> **Analogy:** Think of Trivy as an X-ray machine for your Docker image — it looks inside every layer and tells you what's broken or dangerous.

---

### How They Complement Each Other

```
┌──────────────────────────────────────────────────────────┐
│  Development Lifecycle                                   │
│                                                          │
│  Write Code → SonarQube → Build Image → Trivy → Deploy  │
│               ↑                          ↑               │
│          Scans SOURCE               Scans CONTAINER      │
│          (your Python code)         (all OS + packages)  │
└──────────────────────────────────────────────────────────┘
```

They work at **different layers** and are not interchangeable — you need both.

---

## 2. Objectives & Goals

The goal of adding SonarQube and Trivy to this project was to implement **Shift Left Security** — finding and fixing security issues as early as possible in the development lifecycle, rather than after deployment.

### Specific Goals

| # | Goal | Tool Used |
|---|---|---|
| 1 | Catch security vulnerabilities in Python source code | SonarQube |
| 2 | Enforce code quality standards across the team | SonarQube |
| 3 | Track code coverage trends over time | SonarQube + Coverage XML |
| 4 | Block merges if code quality degrades (Quality Gate) | SonarQube |
| 5 | Scan Docker images for OS-level CVEs | Trivy |
| 6 | Remove unnecessary packages from production images | Trivy findings |
| 7 | Fail pipelines on CRITICAL vulnerabilities automatically | Trivy |
| 8 | Upload vulnerability reports to GitHub Security tab | Trivy SARIF |

---

## 3. Tools Comparison

| Feature | SonarQube | Trivy |
|---|---|---|
| **What it scans** | Source code (Python, Java, JS, etc.) | Docker images, filesystems |
| **When it runs** | After tests, before Docker build | After Docker build |
| **Output format** | Web dashboard + Quality Gate | Table, JSON, SARIF |
| **Blocks pipeline?** | Yes — Quality Gate PASS/FAIL | Yes — `--exit-code 1` on CRITICAL |
| **Free version?** | ✅ Community Edition | ✅ Fully open source |
| **Server needed?** | Yes (port 9000) | No — CLI only |
| **Finds** | Code bugs, smells, security flaws | OS/package CVEs |
| **Trend tracking** | ✅ History over builds | ❌ Per-scan only |

---

## 4. Implementation — SonarQube

### 4.1 Architecture

```
┌─────────────────────────────────────────┐
│           SonarQube Server              │
│  • Runs as Docker container             │
│  • Accessible at http://localhost:9000  │
│  • Stores: projects, rules, history     │
│  • Port: 9000                           │
└──────────────┬──────────────────────────┘
               ↑  sends analysis results
┌──────────────┴──────────────────────────┐
│         sonar-scanner CLI               │
│  • Runs in Jenkins pipeline             │
│  • Reads: sonar-project.properties      │
│  • Reads: coverage.xml (from pytest)    │
│  • Authenticates with SONAR_TOKEN       │
└─────────────────────────────────────────┘
```

### 4.2 Starting SonarQube (Docker)

```powershell
# Start SonarQube Community Edition
docker run -d \
  --name sonarqube \
  -p 9000:9000 \
  -v sonarqube_data:/opt/sonarqube/data \
  sonarqube:community
```

**Flags explained:**
- `-d` — run in background (detached mode)
- `-p 9000:9000` — expose port 9000 on your PC
- `-v sonarqube_data:...` — persist data across restarts (named Docker volume)

SonarQube takes **~2 minutes** to fully start. Check status at `http://localhost:9000`.

### 4.3 First-Time Setup (One-Time Wizard)

> ⚠️ **Critical:** SonarQube 26.x requires completing the full setup wizard. Skipping any step leaves tokens invalid.

```
Step 1: Open http://localhost:9000
Step 2: Login → admin / admin
Step 3: CHANGE PASSWORD when prompted (mandatory)
         → New password: Admin@1234 (or your choice)
Step 4: Create a local project
         → Name: CI/CD Demo FastAPI
         → Key:  cicd-demo          ← exact spelling
         → Branch: main
Step 5: Select "Use global setting" → Create project
Step 6: Select "Locally" → Generate token
         → Name: scanner
         → Copy the token (starts with sqp_ or sqa_)
```

### 4.4 Project Configuration File

Created [`sonar-project.properties`](file:///c:/devops/CI-CD/sonar-project.properties) in the project root:

```properties
sonar.projectKey=cicd-demo
sonar.projectName=CI/CD Demo FastAPI
sonar.projectVersion=1.0.0

sonar.sources=app
sonar.tests=tests
sonar.inclusions=app/**/*.py
sonar.test.inclusions=tests/**/*.py

sonar.python.version=3
sonar.python.coverage.reportPaths=reports/coverage.xml,coverage.xml
sonar.sourceEncoding=UTF-8
```

**Why this file?** When sonar-scanner runs, it automatically picks up this file from the project root, so no `-D` flags need to be passed on the command line.

### 4.5 Running SonarQube Analysis Locally

```powershell
# Single-line command — avoids PowerShell backtick issues
docker run --rm `
  -v "${PWD}:/usr/src" `
  -e SONAR_HOST_URL="http://host.docker.internal:9000" `
  -e SONAR_TOKEN="YOUR_TOKEN_HERE" `
  sonarsource/sonar-scanner-cli
```

> **Note:** `host.docker.internal` is how a Docker container refers to your PC's localhost. This allows the scanner container to reach the SonarQube server running on your machine.

### 4.6 SonarQube in Jenkins Pipeline

```groovy
stage('SonarQube Analysis') {
    steps {
        withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_AUTH_TOKEN')]) {
            sh '''
                # Download sonar-scanner if not installed
                if ! command -v sonar-scanner &> /dev/null; then
                    curl -sSLo /tmp/sonar-scanner.zip \
                        https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-6.2.1.4610-linux-x64.zip
                    unzip -q /tmp/sonar-scanner.zip -d /tmp/
                    export PATH="/tmp/sonar-scanner-6.2.1.4610-linux-x64/bin:$PATH"
                fi

                sonar-scanner \
                    -Dsonar.host.url="${SONAR_HOST}" \
                    -Dsonar.token="${SONAR_AUTH_TOKEN}" \
                    -Dsonar.projectKey=cicd-demo \
                    -Dsonar.sources=app \
                    -Dsonar.tests=tests \
                    -Dsonar.python.version=3 \
                    -Dsonar.python.coverage.reportPaths=reports/coverage.xml
            '''
        }
    }
}

stage('Quality Gate — SonarQube') {
    steps {
        timeout(time: 5, unit: 'MINUTES') {
            script {
                withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_AUTH_TOKEN')]) {
                    def qgStatus = sh(
                        script: '''
                            curl -s -u "${SONAR_AUTH_TOKEN}:" \
                                "http://host.docker.internal:9000/api/qualitygates/project_status?projectKey=cicd-demo" \
                                | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['projectStatus']['status'])"
                        ''',
                        returnStdout: true
                    ).trim()

                    if (qgStatus != 'OK' && qgStatus != 'NONE') {
                        error("SonarQube Quality Gate FAILED — status: ${qgStatus}")
                    }
                }
            }
        }
    }
}
```

### 4.7 SonarQube in GitHub Actions (SonarCloud)

For GitHub Actions, SonarCloud (the hosted version) is used instead because GitHub Actions runners cannot reach a local SonarQube server.

```yaml
sonarcloud:
  name: "📊 SonarCloud Analysis"
  runs-on: ubuntu-latest
  needs: test

  steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0   # Full history needed for new code detection

    - name: Download coverage report
      uses: actions/download-artifact@v4
      with:
        name: coverage-report

    - name: SonarCloud analysis
      uses: SonarSource/sonarcloud-github-action@master
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        SONAR_TOKEN:  ${{ secrets.SONAR_TOKEN }}
```

**Required GitHub Secrets:**

| Secret Name | Value | Where to get it |
|---|---|---|
| `SONAR_TOKEN` | SonarCloud token | sonarcloud.io → My Account → Security |

### 4.8 SonarQube for IDE Extension

The **SonarQube for IDE** (VS Code extension, formerly SonarLint) provides real-time analysis without any server:

- **Standalone mode** — Works immediately, no setup, highlights issues inline as you type
- **Connected mode** — Syncs with SonarQube/SonarCloud for consistent rules

To connect to local SonarQube:
```
Ctrl+Shift+P → "SonarQube: Connect to SonarQube"
Server URL: http://localhost:9000
Token:      (from My Account → Security)
Project:    cicd-demo
```

---

## 5. Implementation — Trivy

### 5.1 How Trivy Works

```
Built Docker image (cicd-demo:sha-abc123)
              ↓
Trivy pulls vulnerability databases:
  ├── NVD (National Vulnerability Database)
  ├── GitHub Security Advisories  
  └── Debian/Ubuntu security trackers
              ↓
Scans every layer of the image:
  ├── OS packages (libssl, libc, openssl...)
  └── Python packages (fastapi, uvicorn, pydantic...)
              ↓
Outputs:
  ├── Table (human readable, in console)
  ├── JSON  (saved as build artifact)
  └── SARIF (uploaded to GitHub Security tab)
```

### 5.2 Severity Levels

| Severity | Color | Pipeline action |
|---|---|---|
| **CRITICAL** | 🔴 | **Fails pipeline** — must be fixed before merge |
| **HIGH** | 🟠 | Shown as warning — pipeline continues |
| **MEDIUM** | 🟡 | Not shown in our config |
| **LOW** | 🟢 | Not shown in our config |

### 5.3 Running Trivy Locally (No Installation Needed)

```powershell
# Trivy via Docker — scans a local image
docker run --rm `
  -v //var/run/docker.sock:/var/run/docker.sock `
  aquasec/trivy image `
  --severity HIGH,CRITICAL `
  --format table `
  cicd-demo:local
```

**Flags explained:**
- `-v //var/run/docker.sock:/var/run/docker.sock` — gives Trivy access to Docker to read images
- `--severity HIGH,CRITICAL` — only show HIGH and CRITICAL findings
- `--format table` — human-readable output
- `--exit-code 1` — fail the command if vulnerabilities are found (used in CI)

### 5.4 Trivy in Jenkins Pipeline

Embedded inside the Docker Build & Push stage:

```groovy
sh """
    # Download Trivy if not installed
    if ! command -v trivy &> /dev/null; then
        curl -sSfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
            | sh -s -- -b /usr/local/bin
    fi

    # Show all HIGH/CRITICAL CVEs (informational, doesn't fail)
    trivy image \\
        --exit-code 0 \\
        --severity HIGH,CRITICAL \\
        --format table \\
        "\${IMAGE_REPO}:\${IMAGE_TAG}"

    # Save JSON report as artifact
    mkdir -p reports
    trivy image \\
        --exit-code 1 \\
        --severity CRITICAL \\
        --format json \\
        --output reports/trivy-report.json \\
        "\${IMAGE_REPO}:\${IMAGE_TAG}"
"""
```

### 5.5 Trivy in GitHub Actions

```yaml
# Step 1: Show all HIGH/CRITICAL (informational)
- name: "Trivy — vulnerability scan (table)"
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.IMAGE_REPO }}:latest
    format: table
    exit-code: "0"
    severity: "HIGH,CRITICAL"

# Step 2: Fail if CRITICAL CVEs found
- name: "Trivy — fail on CRITICAL CVEs"
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.IMAGE_REPO }}:latest
    format: sarif
    output: trivy-results.sarif
    exit-code: "1"
    severity: "CRITICAL"
    ignore-unfixed: true    # Skip CVEs with no fix available

# Step 3: Upload results to GitHub Security tab
- name: Upload Trivy SARIF to GitHub Security
  uses: github/codeql-action/upload-sarif@v3
  if: always()
  with:
    sarif_file: trivy-results.sarif
    category: trivy
```

---

## 6. Pipeline Integration

### 6.1 Complete Pipeline Flow

```
Git Push to GitHub
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│  JENKINS PIPELINE                                        │
│                                                          │
│  Stage 1: Checkout                                       │
│  Stage 2: Setup Python (venv + dependencies)             │
│  Stage 3: Quality Gate                                   │
│           ├── Black (format check)                       │
│           ├── isort (import order)                       │
│           ├── Flake8 (linting)                           │
│           ├── mypy (type checking)                       │
│           ├── Bandit (Python security)                   │
│           └── pip-audit (dependency CVEs)                │
│  Stage 4: Tests & Coverage (75 tests, 100% coverage)     │
│  Stage 5: SonarQube Analysis ← NEW                       │
│  Stage 6: Quality Gate Check ← NEW                       │
│  Stage 7: Docker Build                                   │
│           ├── Trivy Scan ← NEW                           │
│           └── Docker Push (main branch only)             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  GITHUB ACTIONS                                          │
│                                                          │
│  Job 1: quality-gate (Black, isort, Flake8, mypy,       │
│                        Bandit, pip-audit)                │
│  Job 2: test (pytest + coverage)                         │
│  Job 3: sonarcloud ← NEW (parallel with docker-build)   │
│  Job 4: docker-build                                     │
│           ├── Build image                                │
│           ├── Trivy scan ← NEW                           │
│           └── Push to Docker Hub                         │
└──────────────────────────────────────────────────────────┘
```

### 6.2 Jenkins Credentials Required

| Credential ID | Type | Value |
|---|---|---|
| `DOCKER_HUB_USERNAME` | Secret Text | Your Docker Hub username |
| `DOCKER_HUB_TOKEN` | Secret Text | Docker Hub access token |
| `SONAR_TOKEN` | Secret Text | SonarQube token from localhost:9000 |

### 6.3 GitHub Secrets Required

| Secret Name | Value |
|---|---|
| `DOCKER_HUB_USERNAME` | Docker Hub username |
| `DOCKER_HUB_TOKEN` | Docker Hub access token |
| `SONAR_TOKEN` | SonarCloud token from sonarcloud.io |

---

## 7. Challenges & Resolutions

### Challenge 1 — PowerShell Line Continuation Splits Arguments

**Problem:** Running sonar-scanner via Docker with backtick (`` ` ``) line continuation caused `-Dsonar.projectKey=cicd-demo` to be split into two arguments: `-D` (consumed as a flag) and `sonar.projectKey=cicd-demo` (unrecognized).

```
ERROR: Unrecognized option: .projectKey=cicd-demo
```

**Root cause:** PowerShell's backtick continuation sometimes adds whitespace or mis-handles strings, causing the CLI parser to separate `-D` from the property name.

**Resolution:** Use a single-line command and rely on `sonar-project.properties` for all configuration. Since the file exists in the project root and is mounted at `/usr/src` in the container, sonar-scanner picks it up automatically with no `-D` flags needed.

```powershell
# ✅ Correct — single line, no flags
docker run --rm -v "${PWD}:/usr/src" -e SONAR_HOST_URL="..." -e SONAR_TOKEN="..." sonarsource/sonar-scanner-cli
```

---

### Challenge 2 — SonarQube Tokens Invalid (401 Unauthorized)

**Problem:** All generated tokens (`sqa_...`) returned HTTP 401 when used with the scanner. Even `admin/admin` credentials failed validation via the API.

**Root cause:** SonarQube 26.5 requires completing the full **setup wizard** through the browser. If any step is skipped (particularly the mandatory password change), the server enters a half-initialized state where tokens are created but never become valid.

**Resolution:** 
1. Stop and remove the SonarQube container and its data volume
2. Start a fresh container
3. Complete the **entire** setup wizard without skipping any step
4. Generate the token specifically during Step 6 of the wizard ("Analyze locally")

```powershell
# Reset SonarQube completely
docker stop sonarqube && docker rm sonarqube
docker volume rm sonarqube_data

# Fresh start
docker run -d --name sonarqube -p 9000:9000 -v sonarqube_data:/opt/sonarqube/data sonarqube:community
```

---

### Challenge 3 — Trivy Found Python CVEs from Dev Tools in Production Image

**Problem:** The original `Dockerfile` installed ALL packages from `requirements.txt` (including dev tools like `bandit`, `pip-audit`, `black`, `pytest`, `build`) into the production image. Trivy found HIGH CVEs in `jaraco.context` and `wheel` — packages that have no business being in a production container.

**Trivy report before fix:**
```
Python (python-pkg)
Total: 3 (HIGH: 3, CRITICAL: 0)

│ jaraco.context │ CVE-2026-23949 │ HIGH │ fixed │ 5.3.0 │ 6.1.0 │
│ wheel          │ CVE-2026-24049 │ HIGH │ fixed │ 0.45.1│ 0.46.2│
```

**Root cause:** `jaraco.context` is a transitive dependency of `setuptools`/`build`. `wheel` is a dev/packaging tool. Neither should be in a production runtime image.

**Resolution:** Created a separate `requirements-runtime.txt` containing only the three packages the app actually needs at runtime:

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
```

Updated `Dockerfile` to use `requirements-runtime.txt` in the builder stage instead of `requirements.txt`. Dev tools continue to be installed only in the CI pipeline virtual environment — never in the Docker image.

**Result:** Docker build time dropped from **36 seconds → 15 seconds**. Python CVEs from dev tools eliminated from the image.

---

### Challenge 4 — Docker Image Still Shows OS-Level CVEs

**Problem:** After removing dev tools, Trivy still reports HIGH CVEs from OpenSSL in the `python:3.11-slim` base OS.

```
│ libssl3 │ CVE-2026-28387 │ HIGH │ unfixed │ openssl: ...
```

**Root cause:** These CVEs are in the Debian OS packages bundled with `python:3.11-slim`. They are **not from our application code** and cannot be fixed by changing `requirements.txt`.

**Resolution:** These are accepted as known base-image CVEs. Our pipeline is configured to:
- **Show** HIGH CVEs as warnings (`--exit-code 0`)
- **Fail** only on CRITICAL CVEs (`--exit-code 1 --severity CRITICAL`)
- Use `--ignore-unfixed` to suppress CVEs with no available fix

For long-term mitigation, see [Recommendations](#10-recommendations-for-future-use).

---

## 8. Key Findings & Outcomes

### 8.1 Trivy Scan Results Summary

| Image | Python CVEs (HIGH) | OS CVEs (HIGH) | CRITICAL | Pipeline Result |
|---|---|---|---|---|
| `cicd-demo:local` (original) | 3 (dev tools) | 4 (OpenSSL) | **0** | ✅ PASS |
| `cicd-demo:fixed` (runtime only) | **0** (eliminated) | 4 (OpenSSL) | **0** | ✅ PASS |

**Most significant finding:** The production Docker image was unnecessarily packaging ~80 Python packages (including `bandit`, `pytest`, `pip-audit`, `black`, etc.) that exist only for CI/quality purposes. This:
- Increased the image attack surface needlessly
- Added 60+ extra packages (and their CVEs) to the container
- Made the image 2x slower to build

### 8.2 SonarQube Expected Findings

Based on the code quality measures already in place (100% test coverage, Black/isort/Flake8/mypy all passing), SonarQube analysis is expected to confirm:

| Metric | Expected Result |
|---|---|
| Bugs | 0 |
| Vulnerabilities | 0 |
| Security Hotspots | 0 |
| Code Smells | Minimal |
| Coverage | 100% |
| Quality Gate | ✅ PASSED |
| Duplications | < 5% |

### 8.3 Infrastructure Improvements Made

As a direct result of the Trivy findings:

| Change | Impact |
|---|---|
| Created `requirements-runtime.txt` | Separates prod vs dev dependencies |
| Updated `Dockerfile` to use runtime deps only | Eliminates dev-tool CVEs from image |
| Updated `.dockerignore` | Prevents tests, CI configs, reports from entering build context |
| Reduced image packages: 80+ → 19 | Smaller attack surface, faster builds |

---

## 9. Files Created / Modified

| File | Action | Purpose |
|---|---|---|
| [`sonar-project.properties`](file:///c:/devops/CI-CD/sonar-project.properties) | ✅ Created | SonarQube/SonarCloud project configuration |
| [`requirements-runtime.txt`](file:///c:/devops/CI-CD/requirements-runtime.txt) | ✅ Created | Runtime-only dependencies for Docker image |
| [`Dockerfile`](file:///c:/devops/CI-CD/Dockerfile) | ✏️ Modified | Uses `requirements-runtime.txt` instead of full dev deps |
| [`.dockerignore`](file:///c:/devops/CI-CD/.dockerignore) | ✏️ Modified | Added tests/, reports/, jenkins/, sonar configs |
| [`Jenkinsfile`](file:///c:/devops/CI-CD/Jenkinsfile) | ✏️ Modified | Added SonarQube Analysis + Quality Gate + Trivy stages |
| [`.github/workflows/ci-cd.yml`](file:///c:/devops/CI-CD/.github/workflows/ci-cd.yml) | ✏️ Modified | Added sonarcloud job + Trivy steps in docker-build |

---

## 10. Recommendations for Future Use

### 10.1 Fix OS-Level OpenSSL CVEs

The remaining HIGH CVEs (OpenSSL) come from `python:3.11-slim`. Options:

```dockerfile
# Option A: Pin to a specific python image with latest security patches
FROM python:3.11.12-slim   # Pin to specific patched version

# Option B: Use distroless image (smallest possible attack surface)
FROM gcr.io/distroless/python3-debian12

# Option C: Add OS update to Dockerfile runtime stage
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
```

### 10.2 Persist SonarQube with PostgreSQL

The current setup uses SonarQube's built-in H2 database which is for **evaluation only** and warns:
```
WARN: H2 database should be used for evaluation purpose only.
```

For team/production use, switch to PostgreSQL:

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: sonar
      POSTGRES_PASSWORD: sonar
      POSTGRES_DB: sonarqube

  sonarqube:
    image: sonarqube:community
    depends_on: [db]
    environment:
      SONAR_JDBC_URL: jdbc:postgresql://db:5432/sonarqube
      SONAR_JDBC_USERNAME: sonar
      SONAR_JDBC_PASSWORD: sonar
    ports:
      - "9000:9000"
```

### 10.3 Set SonarQube Quality Gate Thresholds

Configure custom Quality Gate rules in SonarQube UI:
```
Administration → Quality Gates → Create Gate → Add Conditions:

  Coverage < 80%         → FAIL
  New Bugs > 0           → FAIL  
  New Vulnerabilities > 0 → FAIL
  New Code Smells > 10   → FAIL
  Security Hotspots reviewed < 100% → FAIL
```

### 10.4 Add Trivy for Filesystem Scanning

Beyond image scanning, also scan the repository filesystem for embedded secrets:

```yaml
- name: "Trivy — filesystem scan for secrets"
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: fs
    scan-ref: .
    format: table
    exit-code: "1"
    severity: "CRITICAL,HIGH"
    scanners: "secret"
```

### 10.5 Schedule Nightly Trivy Scans

Since new CVEs are discovered daily, schedule automatic rescans even without code changes:

```yaml
# .github/workflows/nightly-security.yml
on:
  schedule:
    - cron: '0 1 * * *'   # Every day at 1 AM UTC
```

### 10.6 Pin sonar-scanner and Trivy Versions

For reproducibility, pin the versions in CI:

```groovy
// Jenkinsfile — pin sonar-scanner version
SCANNER_VERSION = "6.2.1.4610"

// GitHub Actions — pin trivy-action version
uses: aquasecurity/trivy-action@v0.30.0   // not @master
```

### 10.7 Upgrade Python Base Image Regularly

Set a reminder to check for newer `python:3.11-slim` builds:

```powershell
# Check current image digest
docker inspect python:3.11-slim --format '{{.RepoDigests}}'

# Pull latest to get OS security patches
docker pull python:3.11-slim
docker build -t cicd-demo:local .   # Rebuild
docker run aquasec/trivy image cicd-demo:local  # Rescan
```

---

## 11. Quick Reference Commands

### SonarQube

```powershell
# Start SonarQube
docker run -d --name sonarqube -p 9000:9000 -v sonarqube_data:/opt/sonarqube/data sonarqube:community

# Stop SonarQube
docker stop sonarqube

# Check SonarQube status
Invoke-WebRequest -Uri "http://localhost:9000/api/system/status" -UseBasicParsing | Select-Object -ExpandProperty Content

# Validate a token
Invoke-WebRequest -Uri "http://localhost:9000/api/authentication/validate" -Headers @{Authorization = "Bearer YOUR_TOKEN"} -UseBasicParsing | Select-Object -ExpandProperty Content

# Run scanner (uses sonar-project.properties automatically)
docker run --rm -v "${PWD}:/usr/src" -e SONAR_HOST_URL="http://host.docker.internal:9000" -e SONAR_TOKEN="YOUR_TOKEN" sonarsource/sonar-scanner-cli

# Reset SonarQube completely (fresh start)
docker stop sonarqube; docker rm sonarqube; docker volume rm sonarqube_data
```

### Trivy

```powershell
# Scan a local Docker image
docker run --rm -v //var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --severity HIGH,CRITICAL --format table cicd-demo:local

# Scan and save JSON report
docker run --rm -v //var/run/docker.sock:/var/run/docker.sock -v "${PWD}/reports:/reports" aquasec/trivy image --format json --output /reports/trivy.json cicd-demo:local

# Scan filesystem for secrets
docker run --rm -v "${PWD}:/src" aquasec/trivy fs /src --scanners secret

# Check Trivy version
docker run --rm aquasec/trivy --version
```

### Docker Image

```powershell
# Build image (runtime-only deps)
docker build -t cicd-demo:local .

# Build and scan in sequence
docker build -t cicd-demo:local .
docker run --rm -v //var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --severity HIGH,CRITICAL cicd-demo:local

# Compare image sizes
docker images cicd-demo
```

---

*This documentation was created as part of the CI/CD Demo FastAPI project. For questions, refer to the [jenkins/README.md](file:///c:/devops/CI-CD/jenkins/README.md) for Jenkins-specific setup instructions.*
