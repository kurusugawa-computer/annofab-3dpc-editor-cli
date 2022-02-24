.PHONY: lint test docs

ONLY=""

lint:
	poetry run flake8 anno3d tests sandbox.py
	poetry run mypy anno3d tests sandbox.py
	poetry run black --check .
	poetry run pylint --jobs=$(shell nproc) anno3d tests sandbox --rcfile .pylintrc

format:
	poetry run isort --recursive anno3d tests
	poetry run black .

test:
ifeq ($(ONLY),"")
		poetry run pytest
else
		poetry run pytest ${ONLY}
endif

docs:
	cd docs && poetry run make html

