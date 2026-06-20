PROJECT = murdermotel
OUTDIR = $(CURDIR)/dist/
VERSION = 0.0.0.dev$(shell date +%Y%m%d%H%M)
MEDIA = /run/media/jam/BEA6-BBCE/work/$(PROJECT)/
PYTHON = $(HOME)/.venv/bin/python

.PHONY: all clean build sdist version

all:

clean:
	-rm *~
	$(MAKE) -C src clean

build: version
	cd src && $(PYTHON) ./setup.py build

sdist: version
	cd src && $(PYTHON) ./setup.py sdist

version:
	@echo '__version__ = "$(VERSION)"' > src/murdermotel/_version.py
	@echo 'githash = "'`git log -1 --format='%H' | cut -c 1-16`'"' >> src/murdermotel/_version.py
	@echo 'datestamp = "$(shell date +%Y%m%d%H%M)"' >> src/murdermotel/_version.py

push:
	git push

backup:
	rsync --recursive --verbose --exclude=.venv . $(MEDIA)

www:
	$(MAKE) -C www prod
