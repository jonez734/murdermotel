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
  url="https://zoidtechnologies.com/%s/" % (projectname),
  author="zoidtechnologies.com",
  author_email="%s@projects.zoidtechnologies.com" % (projectname),
  requires=["bbsengine6",],
  scripts=[f"../bin/{projectname}"],
  license="GPLv2",
  provides=[projectname],
  packages=[projectname, f"{projectname}.data"],
  long_description = """murder motel -- turn based game involving assassination of other players""",
  include_package_data = True,
)
