.PHONY: help build clean install test lint typecheck release

help: ## Show this help message
	@echo "TrustGet Build Commands"
	@echo "======================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Python package (wheel and sdist)
	@echo "Building Python package..."
	python3 -m build
	@echo "✓ Build complete. Packages in dist/"

clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	rm -rf dist/ build/ *.egg-info .eggs/
	rm -rf debian/.debhelper debian/files debian/trustget.substvars
	rm -rf .pytest_cache/ .ruff_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Clean complete"

install: ## Install from wheel
	@echo "Installing trustget..."
	pip3 install dist/trustget-*-py3-none-any.whl
	@echo "✓ Installation complete"

install-dev: ## Install in development mode
	@echo "Installing trustget in development mode..."
	pip3 install -e ".[dev]"
	@echo "✓ Development installation complete"

test: ## Run tests
	@echo "Running tests..."
	pytest tests/ -v --cov=trustget

lint: ## Run linter
	@echo "Running ruff linter..."
	ruff check trustget/
	@echo "✓ Linting complete"

typecheck: ## Run type checker
	@echo "Running mypy..."
	mypy trustget/ --ignore-missing-imports
	@echo "✓ Type checking complete"

deb: ## Build Debian package
	@echo "Building Debian package..."
	./scripts/build-deb.sh
	@echo "✓ Debian package build complete"

release: clean build test lint ## Full release build
	@echo ""
	@echo "✓ Release build complete!"
	@echo "Packages:"
	@ls -lh dist/

upload-test: ## Upload to TestPyPI
	@echo "Uploading to TestPyPI..."
	python3 -m twine upload --repository testpypi dist/*
	@echo "✓ Upload to TestPyPI complete"

upload: ## Upload to PyPI (requires TWINE_PASSWORD)
	@echo "Uploading to PyPI..."
	python3 -m twine upload dist/*
	@echo "✓ Upload to PyPI complete"
