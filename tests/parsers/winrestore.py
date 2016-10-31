#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Restore Point (rp.log) file parser."""

import unittest

from plaso.formatters import winrestore  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winrestore

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class RestorePointLogParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Restore Point (rp.log) file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'rp.log'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = winrestore.RestorePointLogParser()
    storage_writer = self._ParseFile([u'rp.log'], parser_object)

    self.assertEqual(len(storage_writer.events), 1)

    event_object = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-03-23 18:38:14.246954')
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.restore_point_event_type, 102)
    self.assertEqual(event_object.restore_point_type, 0)
    expected_description = u'Software Distribution Service 3.0'
    self.assertEqual(event_object.description, expected_description)

    expected_message = (
        u'{0:s} '
        u'Event type: BEGIN_NESTED_SYSTEM_CHANGE '
        u'Restore point type: UNKNOWN').format(expected_description)
    expected_message_short = expected_description

    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)


if __name__ == '__main__':
  unittest.main()
