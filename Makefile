.PHONY: test

test:
	PYTHONPATH=. python -m pytest --log-level=WARN -s
