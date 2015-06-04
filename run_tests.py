#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to run the tests."""

import unittest
import sys

# Change PYTHONPATH to include plaso.
sys.path.insert(0, u'.')

import plaso.dependencies


if __name__ == '__main__':
  if not plaso.dependencies.CheckTestDependencies():
    sys.exit(1)

  test_suite = unittest.TestLoader().discover('tests', pattern='*.py')
  test_results = unittest.TextTestRunner(verbosity=2).run(test_suite)
  if not test_results.wasSuccessful():
    sys.exit(1)

  # Run the tool tests.
  test_suite = unittest.TestLoader().discover('tools', pattern='*_test.py')
  test_results = unittest.TextTestRunner(verbosity=2).run(test_suite)
  if not test_results.wasSuccessful():
    sys.exit(1)
