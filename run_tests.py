#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script to run the tests."""

from __future__ import print_function

import sys
import unittest

# Change PYTHONPATH to include dependencies.
sys.path.insert(0, '.')

import utils.dependencies  # pylint: disable=wrong-import-position


if __name__ == '__main__':
  print('Using Python version {0!s}'.format(sys.version))
  fail_unless_has_test_file = '--fail-unless-has-test-file' in sys.argv
  setattr(unittest, 'fail_unless_has_test_file', fail_unless_has_test_file)
  if fail_unless_has_test_file:
    # Remove --fail-unless-has-test-file otherwise it will conflict with
    # the argparse tests.
    sys.argv.remove('--fail-unless-has-test-file')

  dependency_helper = utils.dependencies.DependencyHelper()

  if not dependency_helper.CheckTestDependencies():
    sys.exit(1)

  test_suite = unittest.TestLoader().discover('tests', pattern='*.py')
  test_results = unittest.TextTestRunner(verbosity=2).run(test_suite)
  if not test_results.wasSuccessful():
    sys.exit(1)
