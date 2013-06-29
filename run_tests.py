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
"""A simple python file to run all of the automatic tests."""
import glob
import os
import unittest
import sys

from plaso.lib import utils


def FindTestFiles():
  """Return a list of all test files in the project."""
  file_list = []
  pattern = '*_test.py'
  #plaso_root_dir = os.path.join('.', 'plaso', 'parsers')
  plaso_root_dir = os.path.join('.', 'plaso')

  for directory, sub_directories, files in os.walk(plaso_root_dir):
    directory_pattern = os.path.join(directory, pattern)

    for pattern_match in glob.iglob(directory_pattern):
      if os.path.isfile(pattern_match):
        file_list.append(pattern_match)

  return file_list


def RunTests():
  """Runs all the tests and returns the results back."""
  test_classes = []

  for test_file in FindTestFiles():
    library_name = test_file.rstrip('.py').replace('/', '.').lstrip('.')
    test_classes.append(library_name)

  tests = unittest.TestLoader().loadTestsFromNames(test_classes)
  test_run = unittest.TextTestRunner(verbosity=1)
  return test_run.run(tests)


def PrintResults(results):
  """Print the results from an aggregated test run."""
  errors = 0
  failures = 0
  print 'Ran: {} tests.'.format(results.testsRun)
  if results.wasSuccessful():
    print '--++'*20
    print 'Yeee you know what, all tests came out clean.'
    print '--++'*20
  else:
    errors = len(results.errors)
    failures = len(results.failures)

    print results.printErrors()
    print utils.FormatHeader('Tests failed.')
    print '  {:>10s}: {}\n  {:>10s}: {}\n  {:>10s}: {}'.format(
        'Errors', errors, 'Failures', failures, 'Total',
        errors + failures)
    print '+='*40


if __name__ == '__main__':
  """Run all of tests."""
  # Modify the system path to first search the CWD.
  sys.path.insert(0, '.')

  results = RunTests()
  errors = 0
  failures = 0

  PrintResults(results)


