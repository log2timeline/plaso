#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This is the setup file for the project. The standard setup rules apply:

   python setup.py build
   sudo python setup.py install
"""

import glob
import os
import sys

import run_tests

try:
  from setuptools import find_packages, setup, Command
except ImportError:
  from distutils.core import find_packages, setup, Command

version_tuple = (sys.version_info[0], sys.version_info[1])
if version_tuple < (2, 7) or version_tuple >= (3, 0):
  print (u'Unsupported Python version: {0:s}, version 2.7 or higher and '
         u'lower than 3.x required.').format(sys.version)
  sys.exit(1)

# Change PYTHONPATH to include plaso so that we can get the version.
sys.path.insert(0, '.')

import plaso


def GetTools():
  """List up all scripts that should be runable from the command line."""
  tools = []

  tool_filenames = frozenset([
      u'export_image.py',
      u'log2timeline.py',
      u'pinfo.py',
      u'plasm.py',
      u'pprof.py',
      u'preg.py',
      u'pshell.py',
      u'psort.py'])

  for filename in tool_filenames:
    tools.append(os.path.join(u'plaso', u'frontend', filename))

  tool_filenames = frozenset([
      u'image_export.py',
      u'plaso_extract_search_history.py'])

  for filename in tool_filenames:
    tools.append(os.path.join(u'tools', filename))

  return tools


class TestCommand(Command):
  """Run tests, implementing an interface."""
  user_options = []

  def initialize_options(self):
    self._dir = os.getcwd()

  def finalize_options(self):
    pass

  def run(self):
    test_results = run_tests.RunTests()


# Unicode in the description will break python-setuptools, hence
# "Plaso Langar Að Safna Öllu" was removed.
plaso_description = (
    u'plaso is a tool designed to extract timestamps from various files found '
    u'on a typical computer system(s) and aggregate them.')

setup(
    name='plaso',
    version=plaso.GetVersion(),
    description=plaso_description,
    long_description=plaso_description,
    license='Apache License, Version 2.0',
    url='https://sites.google.com/a/kiddaland.net/plaso',
    maintainer='Plaso development team',
    maintainer_email='log2timeline-dev@googlegroups.com',
    scripts=GetTools(),
    cmdclass={'test': TestCommand},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    package_dir={'plaso': 'plaso'},
    packages=find_packages('.'),
)
