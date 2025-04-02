# Makefile for Prefect MCP Server Repository

.PHONY: install build test deploy clean

# Build the package
build:
	uv build

# Run tests using pytest (if tests are available)
test:
	pytest

# Deploy package (customize as needed)
deploy:
	uv run twine upload dist/* --skip-existing

# Clean build artifacts
clean:
	rm -rf build dist *.egg-info 