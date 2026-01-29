.PHONY: help server local-3 local-4 local-6 train clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make server        - Launch the Djambi server"
	@echo "  make local-3       - Launch local game with 3 players"
	@echo "  make local-4       - Launch local game with 4 players"
	@echo "  make local-6       - Launch local game with 6 players"
	@echo "  make train         - Launch training mode"
	@echo "  make clean         - Clean up generated files"
	@echo "  make help          - Show this help message"

# Server launch
server:
	poetry run gunicorn -w 4 -b 0.0.0.0:8000 backend.src.main:app

# Local game modes
local-3:
	PYTHONPATH=. poetry run python -m backend.src.main --nb_player_mode 3

local-4:
	PYTHONPATH=. poetry run python -m backend.src.main --nb_player_mode 4

local-6:
	PYTHONPATH=. poetry run python -m backend.src.main --nb_player_mode 6

# Training mode
train-3:
	PYTHONPATH=. poetry run python -m local.train --nb_player_mode 3

train-4:
	PYTHONPATH=. poetry run python -m local.train --nb_player_mode 4

train-6:
	PYTHONPATH=. poetry run python -m local.train --nb_player_mode 6

# Clean up
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf *.pyc
	rm -rf *.pyo
	rm -rf *.pyd
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf djambi_rl.log
