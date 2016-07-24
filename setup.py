#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This is the setup file for the project. The standard setup rules apply:

   python setup.py build
   sudo python setup.py install
"""

from __future__ import print_function
import glob
import locale
import os
import sys

import run_tests

try:
  from setuptools import find_packages, setup, Command
except ImportError:
  from distutils.core import find_packages, setup, Command

# Change PYTHONPATH to include plaso.
sys.path.insert(0, '.')

import plaso
import plaso.dependencies


version_tuple = (sys.version_info[0], sys.version_info[1])
if version_tuple < (2, 7) or version_tuple >= (3, 0):
  print(('Unsupported Python version: {0:s}, version 2.7 or higher and '
         'lower than 3.x required.').format(sys.version))
  sys.exit(1)


def GetScripts():
  """List up all scripts that should be runable from the command line."""
  scripts = []

  script_filenames = frozenset([
      'image_export.py',
      'log2timeline.py',
      'pinfo.py',
      'preg.py',
      'psort.py'])

  for filename in script_filenames:
    scripts.append(os.path.join('tools', filename))

  return scripts


class TestCommand(Command):
  """Run tests, implementing an interface."""
  user_options = []

  def initialize_options(self):
    self._dir = os.getcwd()

  def finalize_options(self):
    pass

  def run(self):
    test_results = run_tests.RunTests()


encoding = sys.stdin.encoding

# Note that sys.stdin.encoding can be None.
if not encoding:
  encoding = locale.getpreferredencoding()

# Make sure the default encoding is set correctly otherwise
# setup.py sdist will fail to include filenames with Unicode characters.
reload(sys)
sys.setdefaultencoding(encoding)

# Unicode in the description will break python-setuptools, hence
# "Plaso Langar Að Safna Öllu" was removed.
plaso_description = 'Super timeline all the things'
plaso_long_description = (
    'Log2Timeline is a framework to create super timelines. Its purpose '
    'is to extract timestamps from various files found on typical computer '
    'systems and aggregate them. Plaso is the Python rewrite of log2timeline.')

setup(
    name='plaso',
    version=plaso.GetVersion(),
    description=plaso_description,
    long_description=plaso_long_description,
    license='Apache License, Version 2.0',
    url='https://sites.google.com/a/kiddaland.net/plaso',
    maintainer='Log2Timeline maintainers',
    maintainer_email='log2timeline-maintainers@googlegroups.com',
    scripts=GetScripts(),
    cmdclass={'test': TestCommand},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages=find_packages('.', exclude=[
        'docs', 'tests', 'tests.*', 'tools', 'utils']),
    package_dir={
        'plaso': 'plaso',
    },
    data_files=[
        ('share/plaso', glob.glob(os.path.join('data', '*'))),
        ('share/doc/plaso', [
            'AUTHORS', 'ACKNOWLEDGEMENTS', 'LICENSE', 'README']),
    ],
    # TODO: this is disabled for now since setup.py will actually try
    # to install the depencies directly from pypi.
    # install_requires=plaso.dependencies.GetInstallRequires(),
)
