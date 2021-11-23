# -*- coding: utf-8 -*
"""Tests for the GCP Logging parser."""

import unittest

from plaso.parsers import gcp_logging

from tests.parsers import test_lib

class GCPLoggingUnitTest(test_lib.ParserTestCase):
  """Tests for the GCP Logging parser."""

  def testParseGCPLogs(self):
    """Tests the _ParseLogJSON function."""
    parser = gcp_logging.GCPLogsParser()
    path_segments = ['gcp_logging.json']

    storage_writer = self._ParseFile(path_segments, parser)

    self.assertEqual(storage_writer.number_of_events, 9)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_timestamps = [
      "2021-10-19 02:57:47.339377",
      "2021-10-19 02:57:39.354769",
      "2021-10-19 02:55:51.658015",
      "2021-10-19 02:55:46.097818",
      "2021-10-19 02:43:48.064377",
      "2021-10-19 02:42:22.986298",
      "2021-10-19 02:42:13.839954",
      "2021-10-19 02:05:41.496590",
      "2021-10-19 02:04:00.272384"
    ]

    expected_event_values = {
      'user': 'fakeemailxyz@gmail.com'
    }

    for index, event in enumerate(events):
      self.CheckTimestamp(event.timestamp, expected_timestamps[index])
      # Last element is a text_payload
      if index != len(expected_timestamps) -1:
        self.CheckEventValues(storage_writer, event, expected_event_values)


if __name__ == '__main__':
  unittest.main()
