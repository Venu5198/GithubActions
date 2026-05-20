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
//  Prerequisites on Jenkins server:
//    - Python 3.11 installed and on PATH
//    - Docker installed and Jenkins user in docker group
//    - Jenkins Credentials:
//        ID: DOCKER_HUB_USERNAME  (Secret Text)
//        ID: DOCKER_HUB_TOKEN     (Secret Text)
// =============================================================

pipeline {

    // Run on any available agent (Jenkins server or any connected node)
    agent any

    // ── TRIGGERS ───────────────────────────────────────────────
    triggers {
        // Poll SCM every 5 minutes for changes (fallback if webhooks aren't set up)
        pollSCM('H/5 * * * *')
    }

    // ── GLOBAL OPTIONS ─────────────────────────────────────────
    options {
        // Keep only the last 10 builds to save disk space
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // Abort the build if it takes longer than 30 minutes
        timeout(time: 30, unit: 'MINUTES')
        // Add timestamps to console output
        timestamps()
        // Do not allow concurrent builds on the same branch
        disableConcurrentBuilds()
    }

    // ── GLOBAL ENVIRONMENT VARIABLES ───────────────────────────
    environment {
        PYTHON_VERSION = '3.11'
        VENV_DIR       = '.venv-jenkins'
        IMAGE_REPO     = "${DOCKER_HUB_USR}/cicd-demo"
        // Docker Hub credentials are injected via withCredentials below
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

        // ── Stage 1: Setup Python Virtual Environment ──────────
        stage('Setup Python') {
            steps {
                echo "🐍 Setting up Python ${PYTHON_VERSION} virtual environment..."
                sh '''
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        // ── Stage 2: Quality Gate ──────────────────────────────
        // Mirrors GitHub Actions job: quality-gate
        stage('Quality Gate') {
            steps {
                echo '🔍 Running quality checks...'

                // Black — code formatting check
                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- Black: format check ---"
                    black --check --diff app/ tests/ main.py
                '''

                // isort — import order check
                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- isort: import order check ---"
                    isort --check-only --diff app/ tests/ main.py
                '''

                // Flake8 — style linting
                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- Flake8: lint ---"
                    flake8 app/ tests/
                '''

                // mypy — static type checking
                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- mypy: type check ---"
                    mypy app/
                '''

                // Bandit — Python security scan
                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- Bandit: security scan ---"
                    bandit -r app/ -c .bandit
                '''

                // pip-audit — dependency CVE check
                sh '''
                    . ${VENV_DIR}/bin/activate
                    echo "--- pip-audit: dependency CVE check ---"
                    pip-audit -r requirements.txt
                '''
            }
        }

        // ── Stage 3: Tests & Coverage ──────────────────────────
        // Mirrors GitHub Actions job: test
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
                    // Publish JUnit test results (visible in Jenkins test trend graph)
                    junit 'reports/junit.xml'

                    // Publish HTML coverage report
                    publishHTML(target: [
                        allowMissing         : false,
                        alwaysLinkToLastBuild: true,
                        keepAll              : true,
                        reportDir            : 'reports/htmlcov',
                        reportFiles          : 'index.html',
                        reportName           : 'Coverage Report'
                    ])

                    // Archive coverage XML as a build artifact
                    archiveArtifacts artifacts: 'reports/coverage.xml', fingerprint: true
                }
            }
        }

        // ── Stage 4: Docker Build & Push ───────────────────────
        // Mirrors GitHub Actions job: docker-build
        // Only pushes the image when building the 'main' branch
        stage('Docker Build & Push') {
            steps {
                script {
                    def shortSha = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    def imageTag = "sha-${shortSha}"
                    def isMain   = env.BRANCH_NAME == 'main'

                    withCredentials([
                        string(credentialsId: 'DOCKER_HUB_USERNAME', variable: 'DOCKER_HUB_USR'),
                        string(credentialsId: 'DOCKER_HUB_TOKEN',    variable: 'DOCKER_HUB_PWD')
                    ]) {
                        def imageRepo = "${DOCKER_HUB_USR}/cicd-demo"

                        echo "🐳 Building Docker image: ${imageRepo}:${imageTag}"
                        sh "docker build -t ${imageRepo}:${imageTag} ."

                        if (isMain) {
                            echo "🚀 Pushing image to Docker Hub (main branch)..."
                            sh "echo ${DOCKER_HUB_PWD} | docker login -u ${DOCKER_HUB_USR} --password-stdin"
                            sh "docker push ${imageRepo}:${imageTag}"

                            // Also tag and push as :latest on main
                            sh "docker tag ${imageRepo}:${imageTag} ${imageRepo}:latest"
                            sh "docker push ${imageRepo}:latest"

                            echo "✅ Image pushed: ${imageRepo}:${imageTag} and ${imageRepo}:latest"
                        } else {
                            echo "ℹ️ Not on main branch — build only, no push."
                        }

                        // Clean up local image to save disk space
                        sh "docker rmi ${imageRepo}:${imageTag} || true"
                    }
                }
            }
        }
    }

    // ── POST-BUILD NOTIFICATIONS ───────────────────────────────
    post {
        success {
            echo """
            ✅ Pipeline SUCCESS
            Branch  : ${env.BRANCH_NAME}
            Build # : ${env.BUILD_NUMBER}
            Commit  : ${env.GIT_COMMIT?.take(7)}
            """
        }
        failure {
            echo """
            ❌ Pipeline FAILED
            Branch  : ${env.BRANCH_NAME}
            Build # : ${env.BUILD_NUMBER}
            Commit  : ${env.GIT_COMMIT?.take(7)}
            Check the console output for details.
            """
        }
        unstable {
            echo '⚠️ Pipeline UNSTABLE — some tests may have failed. Check test results.'
        }
        cleanup {
            // Remove the virtual environment to keep the workspace clean
            sh 'rm -rf ${VENV_DIR} || true'
        }
    }
}
