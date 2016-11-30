# -*- coding: utf-8 -*- #
"""Tests for the bash history parser."""
import unittest

from plaso.lib import timelib
from plaso.parsers import bash_history

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class BashHistoryTest(test_lib.ParserTestCase):
  """Test for the bash history parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser_object = bash_history.BashParser()

  @shared_test_lib.skipUnlessHasTestFile([u'bash_history_desync'])
  def testParsingExtractionDesync(self):
    """Tests that the parser correctly handles a desynchronized file.

    A desynchronized file is one with half an event at the top. ie, it starts
    with a command line instead of a timestamp.
    """
    storage_writer = self._ParseFile(
        [u'bash_history_desync'], self._parser_object)
    events = storage_writer.events
    self._TestEventsFromFile(events)

  @shared_test_lib.skipUnlessHasTestFile([u'bash_history'])
  def testParsingExtractionSync(self):
    """Tests that the parser correctly handles a synchronised file.

    A synchronised file is one with an event at the top. ie, it starts
    with a timestamp line.
    """
    storage_writer = self._ParseFile([u'bash_history'], self._parser_object)
    events = storage_writer.events
    self._TestEventsFromFile(events)

  def _TestEventsFromFile(self, events):
    """Validates that all events are as expected.

    Args:
      events: events to check values of.
    """
    # There are three events in the test log
    self.assertEqual(len(events), 3)

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


if __name__ == '__main__':
  unittest.main()
