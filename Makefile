.PHONY: help install install-frontend install-all dev dev-api test

.DEFAULT_GOAL := help

PYTHON ?= python3
VENV ?= .venv
VENV_BIN := $(VENV)/bin

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Create .venv and install backend deps (FastAPI, uvicorn, etc.)
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@$(VENV_BIN)/pip install --upgrade pip
	@$(VENV_BIN)/pip install -r backend/requirements.txt

install-frontend: ## Install frontend npm dependencies
	cd frontend && npm install

install-all: install install-frontend ## Install backend and frontend dependencies

dev: ## Run Vite frontend (http://localhost:3000)
	cd frontend && npm run dev

dev-api: ## Run FastAPI + uvicorn reload (http://localhost:8000)
	@test -d $(VENV) || (echo "Run 'make install' first." >&2 && exit 1)
	cd backend && ../$(VENV_BIN)/python run.py

test: ## Verify backend import and frontend build (run install-all if deps missing)
	@test -d $(VENV) || (echo "Run 'make install' first." >&2 && exit 1)
	@test -d frontend/node_modules || (echo "Run 'make install-frontend' first." >&2 && exit 1)
	cd backend && ../$(VENV_BIN)/python -c "from app.main import app; print('backend import ok:', app.title)"
	cd frontend && npm run build
