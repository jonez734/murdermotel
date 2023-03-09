import importlib.resources as resources

from ..lib import PACKAGENAME

# @since 20220810
# @see https://github.com/cirosantilli/python-sample-package-with-data/blob/master/python_sample_package_with_data/__init__.py
# @see https://stackoverflow.com/questions/3596979/manifest-in-ignored-on-python-setup-py-install-no-data-files-installed
# @see https://the-hitchhikers-guide-to-packaging.readthedocs.io/en/latest/quickstart.html
def get(name):
    return resources.open_text(PACKAGENAME+".data", name)
