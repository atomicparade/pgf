lint:
	black pgf.py
	mypy --strict pgf.py
	pylint pgf.py

.PHONY: lint
