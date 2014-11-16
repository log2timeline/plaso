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
"""A simple python file to run all of the automatic tests."""

import glob
import os
import pdb
import unittest
import sys


def FormatHeader(header, char='*'):
  """Formats the header as a line of 80 chars with the header text centered."""
  format_string = '\n{{0:{0:s}^80}}'.format(char)
  return format_string.format(u' {0:s} '.format(header))


def FindTestFiles():
  """Return a list of all test files in the project."""
  file_list = []
  pattern = '*_test.py'
  module_dir = os.path.join('.', 'plaso')

  for directory, _, _ in os.walk(module_dir):
    directory_pattern = os.path.join(directory, pattern)

    for pattern_match in glob.iglob(directory_pattern):
      if os.path.isfile(pattern_match):
        file_list.append(pattern_match)

  return file_list


def RunTests(debug_mode=False):
  """Runs all the tests and returns the results back."""
  # TODO: Re-enable the mac securityd test. There were no changes to any files
  # related to securityd parsing, yet the tests fail, but not if run
  # independently, this has something to do with the test suite.
  blacklisted_casses = [
      'plaso.parsers.pcap_test', 'plaso.parsers.mac_securityd_test',
      'plaso.frontend.preg_test']

  tests = None
  for test_file in sorted(FindTestFiles()):
    library_name = test_file.rstrip('.py').replace(os.path.sep, '.').lstrip('.')
    if library_name in blacklisted_casses:
      continue
    try:
      if not tests:
        tests = unittest.TestLoader().loadTestsFromName(library_name)
      else:
        tests.addTests(unittest.TestLoader().loadTestsFromName(library_name))
    except AttributeError as exception:
      print u'Unable to run test: {0:s} [{1:s}] due to error: {2:s}'.format(
          library_name, test_file, exception)
      if debug_mode:
        pdb.post_mortem()
      sys.exit(1)

  test_run = unittest.TextTestRunner(verbosity=1)
  return test_run.run(tests)


def PrintResults(my_results):
  """Print the results from an aggregated test run."""
  errors = 0
  failures = 0
  print 'Ran: {0:d} tests.'.format(my_results.testsRun)
  if my_results.wasSuccessful():
    print '--++'*20
    print 'Yeee you know what, all tests came out clean.'
    print '--++'*20
  else:
    errors = len(my_results.errors)
    failures = len(my_results.failures)

    print my_results.printErrors()
    print FormatHeader('Tests failed.')
    print '  {:>10s}: {0:d}\n  {:>10s}: {1:d}\n  {:>10s}: {2:d}'.format(
        'Errors', errors, 'Failures', failures, 'Total',
        errors + failures)
    print '+='*40


if __name__ == '__main__':
  # Modify the system path to first search the CWD.
  sys.path.insert(0, '.')

  # Allow debug mode, no need for advanced parameter handling.
  if len(sys.argv) == 2 and sys.argv[1] == '-d':
    debug = True
  else:
    debug = False

  test_results = RunTests(debug)

  if not test_results:
    print 'Unable to run tests due to an error.'
    sys.exit(1)

  PrintResults(test_results)
  if not test_results.wasSuccessful():
    sys.exit(1)
