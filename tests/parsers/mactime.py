#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the for mactime parser."""

import unittest

from plaso.formatters import mactime as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import mactime

from tests.parsers import test_lib


class MactimeTest(test_lib.ParserTestCase):
  """Tests the for mactime parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser_object = mactime.MactimeParser()
    storage_writer = self._ParseFile(
        [u'mactime.body'], parser_object)

    # The file contains 13 lines x 4 timestamps per line, which should be
    # 52 events in total. However several of these events have an empty
    # timestamp value and are omitted.
    # Total entries: 11 * 3 + 2 * 4 = 41
    self.assertEqual(len(storage_writer.events), 41)

    # Test this entry:
    # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
    # 1337961584|1337961585|0
    event_object = storage_writer.events[8]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:44')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    event_object = storage_writer.events[6]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:43')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEqual(event_object.inode, 16)

    event_object = storage_writer.events[7]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:45')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CHANGE_TIME)

    expected_filename = u'/a_directory/another_file'
    self.assertEqual(event_object.filename, expected_filename)
    self.assertEqual(event_object.mode_as_string, u'r/rrw-------')

    self._TestGetMessageStrings(
        event_object, expected_filename, expected_filename)


if __name__ == '__main__':
  unittest.main()
