.PHONY: lint test

ONLY=""

lint:
	poetry run flake8 anno3d tests
	poetry run mypy anno3d tests
	poetry run black --check .
	poetry run pylint --jobs=$(shell nproc) anno3d tests --rcfile .pylintrc

format:
	poetry run isort --verbose --recursive anno3d tests
	poetry run black .

test:
ifeq ($(ONLY),"")
		poetry run pytest
else
		poetry run pytest ${ONLY}
endif