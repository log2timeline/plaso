# -*- coding: utf-8 -*- #
"""Tests for the bash history parser."""
import unittest

from plaso.lib import timelib
from plaso.parsers import bash_history

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class BashHistoryTest(test_lib.ParserTestCase):
  """Test for the bash history parser."""

  def _TestEventsFromFile(self, storage_writer):
    """Validates that all events are as expected.

    Args:
      storage_writer (FakeStorageWriter): storage writer.
    """
    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetEvents())

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-01 12:36:17')
    expected_command = u'/usr/lib/plaso'
    self.assertEqual(events[0].timestamp, expected_timestamp)
    self.assertEqual(events[0].command, expected_command)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-01 12:36:18')
    expected_command = u'/bin/bash'
    self.assertEqual(events[1].timestamp, expected_timestamp)
    self.assertEqual(events[1].command, expected_command)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-01 12:36:19')
    expected_command = u'/usr/local/bin/splunk -p 8080'
    self.assertEqual(events[2].timestamp, expected_timestamp)
    self.assertEqual(events[2].command, expected_command)

  @shared_test_lib.skipUnlessHasTestFile([u'bash_history_desync'])
  def testParsingExtractionDesync(self):
    """Tests that the parser correctly handles a desynchronized file.

    A desynchronized file is one with half an event at the top. That is, it
    starts with a command line instead of a timestamp.
    """
    parser = bash_history.BashHistoryParser()
    storage_writer = self._ParseFile([u'bash_history_desync'], parser)
    self._TestEventsFromFile(storage_writer)

  @shared_test_lib.skipUnlessHasTestFile([u'bash_history'])
  def testParsingExtractionSync(self):
    """Tests that the parser correctly handles a synchronized file.

    A synchronized file is one that starts with a timestamp line.
    """
    parser = bash_history.BashHistoryParser()
    storage_writer = self._ParseFile([u'bash_history'], parser)
    self._TestEventsFromFile(storage_writer)


if __name__ == '__main__':
  unittest.main()
