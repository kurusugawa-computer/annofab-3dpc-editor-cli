.PHONY: lint test docs publish

ONLY=""

lint:
	poetry run flake8 anno3d tests
	poetry run mypy anno3d tests
	poetry run black --check .
	poetry run pylint --jobs=$(shell nproc) anno3d tests --rcfile .pylintrc

format:
	poetry run isort anno3d tests
	poetry run black .

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
