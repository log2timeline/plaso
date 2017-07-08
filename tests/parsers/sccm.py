#!/usr/bin/python
# -*_ coding: utf-8 -*-
"""Tests for the SCCM Logs Parser."""

import unittest

from plaso.formatters import sccm  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import sccm

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class SCCMLogsUnitTest(test_lib.ParserTestCase):
  """Tests for the SCCM Logs Parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'sccm_various.log'])
  def testParse(self):
    """Tests for the Parse function."""
    parser = sccm.SCCMParser()
    storage_writer = self._ParseFile([u'sccm_various.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    event = events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-11-28 14:03:19.766')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Test timestamps with seven digits after seconds.
    event = events[3]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-01-02 10:22:50.873496')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Test timestamps with '-' in microseconds.
    event = events[7]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-12-28 07:59:43.373')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Test timestamps with '+' in microseconds.
    event = events[9]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-11-24 09:52:13.827')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Test full and short message formats.
    event = events[4]
    expected_message = (
        u'ContentAccess Releasing content request '
        u'{4EA97AD6-E7E2-4583-92B9-21F532501337}')

    expected_short_message = (
        u'Releasing content request '
        u'{4EA97AD6-E7E2-4583-92B9-21F532501337}')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
