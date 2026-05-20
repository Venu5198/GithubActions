# Jenkins Setup Guide — CI/CD Demo FastAPI App

This guide walks you through configuring Jenkins to run the same CI/CD pipeline as GitHub Actions.

---

## Prerequisites

### On the Jenkins Server

| Requirement | Minimum Version | Check Command |
|---|---|---|
| Jenkins | 2.440+ | `jenkins --version` |
| Python | 3.11 | `python3 --version` |
| pip | latest | `pip --version` |
| Docker | 24+ | `docker --version` |
| Git | 2.x | `git --version` |

> **Important:** Make sure the Jenkins user (`jenkins`) has permission to run Docker:
> ```bash
> sudo usermod -aG docker jenkins
> sudo systemctl restart jenkins
> ```

---

## Step 1 — Install Required Jenkins Plugins

Go to **Manage Jenkins → Plugins → Available plugins** and install:

| Plugin | Purpose |
|---|---|
| **Pipeline** | Core pipeline support (usually pre-installed) |
| **Git Plugin** | Clone repositories |
| **GitHub Plugin** | GitHub webhook integration |
| **HTML Publisher Plugin** | Publish coverage HTML reports |
| **JUnit Plugin** | Display test results trend graphs |
| **Docker Pipeline** | Docker commands in pipelines |
| **Credentials Binding Plugin** | Inject secrets securely |
| **Timestamper** | Add timestamps to build logs |

After installing, restart Jenkins.

---

## Step 2 — Add Docker Hub Credentials

1. Go to **Manage Jenkins → Credentials → System → Global credentials**
2. Click **Add Credentials** and add the following two entries:

### Credential 1 — Docker Hub Username
| Field | Value |
|---|---|
| Kind | **Secret text** |
| Secret | Your Docker Hub username (e.g. `johndoe`) |
| ID | `DOCKER_HUB_USERNAME` ← must match exactly |
| Description | Docker Hub username |

### Credential 2 — Docker Hub Token
| Field | Value |
|---|---|
| Kind | **Secret text** |
| Secret | Your Docker Hub Access Token (from hub.docker.com → Account Settings → Security) |
| ID | `DOCKER_HUB_TOKEN` ← must match exactly |
| Description | Docker Hub access token |

---

## Step 3 — Create the Jenkins Pipeline Job

1. Click **New Item** on the Jenkins dashboard
2. Enter a name: `cicd-demo` (or any name you like)
3. Select **Multibranch Pipeline** → click **OK**

### Configure Branch Sources

Under **Branch Sources**, click **Add source → Git** (or **GitHub** if using the GitHub plugin):

| Setting | Value |
|---|---|
| Repository URL | `https://github.com/your-org/cicd-demo.git` |
| Credentials | Add your GitHub credentials if it's a private repo |
| Discover branches | All branches |

### Build Configuration

| Setting | Value |
|---|---|
| Mode | **by Jenkinsfile** |
| Script Path | `Jenkinsfile` (default) |

4. Click **Save** — Jenkins will scan the repository and create jobs for each branch.

---

## Step 4 — (Optional) Configure GitHub Webhooks

To trigger Jenkins builds automatically on push (instead of polling every 5 minutes):

1. In your GitHub repo: **Settings → Webhooks → Add webhook**
2. Set the payload URL to: `http://<your-jenkins-url>/github-webhook/`
3. Content type: `application/json`
4. Select: **Just the push event**
5. Click **Add webhook**

Then in Jenkins, under the job's **Configuration**, disable SCM polling and enable **GitHub hook trigger for GITScm polling**.

---

## Step 5 — Trigger Your First Build

1. Go to the `cicd-demo` pipeline job in Jenkins
2. Click **Scan Multibranch Pipeline Now**
3. Jenkins will discover your branches and queue builds
4. Click on the `main` branch → **Build Now** to trigger manually

---

## Pipeline Stage Overview

```
📥 Checkout
    ↓
🐍 Setup Python  (creates .venv-jenkins, installs requirements.txt)
    ↓
🔍 Quality Gate
    ├── Black  (formatting)
    ├── isort  (import order)
    ├── Flake8 (linting)
    ├── mypy   (type checking)
    ├── Bandit (security)
    └── pip-audit (CVE scan)
    ↓
🧪 Tests & Coverage
    ├── pytest with --cov
    ├── JUnit XML report  → Test Results tab in Jenkins
    └── HTML Coverage     → Coverage Report tab in Jenkins
    ↓
🐳 Docker Build & Push
    ├── Builds image tagged with git short SHA
    ├── On main branch: pushes :sha-<hash> and :latest to Docker Hub
    └── On other branches: build only (no push)
```

---

## Comparison: Jenkins vs GitHub Actions

| Feature | Jenkinsfile | ci-cd.yml |
|---|---|---|
| Quality Gate | ✅ Stage: Quality Gate | ✅ Job: quality-gate |
| Tests (pytest) | ✅ Stage: Tests & Coverage | ✅ Job: test |
| Coverage Report | ✅ HTML Publisher (Jenkins UI) | ✅ Artifact upload |
| JUnit Results | ✅ JUnit plugin (Jenkins UI) | ✅ (via pytest-junit) |
| Docker Build | ✅ Stage: Docker Build & Push | ✅ Job: docker-build |
| Docker Push | ✅ main branch only | ✅ main branch / not on PRs |
| Triggers | SCM poll + webhook | push/PR/manual |
| Secrets | Jenkins Credentials store | GitHub Actions Secrets |

---

## Troubleshooting

### `python3: command not found`
Ensure Python 3.11 is installed and on the `PATH` for the Jenkins user:
```bash
sudo apt install python3.11 python3.11-venv  # Ubuntu/Debian
```

### `docker: permission denied`
Add the Jenkins user to the docker group and restart:
```bash
sudo usermod -aG docker jenkins && sudo systemctl restart jenkins
```

### `DOCKER_HUB_USERNAME credential not found`
Double-check the credential ID matches exactly: `DOCKER_HUB_USERNAME` (case-sensitive).

### Coverage report not showing
Ensure the **HTML Publisher Plugin** is installed and the `reports/htmlcov/index.html` file exists after the test run.
