#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tagging analysis plugin."""

from __future__ import unicode_literals

import unittest

from plaso.analysis import tagging
from plaso.lib import definitions
from plaso.lib import timelib

from tests import test_lib as shared_test_lib
from tests.analysis import test_lib


class TaggingAnalysisPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests the tagging analysis plugin."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'windows:prefetch',
       'timestamp': timelib.Timestamp.CopyFromString('2015-05-01 15:12:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'chrome:history:file_downloaded',
       'timestamp': timelib.Timestamp.CopyFromString('2015-05-01 05:06:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'something_else',
       'timestamp': timelib.Timestamp.CopyFromString('2015-02-19 08:00:01'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'data_type': 'windows:evt:record',
       'event_identifier': 538,
       'source_name': 'Security',
       'timestamp': timelib.Timestamp.CopyFromString('2016-05-25 13:00:06'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN},
      {'body': 'this is a message',
       'data_type': 'windows:evt:record',
       'event_identifier': 16,
       'timestamp': timelib.Timestamp.CopyFromString('2016-05-25 13:00:06'),
       'source_name': 'Messaging',
       'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  @shared_test_lib.skipUnlessHasTestFile(['tagging_file', 'valid.txt'])
  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    test_events = []
    for event_values in self._TEST_EVENTS:
      event, event_data = self._CreateTestEvent(event_values)
      test_events.append((event, event_data))

    test_file = self._GetTestFilePath(['tagging_file', 'valid.txt'])
    plugin = tagging.TaggingAnalysisPlugin()
    plugin.SetAndLoadTagFile(test_file)

    storage_writer = self._AnalyzeEvents(test_events, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)
    self.assertEqual(storage_writer.number_of_event_tags, 4)

    report = storage_writer.analysis_reports[0]
    self.assertIsNotNone(report)

    expected_text = 'Tagging plugin produced 4 tags.\n'
    self.assertEqual(report.text, expected_text)

    labels = []
    for event_tag in storage_writer.GetEventTags():
      labels.extend(event_tag.labels)

    self.assertEqual(len(labels), 5)

    # This is from a tag rule declared in objectfilter syntax.
    self.assertIn('application_execution', labels)
    # This is from a tag rule declared in dotty syntax.
    self.assertIn('login_attempt', labels)
    # This is from a rule using the "contains" operator
    self.assertIn('text_contains', labels)


if __name__ == '__main__':
  unittest.main()
