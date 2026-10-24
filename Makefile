# QoSBoost Makefile - SDN-Based QoS Management for Real-Time Applications

.PHONY: all setup test lint format run-backend run-frontend run-controller demo clean check-prereqs help

PYTHON ?= python
PIP ?= pip
NPM ?= npm

help:
	@echo "======================================================================"
	@echo " QoSBoost: SDN-Based QoS Management for Real-Time Applications"
	@echo "======================================================================"
	@echo " Available Commands:"
	@echo "   make setup          - Install Python and Node dependencies"
	@echo "   make check-prereqs  - Verify system prerequisites (Mininet, OVS, Python, Node)"
	@echo "   make demo           - Launch the full demonstrable system (one-command launch)"
	@echo "   make run-backend    - Run FastAPI backend on port 8000"
	@echo "   make run-frontend   - Run React + Vite frontend on port 5173"
	@echo "   make run-controller - Run Ryu SDN Controller on OpenFlow port 6653"
	@echo "   make test           - Run all backend, classifier, and frontend unit tests"
	@echo "   make lint           - Run ruff linter on Python modules"
	@echo "   make format         - Check Python code formatting with black"
	@echo "   make typecheck      - Run mypy type checker on backend and controller"
	@echo "   make clean          - Teardown Mininet/OVS state, kill processes, clean caches"
	@echo "======================================================================"

lint:
	@echo "Running ruff linter..."
	@$(PYTHON) -m ruff check backend controller network tests

format:
	@echo "Checking black formatting..."
	@$(PYTHON) -m black --check backend controller network tests

typecheck:
	@echo "Running mypy type checks..."
	@$(PYTHON) -m mypy backend controller network

check-prereqs:
	@$(PYTHON) scripts/check_prereqs.py

setup:
	@echo "Installing Python dependencies..."
	@$(PIP) install -r requirements.txt
	@echo "Installing Frontend dependencies..."
	@cd frontend && $(NPM) install
	@echo "Setup complete!"

run-backend:
	@$(PYTHON) -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	@cd frontend && $(NPM) run dev

run-controller:
	@$(PYTHON) -m controller.main

demo:
	@bash scripts/run_demo.sh || $(PYTHON) scripts/run_demo.py

test:
	@echo "Running backend & controller tests..."
	@$(PYTHON) -m pytest tests/ -v
	@echo "Running frontend tests..."
	@cd frontend && $(NPM) run test -- --run

clean:
	@echo "Cleaning up processes and temporary states..."
	@bash scripts/cleanup.sh || $(PYTHON) scripts/cleanup.py
