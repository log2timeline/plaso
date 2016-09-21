# -*- coding: utf-8 -*-
"""Tests for the analyzer manager."""

import unittest

from plaso.analyzers import interface
from plaso.analyzers import manager
from plaso.containers import analyzer_result

from tests.analyzers import test_lib


class TestAnalyzer(interface.BaseAnalyzer):
  """Test analyzer."""

  NAME = u'testanalyze'

  def __init__(self):
    """Initializes a test analyzer."""
    super(TestAnalyzer, self).__init__()
    self._results = []

  def _AddResult(self):
    """Adds a  result to the results object."""
    if not self._results:
      result = analyzer_result.AnalyzerResult()
      result.attribute_name = u'test_result'
      result.attribute_value = u'is_vegetable'
      self._results.append(result)

  def Analyze(self, data):
    """Processes a block of data, updating the state of the analyzer

    Args:
      data(str): a string of data to process.
    """
    self._AddResult()

  def GetResults(self):
    """Retrieves the results of the processing of all data.

    Returns:
      list(AnalyzerResult): results.
    """
    return self._results

  def Reset(self):
    """Resets the internal state of the analyzer."""
    self._results = []


class AnalyzersManagerTest(test_lib.AnalyzerTestCase):
  """Tests for the analyzers manager."""

  # pylint: disable=protected-access

  def tearDown(self):
    """Cleans up after running an individual test."""
    try:
      manager.AnalyzersManager.DeregisterAnalyzer(TestAnalyzer)
    except KeyError:
      pass

  def testAnalyzerRegistration(self):
    """Tests the registration and deregistration of analyzers."""
    number_of_analyzers = len(manager.AnalyzersManager._analyzer_classes)
    manager.AnalyzersManager.RegisterAnalyzer(TestAnalyzer)
    self.assertEqual(
        number_of_analyzers + 1, len(
            manager.AnalyzersManager._analyzer_classes))

    with self.assertRaises(KeyError):
      manager.AnalyzersManager.RegisterAnalyzer(TestAnalyzer)

    manager.AnalyzersManager.DeregisterAnalyzer(TestAnalyzer)

    self.assertEqual(
        number_of_analyzers, len(manager.AnalyzersManager._analyzer_classes))

  def testGetAnalyzerInstance(self):
    """Tests the GetAnalyzerInstance function."""
    manager.AnalyzersManager.RegisterAnalyzer(TestAnalyzer)
    analyzer = manager.AnalyzersManager.GetAnalyzerInstance(u'testanalyze')
    self.assertIsNotNone(analyzer)
    self.assertEqual(analyzer.NAME, u'testanalyze')

    analyzer = manager.AnalyzersManager.GetAnalyzerInstance(u'testanalyze')
    self.assertIsNotNone(analyzer)
    self.assertEqual(analyzer.NAME, u'testanalyze')

    with self.assertRaises(KeyError):
      manager.AnalyzersManager.GetAnalyzerInstance(u'bogus')
    manager.AnalyzersManager.DeregisterAnalyzer(TestAnalyzer)

  def testGetAnalyzerInstances(self):
    """Tests getting analyzer objects by name."""
    analyzer_names = manager.AnalyzersManager.GetAnalyzerNames()
    analyzers = manager.AnalyzersManager.GetAnalyzerInstances(analyzer_names)
    self.assertEqual(len(analyzer_names), len(analyzers))
    for analyzer in analyzers:
      self.assertIsInstance(analyzer, interface.BaseAnalyzer)


if __name__ == '__main__':
  unittest.main()
