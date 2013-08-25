#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""
This is the setup file for the project. The standard setup rules apply:

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

if sys.version < '2.7':
  print ('Wrong Python Version, require version 2.7 or higher (and lower '
         'than 3.X).\n%s') % sys.version
  sys.exit(1)

def GetTools():
  """List up all scripts that should be runable from the command line."""
  tools = []
  tools.extend(GetToolsFrom(os.path.join('plaso', 'frontend')))
  tools.extend(GetToolsFrom('tools'))

  return tools


def GetToolsFrom(path):
  """Get tools from a given directory."""
  data = []
  for _, _, filenames in os.walk(path):
    for filename in filenames:
      if '_test' in filename:
        continue
      if '.py' in filename and filename != '__init__.py':
        if os.path.isfile(os.path.join(path, filename)):
          data.append(os.path.join(path, filename))

  return data


def GetFileList(path, patterns):
  file_list = []

  for directory, sub_directories, files in os.walk(path):
    for pattern in patterns:
      directory_pattern = os.path.join(directory, pattern)

      for pattern_match in glob.iglob(directory_pattern):
        if os.path.isfile(pattern_match):
          file_list.append(pattern_match)

  return file_list


class TestCommand(Command):
  """Run tests, implementing an interface."""
  user_options = []

  def initialize_options(self):
    self._dir = os.getcwd()

  def finalize_options(self):
    pass

  def run(self):
    results = run_tests.RunTests()


setup(name='plaso',
      version='1.0.2dev',
      description='The plaso backend as well as few front-ends.',
      license='Apache License, Version 2.0',
      url='https://sites.google.com/a/kiddaland.net/plaso',
      package_dir={'plaso': 'plaso'},
      scripts=GetTools(),
      cmdclass = {'test': TestCommand},
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
      ],
      #include_package_data=True,
      packages=find_packages('.'),
      package_data={'plaso.test_data': GetFileList('test_data', ['*'])},
     )

