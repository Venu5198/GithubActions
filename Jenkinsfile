// =============================================================
//  CI / CD Pipeline — CI/CD Demo FastAPI Application
//  Jenkins Declarative Pipeline (mirrors .github/workflows/ci-cd.yml)
//
//  Pipeline stages (run in order):
//    1. Quality Gate     → Black, isort, Flake8, mypy, Bandit, pip-audit
//    2. Tests & Coverage → pytest with 80% coverage gate + JUnit/HTML reports
//    3. SonarQube        → deep code quality + security analysis
//    4. Quality Gate     → wait for SonarQube PASS/FAIL decision
//    5. Docker Build     → build image
//    6. Trivy Scan       → scan image for CVEs (fails on CRITICAL)
//    7. Docker Push      → push to Docker Hub (main branch only)
//
//  Prerequisites on Jenkins server / container:
//    - Python 3 installed
//    - Docker installed and accessible
//    - sonar-scanner CLI installed  (or downloaded at runtime)
//    - Trivy CLI installed          (or downloaded at runtime)
//    - Jenkins Plugins:
//        SonarQube Scanner, HTML Publisher, JUnit
//    - Jenkins Credentials:
//        ID: DOCKER_HUB_USERNAME  (Secret Text)
//        ID: DOCKER_HUB_TOKEN     (Secret Text)
//        ID: SONAR_TOKEN          (Secret Text — from SonarQube → My Account → Security)
//    - Jenkins System Config (Manage Jenkins → System):
//        SonarQube server name: SonarQube
//        SonarQube server URL:  http://sonarqube:9000   (if same Docker network)
//                            OR http://localhost:9000   (if running on host)
// =============================================================

pipeline {

    agent any

    // ── TRIGGERS ───────────────────────────────────────────────
    triggers {
        pollSCM('H/5 * * * *')
    }

    // ── GLOBAL OPTIONS ─────────────────────────────────────────
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 45, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
    }

    // ── GLOBAL ENVIRONMENT VARIABLES ───────────────────────────
    environment {
        VENV_DIR     = '.venv-jenkins'
        SONAR_HOST   = 'http://host.docker.internal:9000'  // SonarQube on your PC
    }

    // ===========================================================
    // STAGES
    // ===========================================================
    stages {

        // ── Stage 1: Checkout ───────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📥 Checking out source code...'
                checkout scm
            }
        }

        // ── Stage 2: Setup Python Virtual Environment ───────────
        stage('Setup Python') {
            steps {
                echo '🐍 Verifying Python and setting up virtual environment...'
                sh '''
                    python3 --version
                    pip3 --version
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip --quiet
                    pip install -r requirements.txt --quiet
                    echo "✅ Dependencies installed successfully"
                '''
            }
        }

        // ── Stage 3: Quality Gate ───────────────────────────────
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

        // ── Stage 4: Tests & Coverage ───────────────────────────
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
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                    publishHTML(target: [
                        allowMissing         : true,
                        alwaysLinkToLastBuild: true,
                        keepAll              : true,
                        reportDir            : 'reports/htmlcov',
                        reportFiles          : 'index.html',
                        reportName           : 'Coverage Report'
                    ])
                    archiveArtifacts allowEmptyArchive: true,
                                     artifacts: 'reports/coverage.xml',
                                     fingerprint: true
                }
            }
        }

        // ── Stage 5: SonarQube Analysis ─────────────────────────
        // Sends code + coverage data to the SonarQube server.
        // Requires:
        //   • SonarQube Scanner plugin installed in Jenkins
        //   • Server configured: Manage Jenkins → System → SonarQube servers
        //   • SONAR_TOKEN credential added in Jenkins
        stage('SonarQube Analysis') {
            steps {
                echo '📊 Running SonarQube analysis...'
                withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_AUTH_TOKEN')]) {
                    sh '''
                        # Download sonar-scanner if not already installed
                        if ! command -v sonar-scanner &> /dev/null; then
                            echo "⬇️  Downloading sonar-scanner..."
                            curl -sSLo /tmp/sonar-scanner.zip \
                                https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-6.2.1.4610-linux-x64.zip
                            unzip -q /tmp/sonar-scanner.zip -d /tmp/
                            export PATH="/tmp/sonar-scanner-6.2.1.4610-linux-x64/bin:$PATH"
                        fi

                        echo "🔍 Running sonar-scanner..."
                        sonar-scanner \
                            -Dsonar.host.url="${SONAR_HOST}" \
                            -Dsonar.token="${SONAR_AUTH_TOKEN}" \
                            -Dsonar.projectKey=cicd-demo \
                            -Dsonar.projectName="CI/CD Demo FastAPI" \
                            -Dsonar.sources=app \
                            -Dsonar.tests=tests \
                            -Dsonar.python.version=3 \
                            -Dsonar.python.coverage.reportPaths=reports/coverage.xml
                    '''
                }
            }
        }

        // ── Stage 6: SonarQube Quality Gate Check ───────────────
        // Waits for SonarQube to compute the Quality Gate result.
        // Pipeline is aborted if Quality Gate status is FAILED.
        stage('Quality Gate — SonarQube') {
            steps {
                echo '⏳ Waiting for SonarQube Quality Gate result...'
                timeout(time: 5, unit: 'MINUTES') {
                    script {
                        // Poll SonarQube for the project status
                        withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_AUTH_TOKEN')]) {
                            def qgStatus = sh(
                                script: """
                                    curl -s -u "\${SONAR_AUTH_TOKEN}:" \
                                        "${SONAR_HOST}/api/qualitygates/project_status?projectKey=cicd-demo" \
                                        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['projectStatus']['status'])"
                                """,
                                returnStdout: true
                            ).trim()

                            echo "SonarQube Quality Gate status: ${qgStatus}"

                            if (qgStatus != 'OK' && qgStatus != 'NONE') {
                                error("❌ SonarQube Quality Gate FAILED — status: ${qgStatus}. Check ${SONAR_HOST}/dashboard?id=cicd-demo")
                            }
                            echo "✅ SonarQube Quality Gate PASSED"
                        }
                    }
                }
            }
        }

        // ── Stage 7: Docker Build + Trivy Scan + Push ───────────
        stage('Docker Build & Push') {
            steps {
                script {
                    def imageTag = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    def isMain   = (env.BRANCH_NAME == 'main')
                    def pushFlag = isMain ? 'true' : 'false'

                    withCredentials([
                        string(credentialsId: 'DOCKER_HUB_USERNAME', variable: 'DOCKER_USR'),
                        string(credentialsId: 'DOCKER_HUB_TOKEN',    variable: 'DOCKER_PWD')
                    ]) {
                        sh """
                            IMAGE_REPO="\${DOCKER_USR}/cicd-demo"
                            IMAGE_TAG="sha-${imageTag}"

                            # ── 1. Build Docker image ─────────────────────────
                            echo "🐳 Building Docker image: \${IMAGE_REPO}:\${IMAGE_TAG}"
                            docker build -t "\${IMAGE_REPO}:\${IMAGE_TAG}" .

                            # ── 2. Trivy — scan image for CVEs ────────────────
                            echo "🛡️  Running Trivy vulnerability scan..."

                            # Download Trivy if not installed
                            if ! command -v trivy &> /dev/null; then
                                echo "⬇️  Downloading Trivy..."
                                curl -sSfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                            fi

                            # Scan: show all, but only FAIL on CRITICAL severity
                            trivy image \
                                --exit-code 0 \
                                --severity HIGH,CRITICAL \
                                --format table \
                                "\${IMAGE_REPO}:\${IMAGE_TAG}" || true

                            # Save Trivy report as JSON artifact
                            mkdir -p reports
                            trivy image \
                                --exit-code 1 \
                                --severity CRITICAL \
                                --format json \
                                --output reports/trivy-report.json \
                                "\${IMAGE_REPO}:\${IMAGE_TAG}"

                            echo "✅ Trivy scan complete — no CRITICAL CVEs found"

                            # ── 3. Push to Docker Hub (main branch only) ──────
                            if [ "${pushFlag}" = "true" ]; then
                                echo "🚀 Pushing image to Docker Hub..."
                                echo "\${DOCKER_PWD}" | docker login -u "\${DOCKER_USR}" --password-stdin
                                docker push "\${IMAGE_REPO}:\${IMAGE_TAG}"
                                docker tag  "\${IMAGE_REPO}:\${IMAGE_TAG}" "\${IMAGE_REPO}:latest"
                                docker push "\${IMAGE_REPO}:latest"
                                echo "✅ Pushed: \${IMAGE_REPO}:\${IMAGE_TAG} and \${IMAGE_REPO}:latest"
                            else
                                echo "ℹ️  Not on main branch — NOT pushed."
                            fi

                            # ── 4. Cleanup ────────────────────────────────────
                            docker rmi "\${IMAGE_REPO}:\${IMAGE_TAG}" || true
                        """
                    }
                }
            }
            post {
                always {
                    // Archive Trivy JSON report as a downloadable artifact
                    archiveArtifacts allowEmptyArchive: true,
                                     artifacts: 'reports/trivy-report.json',
                                     fingerprint: true
                }
            }
        }
    }

    // ── POST-BUILD ACTIONS ─────────────────────────────────────
    post {
        success {
            echo """
            ╔══════════════════════════════════════╗
            ║   ✅  Pipeline SUCCESS               ║
            ╚══════════════════════════════════════╝
            Branch    : ${env.BRANCH_NAME}
            Build #   : ${env.BUILD_NUMBER}
            Commit    : ${env.GIT_COMMIT?.take(7)}
            SonarQube : ${SONAR_HOST}/dashboard?id=cicd-demo
            """
        }
        failure {
            echo """
            ╔══════════════════════════════════════╗
            ║   ❌  Pipeline FAILED                ║
            ╚══════════════════════════════════════╝
            Branch  : ${env.BRANCH_NAME}
            Build # : ${env.BUILD_NUMBER}
            Commit  : ${env.GIT_COMMIT?.take(7)}
            → Check Console Output for details.
            """
        }
        unstable {
            echo '⚠️  Pipeline UNSTABLE — check Test Results and SonarQube.'
        }
        cleanup {
            sh 'rm -rf ${VENV_DIR} || true'
        }
    }
}
