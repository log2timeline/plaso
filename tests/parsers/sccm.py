#!/usr/bin/env python3
# -*_ coding: utf-8 -*-
"""Tests for the SCCM Logs Parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import sccm as _  # pylint: disable=unused-import
from plaso.parsers import sccm

from tests.parsers import test_lib


class SCCMLogsUnitTest(test_lib.ParserTestCase):
  """Tests for the SCCM Logs Parser."""

  def testParse(self):
    """Tests for the Parse function."""
    parser = sccm.SCCMParser()
    storage_writer = self._ParseFile(['sccm_various.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2014-11-29 01:03:19.766000')

    # Test timestamps with seven digits after seconds.
    event = events[3]

    self.CheckTimestamp(event.timestamp, '2015-01-02 10:22:50.873496')

    # Test timestamps with '-' in microseconds.
    event = events[7]

    self.CheckTimestamp(event.timestamp, '2014-12-28 18:59:43.373000')

    # Test timestamps with '+' in microseconds.
    event = events[9]

    self.CheckTimestamp(event.timestamp, '2014-11-23 17:52:13.827000')

    # Test timestamps with 2 digit UTC offset
    event = events[8]

    self.CheckTimestamp(event.timestamp, '2014-11-26 05:20:47.594000')

    # Test full and short message formats.
    event = events[4]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'ContentAccess Releasing content request '
        '{4EA97AD6-E7E2-4583-92B9-21F532501337}')

    expected_short_message = (
        'Releasing content request '
        '{4EA97AD6-E7E2-4583-92B9-21F532501337}')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
