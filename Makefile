.PHONY: lint format test docs

ONLY=""

lint:
	uv run ruff format --check anno3d tests
	uv run ruff check anno3d tests
	uv run mypy anno3d tests

format:
	uv run ruff check anno3d tests --fix-only --exit-zero
	uv run ruff format anno3d tests

test:
ifeq ($(ONLY),"")
		uv run pytest
else
		uv run pytest ${ONLY}
endif

docs:
	cd docs && uv run make html
