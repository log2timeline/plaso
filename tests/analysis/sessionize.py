#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the sessionize analysis plugin."""

import collections
import unittest

from plaso.analysis import sessionize
from plaso.containers import reports
from plaso.lib import definitions

from tests.analysis import test_lib


class SessionizeAnalysisPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests the sessionize analysis plugin."""

  _TEST_EVENTS = [
      {'_parser_chain': 'test_parser',
       'data_type': 'test:event',
       'timestamp': '2015-05-01 00:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'_parser_chain': 'test_parser',
       'data_type': 'test:event',
       'timestamp': '2015-05-01 00:09:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'_parser_chain': 'test_parser',
       'data_type': 'test:event',
       'timestamp': '2015-05-01 00:18:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'_parser_chain': 'test_parser',
       'data_type': 'test:event',
       'timestamp': '2015-05-01 01:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'_parser_chain': 'test_parser',
       'data_type': 'test:event',
       'timestamp': '2015-05-01 01:09:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testTagAndCompileReport(self):
    """Tests the Sessionize plugin."""
    plugin = sessionize.SessionizeAnalysisPlugin()
    plugin.SetMaximumPause(10)

    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)
    self.assertIsNotNone(analysis_report)

    self.assertEqual(analysis_report.plugin_name, 'sessionize')

    expected_analysis_counter = collections.Counter({
        'session_0': 3,
        'session_1': 2})
    self.assertEqual(
        analysis_report.analysis_counter, expected_analysis_counter)

    number_of_event_tags = storage_writer.GetNumberOfAttributeContainers(
        'event_tag')
    self.assertEqual(number_of_event_tags, 5)


if __name__ == '__main__':
  unittest.main()
