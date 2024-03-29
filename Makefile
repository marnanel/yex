help:
	@echo "use one of:"
	@echo "		make docs"
	@echo "		make venv"
	@echo "		make dependencies"
	@echo "		make test"
	@echo "		make install"

.PHONY: help docs venv dependencies test install

docs:
	make -C docs html

venv:
	python -m venv venv
	@echo "now type:"
	@echo "		source venv/bin/activate"

dependencies:
	@echo "put the kettle on: this takes a while"
	python -m pip install -r requirements.txt
	@echo "If you're building docs, please also run"
	@echo "    make doc-dependencies"

doc-dependencies:
	python -m pip install -r docs/requirements.txt

test:
	./y test

install:
	python setup.py install
