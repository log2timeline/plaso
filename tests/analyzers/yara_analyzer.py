#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Yara analyzer."""

import unittest

from plaso.containers import analyzer_result
from plaso.analyzers import yara_analyzer

from tests import test_lib as shared_test_lib


class YaraAnalyzerTest(shared_test_lib.BaseTestCase):
  """Test the Yara analyzer."""

  # pylint: disable=protected-access

  def _ReadTestRuleFile(self):
    """Reads the test Yara rules file.

    Returns:
      str: contents of the test Yara rules file.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    yara_rules_path = self._GetTestFilePath(['rules.yara'])
    self._SkipIfPathNotExists(yara_rules_path)

    with open(yara_rules_path, 'r', encoding='utf-8') as file_object:
      return file_object.read()

  def testFileRuleParse(self):
    """Tests that the Yara analyzer can read rules."""
    test_yara_rules = self._ReadTestRuleFile()

    analyzer = yara_analyzer.YaraAnalyzer()
    analyzer.SetRules(test_yara_rules)

    self.assertIsNotNone(analyzer._rules)

  def testMatchFile(self):
    """Tests that the Yara analyzer correctly matches a file."""
    test_yara_rules = self._ReadTestRuleFile()

    test_file_path = self._GetTestFilePath(['test_pe.exe'])
    self._SkipIfPathNotExists(test_file_path)

    analyzer = yara_analyzer.YaraAnalyzer()
    analyzer.SetRules(test_yara_rules)

    with open(test_file_path, 'rb') as file_object:
      test_data = file_object.read()

    analyzer.Analyze(test_data)

    results = analyzer.GetResults()
    self.assertIsInstance(results, list)

    first_result = results[0]
    self.assertIsInstance(first_result, analyzer_result.AnalyzerResult)
    self.assertEqual(first_result.attribute_name, 'yara_match')
    self.assertEqual(first_result.analyzer_name, 'yara')
    self.assertEqual(first_result.attribute_value, ['PEfileBasic', 'PEfile'])


if __name__ == '__main__':
  unittest.main()
