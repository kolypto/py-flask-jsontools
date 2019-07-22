all:

SHELL := /bin/bash

# Package
.PHONY: clean
clean:
	@rm -rf build/ dist/ *.egg-info/
#README.md:
#	@python misc/_doc/README.py | j2 --format=json -o README.md misc/_doc/README.md.j2

.PHONY: build publish-test publish
build: README.md
	@./setup.py build sdist bdist_wheel
publish-test: README.md
	@twine upload --repository pypitest dist/*
publish: README.md
	@twine upload dist/*


.PHONY: test test-tox test-docker test-docker-2.6
test:
	@nosetests
test-tox:
	@tox
test-docker:
	@docker run --rm -it -v `pwd`:/src themattrix/tox
test-docker-2.6: # temporary, since `themattrix/tox` has faulty 2.6
	@docker run --rm -it -v $(realpath .):/app mrupgrade/deadsnakes:2.6 bash -c 'cd /app && pip install -e . && pip install nose argparse && nosetests'
