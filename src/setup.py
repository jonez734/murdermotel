#!/usr/bin/env python

import os
import time
from setuptools import setup

r = 1
v = time.strftime("%Y%m%d%H%M")

projectname = "murdermotel"

r = 1
# If VERSION env var is set, use it; otherwise use timestamp
v = os.environ.get("VERSION")
if v is None:
    v = time.strftime("%Y%m%d%H%M")

setup(
    name=projectname,
    version=v,
    url="https://zoidtechnologies.com/%s/" % (projectname),
    author="zoidtechnologies.com",
    author_email="%s@projects.zoidtechnologies.com" % (projectname),
    requires=[
        "bbsengine6",
    ],
    scripts=[f"../bin/{projectname}"],
    license="GPL-2.0-or-later",
    provides=[projectname],
    packages=[projectname, f"{projectname}.data"],
    long_description="""murder motel -- turn based game involving assassination of other players""",
    include_package_data=True,
)
