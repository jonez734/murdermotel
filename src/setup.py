#!/usr/bin/env python

import os
import time
from setuptools import setup

projectname = "murdermotel"
v = os.environ.get("VERSION", time.strftime("%Y%m%d%H%M"))

setup(
    name=projectname,
    version=v,
    url=f"https://zoidtechnologies.com/{projectname}/",
    author="zoidtechnologies.com",
    author_email=f"{projectname}@projects.zoidtechnologies.com",
    requires=["bbsengine6"],
    scripts=["../bin/murdermotel"],
    license="GPL-2.0-or-later",
    provides=[projectname],
    long_description="""murder motel -- turn based game involving assassination of other players""",
    include_package_data=True,
)