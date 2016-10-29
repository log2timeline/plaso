# -*- coding: utf-8 -*-
"""Tests for the Yara analyzer."""

import unittest

from plaso.containers import analyzer_result
from plaso.analyzers import yara_analyzer

from tests import test_lib as shared_test_lib


@shared_test_lib.skipUnlessHasTestFile([u'yara.rules'])
class YaraAnalyzerTest(shared_test_lib.BaseTestCase):
  """Test the Yara analyzer."""

  # pylint: disable=protected-access

  _RULE_FILE = [u'yara.rules']

  def testFileRuleParse(self):
    """Tests that the Yara analyzer can read rules."""
    analyzer = yara_analyzer.YaraAnalyzer()
    rule_path = self._GetTestFilePath(self._RULE_FILE)

    with open(rule_path, 'r') as rules_file:
      rules = rules_file.read()

    analyzer.SetRules(rules)
    self.assertIsNotNone(analyzer._rules)

  @shared_test_lib.skipUnlessHasTestFile([u'test_pe.exe'])
  def testMatchFile(self):
    """Tests that the Yara analyzer correctly matches a file."""
    analyzer = yara_analyzer.YaraAnalyzer()
    rule_path = self._GetTestFilePath(self._RULE_FILE)

    with open(rule_path, 'r') as rule_file:
      rule_string = rule_file.read()

    analyzer.SetRules(rule_string)
    target_path = self._GetTestFilePath([u'test_pe.exe'])

    with open(target_path, 'rb') as target_file:
      target_data = target_file.read()

    analyzer.Analyze(target_data)
    results = analyzer.GetResults()
    self.assertIsInstance(results, list)

    first_result = results[0]
    self.assertIsInstance(first_result, analyzer_result.AnalyzerResult)
    self.assertEqual(first_result.attribute_name, u'yara_match')
    self.assertEqual(first_result.analyzer_name, u'yara')
    self.assertEqual(first_result.attribute_value, u'PEfileBasic,PEfile')


if __name__ == '__main__':
  unittest.main()
