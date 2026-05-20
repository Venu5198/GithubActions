// =============================================================
//  CI / CD Pipeline — CI/CD Demo FastAPI Application
//  Jenkins Declarative Pipeline (mirrors .github/workflows/ci-cd.yml)
//
//  Pipeline stages (run in order):
//    1. Quality Gate  → format + lint + type-check + security
//    2. Test          → pytest with 80% coverage gate + JUnit report
//    3. Docker Build  → build image and push to Docker Hub
//                       (only on main branch, not other branches)
//
//  Prerequisites on Jenkins server / container:
//    - Python 3 installed  (apt-get install -y python3 python3-pip python3-venv)
//    - Docker installed and accessible
//    - Jenkins Credentials:
//        ID: DOCKER_HUB_USERNAME  (Secret Text — your Docker Hub username)
//        ID: DOCKER_HUB_TOKEN     (Secret Text — your Docker Hub access token)
// =============================================================

pipeline {

    // Run on any available Jenkins agent / node
    agent any

    // ── TRIGGERS ───────────────────────────────────────────────
    triggers {
        // Poll SCM every 5 minutes for new commits
        pollSCM('H/5 * * * *')
    }

    // ── GLOBAL OPTIONS ─────────────────────────────────────────
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
    }

    // ── GLOBAL ENVIRONMENT VARIABLES ───────────────────────────
    environment {
        VENV_DIR = '.venv-jenkins'
    }

    // ===========================================================
    // STAGES
    // ===========================================================
    stages {

        // ── Stage 0: Checkout ──────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📥 Checking out source code...'
                checkout scm
            }
        }

        // ── Stage 1: Verify Python & Setup Virtual Environment ─
        stage('Setup Python') {
            steps {
                echo '🐍 Verifying Python and setting up virtual environment...'
                sh '''
                    # Print Python version for diagnostics
                    python3 --version
                    pip3 --version

                    # Create a fresh virtual environment
                    python3 -m venv ${VENV_DIR}

                    # Activate and install all dependencies
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip --quiet
                    pip install -r requirements.txt --quiet
                    echo "✅ Dependencies installed successfully"
                '''
            }
        }

        // ── Stage 2: Quality Gate ──────────────────────────────
        // Runs: Black → isort → Flake8 → mypy → Bandit → pip-audit
        stage('Quality Gate') {
            steps {
                echo '🔍 Running quality checks...'

                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- ✏️  Black: format check ---"
                    black --check --diff app/ tests/ main.py
                '''

                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- 📦 isort: import order check ---"
                    isort --check-only --diff app/ tests/ main.py
                '''

                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- 🔎 Flake8: lint ---"
                    flake8 app/ tests/
                '''

                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- 🔬 mypy: type check ---"
                    mypy app/
                '''

                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- 🔒 Bandit: security scan ---"
                    bandit -r app/ -c .bandit
                '''

                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- 🛡️  pip-audit: dependency CVE check ---"
                    pip-audit -r requirements.txt
                '''
            }
        }

        // ── Stage 3: Tests & Coverage ──────────────────────────
        stage('Tests & Coverage') {
            steps {
                echo '🧪 Running test suite with coverage...'
                sh '''
                    . ${VENV_DIR}/bin/activate
                    mkdir -p reports
                    pytest tests/ \
                        --cov=app \
                        --cov-report=term-missing \
                        --cov-report=xml:reports/coverage.xml \
                        --cov-report=html:reports/htmlcov \
                        --junitxml=reports/junit.xml \
                        -v
                '''
            }
            post {
                always {
                    // Show test results in Jenkins UI (pass/fail trend graph)
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'

                    // Show HTML coverage report as a tab in Jenkins UI
                    publishHTML(target: [
                        allowMissing         : true,
                        alwaysLinkToLastBuild: true,
                        keepAll              : true,
                        reportDir            : 'reports/htmlcov',
                        reportFiles          : 'index.html',
                        reportName           : 'Coverage Report'
                    ])

                    // Save coverage XML as a downloadable build artifact
                    archiveArtifacts allowEmptyArchive: true,
                                     artifacts: 'reports/coverage.xml',
                                     fingerprint: true
                }
            }
        }

        // ── Stage 4: Docker Build & Push ───────────────────────
        // Builds the image on every branch.
        // Pushes to Docker Hub ONLY on the 'main' branch.
        stage('Docker Build & Push') {
            steps {
                script {
                    // Capture the short git SHA (not a secret — safe to use in GString)
                    def imageTag = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    def isMain   = (env.BRANCH_NAME == 'main')
                    def pushFlag = isMain ? 'true' : 'false'

                    withCredentials([
                        string(credentialsId: 'DOCKER_HUB_USERNAME', variable: 'DOCKER_USR'),
                        string(credentialsId: 'DOCKER_HUB_TOKEN',    variable: 'DOCKER_PWD')
                    ]) {
                        // ⚠️  Use \${DOCKER_USR} / \${DOCKER_PWD} so the SHELL expands
                        // them at runtime — never Groovy. This avoids the secret
                        // interpolation security warning.
                        sh """
                            IMAGE_REPO="\${DOCKER_USR}/cicd-demo"
                            IMAGE_TAG="sha-${imageTag}"

                            echo "🐳 Building Docker image: \${IMAGE_REPO}:\${IMAGE_TAG}"
                            docker build -t "\${IMAGE_REPO}:\${IMAGE_TAG}" .

                            if [ "${pushFlag}" = "true" ]; then
                                echo "🚀 Pushing image to Docker Hub (main branch)..."
                                echo "\${DOCKER_PWD}" | docker login -u "\${DOCKER_USR}" --password-stdin
                                docker push "\${IMAGE_REPO}:\${IMAGE_TAG}"
                                docker tag  "\${IMAGE_REPO}:\${IMAGE_TAG}" "\${IMAGE_REPO}:latest"
                                docker push "\${IMAGE_REPO}:latest"
                                echo "✅ Pushed: \${IMAGE_REPO}:\${IMAGE_TAG} and \${IMAGE_REPO}:latest"
                            else
                                echo "ℹ️  Not on main branch — image built locally, NOT pushed."
                            fi

                            # Clean up local image to save disk space
                            docker rmi "\${IMAGE_REPO}:\${IMAGE_TAG}" || true
                        """
                    }
                }
            }
        }
    }

    // ── POST-BUILD ACTIONS ─────────────────────────────────────
    post {
        success {
            echo """
            ╔══════════════════════════════╗
            ║   ✅  Pipeline  SUCCESS      ║
            ╚══════════════════════════════╝
            Branch  : ${env.BRANCH_NAME}
            Build # : ${env.BUILD_NUMBER}
            Commit  : ${env.GIT_COMMIT?.take(7)}
            """
        }
        failure {
            echo """
            ╔══════════════════════════════╗
            ║   ❌  Pipeline  FAILED       ║
            ╚══════════════════════════════╝
            Branch  : ${env.BRANCH_NAME}
            Build # : ${env.BUILD_NUMBER}
            Commit  : ${env.GIT_COMMIT?.take(7)}
            → Open Console Output to see which stage failed.
            """
        }
        unstable {
            echo '⚠️  Pipeline UNSTABLE — some tests failed. Check Test Results tab.'
        }
        cleanup {
            // Always remove the virtual environment to keep workspace tidy
            sh 'rm -rf ${VENV_DIR} || true'
        }
    }
}
