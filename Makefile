.PHONY: lint test docs publish

ONLY=""

lint:
	poetry run ruff format --check anno3d tests
	poetry run ruff check anno3d tests
	poetry run mypy anno3d tests
	poetry run pylint --jobs=$(shell nproc) anno3d tests --rcfile .pylintrc

format:
	poetry run ruff check anno3d tests --fix-only --exit-zero
	poetry run ruff format anno3d tests

test:
ifeq ($(ONLY),"")
		poetry run pytest
else
		poetry run pytest ${ONLY}
endif

docs:
	cd docs && poetry run make html

publish:
	poetry publish --build
