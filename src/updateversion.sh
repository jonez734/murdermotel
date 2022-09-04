#!/usr/bin/sh

echo '__version__ = "'`git log -1 --format='%H' | cut -c 1-16`'"' > murdermotel/version.py
echo '__datestamp__ = "'`date +%Y%m%d-%H%M`-`whoami`'"' >> murdermotel/version.py
