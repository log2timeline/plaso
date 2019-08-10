#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Sophos Anti-Virus log (SAV.txt) parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import sophos_av as _  # pylint: disable=unused-import
from plaso.parsers import sophos_av

from tests.parsers import test_lib


class SophosAVLogParserTest(test_lib.ParserTestCase):
  """Tests for the Sophos Anti-Virus log (SAV.txt) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = sophos_av.SophosAVLogParser()
    storage_writer = self._ParseFile(['sav.txt'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2010-07-20 18:38:14.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'File "C:\\Documents and Settings\\Administrator\\Desktop\\'
        'sxl_test_50.com" belongs to virus/spyware \'LiveProtectTest\'.')
    expected_short_message = '{0:s}...'.format(expected_message[:77])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
