PROJECT=charmguardian

all: .venv lint test

clean:
	rm -rf MANIFEST dist/* $(PROJECT).egg-inf .cover
	find . -name '*.pyc' -delete
	rm -rf .venv
	rm -rf .cover

test: .venv
	@echo Starting tests...
	@.venv/bin/nosetests tests

coverage: .venv
	@echo Starting tests...
	@.venv/bin/nosetests tests --with-coverage

lint:
	@flake8 $(PROJECT) $(TESTS) && echo OK

.venv:
	./bin/test_setup
