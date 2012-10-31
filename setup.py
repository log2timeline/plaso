#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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

try:
  from setuptools import find_packages, setup
except ImportError:
  from distutils.core import find_packages, setup

if sys.version < '2.7':
  print 'Wrong Python Version, require version 2.7 or higher (and lower than 3.X).\n%s' % sys.version
  sys.exit(1)

def GetTools():
  """List up all scripts that should be runable from the command line."""
  data = []
  for _, _, filenames in os.walk('frontend/'):
    for filename in filenames:
      if '.py' in filename and filename != '__init__.py':
        if os.path.isfile(os.path.join('frontend', filename)):
          data.append(os.path.join('frontend', filename))

  return data

def GetPackages():
  packages = ['plaso']

  for package in find_packages('.'):
    packages.append('plaso.' + package)

  return packages


def GetFileList(path, patterns):
  file_list = []

  for directory, sub_directories, files in os.walk(path):
    for pattern in patterns:
      directory_pattern = os.path.join(directory, pattern)

      for pattern_match in glob.iglob(directory_pattern):
        if os.path.isfile(pattern_match):
          file_list.append(pattern_match)

  return file_list


setup(name='plaso',
      version='0.1',
      description='The plaso backend as well as few front-ends, such as log2timeline.',
      license='Apache License, Version 2.0',
      url='https://sites.google.com/a/kiddaland.net/plaso',
      package_dir={'plaso': '../plaso'},
      scripts=GetTools(),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
      ],
      #include_package_data=True,
      packages=GetPackages(),
      package_data={'plaso.test_data': GetFileList('test_data', ['*'])},
     )

