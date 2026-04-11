PROJECT = murdermotel
MEDIA = /run/media/jam/BEA6-BBCE

all:

clean:
	-rm *~
	$(MAKE) -C src clean

push:
	git push

version:
	@echo '__version__ = "'`git log -1 --format='%H' | cut -c 1-16`'"' > murdermotel/_version.py
	@echo '__datestamp__ = "'`date +%Y%m%d-%H%M`-`whoami`'"' >> murdermotel/_version.py

install:
	./setup.py build && sudo ./setup.py install

build: version
	./setup.py build

sdist: version
	./setup.py sdist

backup:
	rsync --recursive --verbose --exclude=.venv . $(MEDIA)work/$(PROJECT)/
