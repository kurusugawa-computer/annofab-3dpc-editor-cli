.PHONY: lint test docs publish

ONLY=""

lint:
	poetry run ruff check anno3d tests
	poetry run flake8 anno3d tests
	poetry run mypy anno3d tests
	poetry run black --check .
	poetry run pylint --jobs=$(shell nproc) anno3d tests --rcfile .pylintrc

format:
	# isortの替わりにruffを使っている
	poetry run ruff check anno3d tests --select I --fix-only --exit-zero
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
