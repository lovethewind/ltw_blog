format:
	uv run autoflake --in-place .
	uv run isort .
	uv run black .

check:
	uv run isort . --check-only
	uv run black . --check