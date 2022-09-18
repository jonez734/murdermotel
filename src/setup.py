#!/usr/bin/env python

import os
import time
from setuptools import setup

r = 1
v = time.strftime("%Y%m%d%H%M")

projectname = "murdermotel"

os.system("./updateversion.sh")

setup(
  name=projectname,
  version=v,
  url="https://repo.zoidtechnologies.com/%s/" % (projectname),
  author="zoid technologies",
  author_email="%s@projects.zoidtechnologies.com" % (projectname),
  requires=["ttyio5", "bbsengine5"],
  scripts=["../bin/murdermotel"],
  license="GPLv2",
  provides=[projectname],
  packages=["murdermotel", "murdermotel.data"],
  long_description = """murder motel -- turn based game involving assassination of other players""",
  include_package_data = True,
)
