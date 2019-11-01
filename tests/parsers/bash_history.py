#!/usr/bin/env python3
# -*- coding: utf-8 -*- #
"""Tests for the bash history parser."""

from __future__ import unicode_literals

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

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-10-01 12:36:17.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.command, '/usr/lib/plaso')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-10-01 12:36:18.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.command, '/bin/bash')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-10-01 12:36:19.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.command, '/usr/local/bin/splunk -p 8080')

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

    # TODO: add test for message string


if __name__ == '__main__':
  unittest.main()
