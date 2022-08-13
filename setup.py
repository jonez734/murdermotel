#!/usr/bin/env python

import os
import time
from setuptools import setup

r = 1
v = time.strftime("%Y%m%d%H%M")

projectname = "empyre"

os.system("./updateversion.sh")

setup(
  name=projectname,
  version=v,
  url="https://repo.zoidtechnologies.com/%s/" % (projectname),
  author="zoid technologies",
  author_email="%s@projects.zoidtechnologies.com" % (projectname),
  requires=["ttyio5", "bbsengine5"],
  scripts=["bin/empyre"],
  license="GPLv2",
  provides=[projectname],
  packages=["empyre", "empyre.island", "empyre.quests", "empyre.data"],
  long_description = """empyre -- turn-based strategy game based on empire6 and built upon bbsengine5""",
  include_package_data = True,
)
