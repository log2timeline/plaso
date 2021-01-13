#!/usr/bin/env python3
# -*- coding: utf-8 -*- #
"""Tests for the bash history parser."""

import unittest

from plaso.parsers import bash_history

from tests.parsers import test_lib


class BashHistoryTest(test_lib.ParserTestCase):
  """Test for the bash history parser."""

  def _TestEventsFromFile(self, storage_writer, expected_number_of_warnings=0):
    """Validates that all events are as expected.

    Args:
      storage_writer (FakeStorageWriter): storage writer.
      expected_number_of_warnings (Optional[int]): number of expected warnings.
          generated.
    """
    self.assertEqual(
        storage_writer.number_of_warnings, expected_number_of_warnings)
    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'command': '/usr/lib/plaso',
        'data_type': 'bash:history:command',
        'timestamp': '2013-10-01 12:36:17.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'command': '/bin/bash',
        'data_type': 'bash:history:command',
        'timestamp': '2013-10-01 12:36:18.000000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'command': '/usr/local/bin/splunk -p 8080',
        'data_type': 'bash:history:command',
        'timestamp': '2013-10-01 12:36:19.000000'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

  def testParsingExtractionDesync(self):
    """Tests that the parser correctly handles a desynchronized file.

    A desynchronized file is one with half an event at the top. That is, it
    starts with a command line instead of a timestamp.
    """
    parser = bash_history.BashHistoryParser()
    storage_writer = self._ParseFile(['bash_history_desync'], parser)
    self._TestEventsFromFile(storage_writer, expected_number_of_warnings=1)

  def testParsingExtractionSync(self):
    """Tests that the parser correctly handles a synchronized file.

    A synchronized file is one that starts with a timestamp line.
    """
    parser = bash_history.BashHistoryParser()
    storage_writer = self._ParseFile(['bash_history'], parser)
    self._TestEventsFromFile(storage_writer)


if __name__ == '__main__':
  unittest.main()
