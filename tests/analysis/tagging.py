#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tagging analysis plugin."""

import collections
import unittest

from plaso.analysis import tagging
from plaso.containers import events
from plaso.containers import reports
from plaso.lib import definitions

from tests.analysis import test_lib


class TaggingAnalysisPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests the tagging analysis plugin."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'_parser_chain': 'winprefetch',
       'data_type': 'windows:prefetch',
       'timestamp': '2015-05-01 15:12:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'_parser_chain': 'sqlite/chrome_history',
       'data_type': 'chrome:history:file_downloaded',
       'timestamp': '2015-05-01 05:06:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'_parser_chain': 'test_parser',
       'data_type': 'something_else',
       'timestamp': '2015-02-19 08:00:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'_parser_chain': 'winevt',
       'data_type': 'windows:evt:record',
       'event_identifier': 538,
       'source_name': 'Security',
       'timestamp': '2016-05-25 13:00:06',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'_parser_chain': 'winevt',
       'body': 'this is a message',
       'data_type': 'windows:evt:record',
       'event_identifier': 16,
       'source_name': 'Messaging',
       'timestamp': '2016-05-25 13:00:06',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    test_file_path = self._GetTestFilePath(['tagging_file', 'valid.txt'])
    self._SkipIfPathNotExists(test_file_path)

    plugin = tagging.TaggingAnalysisPlugin()
    plugin.SetAndLoadTagFile(test_file_path)

    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)
    self.assertIsNotNone(analysis_report)

    self.assertEqual(analysis_report.plugin_name, 'tagging')

    expected_analysis_counter = collections.Counter({
        'application_execution': 1,
        'event_tags': 4,
        'file_downloaded': 1,
        'login_attempt': 1,
        'security_event': 1,
        'text_contains': 1})
    self.assertEqual(
        analysis_report.analysis_counter, expected_analysis_counter)

    number_of_event_tags = storage_writer.GetNumberOfAttributeContainers(
        'event_tag')
    self.assertEqual(number_of_event_tags, 4)

    labels = []
    for event_tag in storage_writer.GetAttributeContainers(
        events.EventTag.CONTAINER_TYPE):
      labels.extend(event_tag.labels)

    self.assertEqual(len(labels), 5)

    expected_labels = [
        'application_execution', 'file_downloaded', 'login_attempt',
        'security_event', 'text_contains']
    self.assertEqual(sorted(labels), expected_labels)


if __name__ == '__main__':
  unittest.main()
