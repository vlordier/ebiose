.PHONY: init build run help lint format type-check test coverage docs serve-docs clean

help:
	@echo "Ebiose - Evolutionary AI Agent Ecosystem"
	@echo ""
	@echo "Available targets:"
	@echo "  init           - Initialize project (create .env and model_endpoints.yml)"
	@echo "  build          - Build Docker image"
	@echo "  run            - Run Docker container"
	@echo "  lint           - Run Ruff linter"
	@echo "  format         - Format code with Ruff"
	@echo "  type-check     - Run mypy type checking"
	@echo "  test           - Run pytest tests"
	@echo "  coverage       - Run tests with coverage report"
	@echo "  docs           - Build documentation"
	@echo "  serve-docs     - Serve documentation locally (http://localhost:8000)"
	@echo "  clean          - Remove build artifacts and caches"

init:
	@[ -f model_endpoints.yml ] && echo "model_endpoints.yml already exists." || (cp model_endpoints_template.yml model_endpoints.yml && echo "model_endpoints.yml created. Please fill it with your API keys.")
	@[ -f .env ] && echo ".env already exists." || (cp .env.example .env && echo ".env created.")
	@echo "Project initialized."

build:
	docker build -t ebiose .

run:
	docker run -it --env-file .env -v ./model_endpoints.yml:/app/model_endpoints.yml -v ./data:/app/data -v ./examples:/app/examples ebiose

lint:
	uv run ruff check ebiose tests

format:
	uv run ruff format . && uv run ruff check --fix .

type-check:
	uv run mypy . || true

test:

coverage:
	uv run pytest --cov=ebiose --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated at htmlcov/index.html"
	@echo "Open with: open htmlcov/index.html"
	uv run pytest

docs:
	uv run mkdocs build

serve-docs:
	uv run mkdocs serve

clean:
	rm -rf site/ .ruff_cache/ .mypy_cache/ .pytest_cache/ build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
