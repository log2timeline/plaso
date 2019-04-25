#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the sessionize analysis plugin."""

from __future__ import unicode_literals

import unittest

from plaso.analysis import sessionize
from plaso.lib import timelib

from tests.analysis import test_lib


class SessionizeAnalysisPluginTest(test_lib.AnalysisPluginTestCase):
  """Tests the sessionize analysis plugin."""

  _TEST_EVENTS = [
      {'timestamp': timelib.Timestamp.CopyFromString('2015-05-01 00:00:00')},
      {'timestamp': timelib.Timestamp.CopyFromString('2015-05-01 00:09:00')},
      {'timestamp': timelib.Timestamp.CopyFromString('2015-05-01 00:18:00')},
      {'timestamp': timelib.Timestamp.CopyFromString('2015-05-01 01:00:00')},
      {'timestamp': timelib.Timestamp.CopyFromString('2015-05-01 01:09:00')},
  ]

  def testTagAndCompileReport(self):
    """Tests the Sessionize plugin."""
    test_events = []
    for event_dictionary in self._TEST_EVENTS:
      event = self._CreateTestEventObject(event_dictionary)
      test_events.append(event)

    plugin = sessionize.SessionizeAnalysisPlugin()
    plugin.SetMaximumPause(10)

    storage_writer = self._AnalyzeEvents(test_events, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)
    self.assertEqual(storage_writer.number_of_event_tags, 5)

    report = storage_writer.analysis_reports[0]
    expected_report_text = (
        'Sessionize plugin identified 2 sessions and applied 5 tags.\n'
        '\tSession 0: 3 events\n'
        '\tSession 1: 2 events')
    self.assertEqual(report.text, expected_report_text)


if __name__ == '__main__':
  unittest.main()
