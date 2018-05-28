#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Trend Micro AV Log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import trendmicroav as _  # pylint: disable=unused-import
from plaso.parsers import trendmicroav

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class TrendMicroUnitTest(test_lib.ParserTestCase):
  """Tests for the Trend Micro AV Log parser."""

  @shared_test_lib.skipUnlessHasTestFile(['pccnt35.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser = trendmicroav.OfficeScanVirusDetectionParser()
    storage_writer = self._ParseFile(['pccnt35.log'], parser)

    # The file contains 3 lines which results in 3 events.
    self.assertEqual(storage_writer.number_of_events, 3)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[1]
    self.CheckTimestamp(event.timestamp, '2018-01-30 14:45:32.000000')

    # The third and last event has been edited to match the older, documented
    # format for log lines (without a Unix timestamp).
    event = events[2]
    self.CheckTimestamp(event.timestamp, '2018-01-30 14:46:00.000000')

    # Test the third event.

    self.assertEqual(event.path, 'C:\\temp\\')
    self.assertEqual(event.filename, 'eicar.com_.gstmp')

    expected_message = (
        r'Path: C:\temp\ File name: eicar.com_.gstmp '
        r'Eicar_test_1 : Failure (clean), moved (Real-time scan)')
    expected_short_message = r'C:\temp\ eicar.com_.gstmp Failure (clean), moved'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile(['OfcUrlf.log'])
  def testWebReputationParse(self):
    """Tests the Parse function."""
    parser = trendmicroav.OfficeScanWebReputationParser()
    storage_writer = self._ParseFile(['OfcUrlf.log'], parser)

    # The file contains 3 lines which results in 3 events.
    self.assertEqual(storage_writer.number_of_events, 4)

    # The order in which DSVParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[1]
    self.CheckTimestamp(event.timestamp, '2018-01-23 13:16:22.000000')

    # Test the third event.
    event = events[2]
    self.assertEqual(event.url, 'http://www.eicar.org/download/eicar.com')
    self.assertEqual(event.group_code, '4E')
    self.assertEqual(event.credibility_score, 49)

    expected_message = (
        'http://www.eicar.org/download/eicar.com '
        'Group: Malware Accomplice 4E Mode: Whitelist only Policy ID: 1 '
        'Credibility rating: 1 Credibility score: 49 Threshold value: 0 '
        'Accessed by: C:\\Users\\user\\Downloads\\wget.exe')
    expected_short_message = (
        'http://www.eicar.org/download/eicar.com Malware Accomplice')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

if __name__ == '__main__':
  unittest.main()
