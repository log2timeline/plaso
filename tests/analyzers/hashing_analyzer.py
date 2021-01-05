#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Hashing analyzer."""

import unittest

from plaso.containers import analyzer_result
from plaso.analyzers import hashing_analyzer
from plaso.analyzers.hashers import manager

from tests import test_lib as shared_test_lib
from tests.analyzers.hashers import manager as manager_test


class HashingAnalyzerTest(shared_test_lib.BaseTestCase):
  """Test the Hashing analyzer."""

  # pylint: disable=protected-access

  @classmethod
  def setUpClass(cls):
    """Makes preparations before running any of the tests."""
    manager.HashersManager.RegisterHasher(manager_test.TestHasher)

  @classmethod
  def tearDownClass(cls):
    """Cleans up after running all tests."""
    manager.HashersManager.DeregisterHasher(manager_test.TestHasher)

  def testHasherInitialization(self):
    """Test the creation of the analyzer, and the enabling of hashers."""
    analyzer = hashing_analyzer.HashingAnalyzer()
    analyzer.SetHasherNames('testhash')
    self.assertEqual(len(analyzer._hashers), 1)

  def testHashFile(self):
    """Tests that results are produced correctly."""
    analyzer = hashing_analyzer.HashingAnalyzer()
    analyzer.SetHasherNames('testhash')
    analyzer.Analyze('test data')
    results = analyzer.GetResults()
    first_result = results[0]
    self.assertIsInstance(first_result, analyzer_result.AnalyzerResult)
    self.assertEqual(first_result.analyzer_name, 'hashing')
    self.assertEqual(first_result.attribute_name, 'testhash_hash')
    self.assertEqual(first_result.attribute_value, '4')
    self.assertEqual(len(results), 1)


if __name__ == '__main__':
  unittest.main()
