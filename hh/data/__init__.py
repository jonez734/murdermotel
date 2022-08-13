import importlib.resources as res

import bbsengine5 as bbsengine

# @since 20220810
# @see https://github.com/cirosantilli/python-sample-package-with-data/blob/master/python_sample_package_with_data/__init__.py
# @see https://stackoverflow.com/questions/3596979/manifest-in-ignored-on-python-setup-py-install-no-data-files-installed
# @see https://the-hitchhikers-guide-to-packaging.readthedocs.io/en/latest/quickstart.html
def get(name):
    return "/"+bbsengine.buildfilepath(res.path(__name__, str(name))) # os.path.dirname(__file__), name)
