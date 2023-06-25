# Turn project into a local, editable package for
# importing modules within src to files in tests/

from setuptools import find_packages, setup

setup(name='src', version='1.0', packages=find_packages())
