"""FastAPI application factory for the CI/CD Demo project."""

from fastapi import FastAPI

from app.routes import router

app = FastAPI(
    title="CI/CD Demo API",
    description=(
        "A sample FastAPI backend that demonstrates every stage of a CI/CD pipeline:\n"
        "unit tests, formatting, linting, type-checking,\n"
        "security scanning, coverage, and packaging."
    ),
    version="1.0.0",
    contact={
        "name": "CI/CD Demo",
        "url": "https://github.com/your-org/cicd-demo",
    },
    license_info={
        "name": "MIT",
    },
)

app.include_router(router)
