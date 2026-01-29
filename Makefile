.PHONY: help install server frontend local-3 local-4 local-6 train-3 train-4 train-6 format lint test clean

# Export cairo library path for macOS
export DYLD_FALLBACK_LIBRARY_PATH := $(shell brew --prefix cairo 2>/dev/null)/lib:$(DYLD_FALLBACK_LIBRARY_PATH)

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make server     - Run multiplayer server"
	@echo "  make frontend   - Serve frontend (opens browser)"
	@echo "  make local-3    - Run local game (3 players)"
	@echo "  make local-4    - Run local game (4 players)"
	@echo "  make local-6    - Run local game (6 players)"
	@echo "  make train-3    - Train RL agent (3 players)"
	@echo "  make train-4    - Train RL agent (4 players)"
	@echo "  make train-6    - Train RL agent (6 players)"
	@echo "  make format     - Format code"
	@echo "  make lint       - Run type checking"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean generated files"

install:
	uv sync

server:
	uv run python -m backend.src.server

frontend:
	@echo "Starting frontend server on http://localhost:8080"
	@open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null || echo "Please open http://localhost:8080 in your browser"
	@python3 -m http.server 8080

local-3:
	uv run djambi --nb_player_mode 3

local-4:
	uv run djambi --nb_player_mode 4

local-6:
	uv run djambi --nb_player_mode 6

train-3:
	uv run python -m local.train --nb_player_mode 3

train-4:
	uv run python -m local.train --nb_player_mode 4

train-6:
	uv run python -m local.train --nb_player_mode 6

format:
	uv run black .
	uv run isort .

lint:
	uv run mypy .

test:
	uv run pytest

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf *.pyc *.pyo *.pyd
	rm -rf htmlcov .coverage
	rm -rf djambi_rl.log
