#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows Restore Point (rp.log) file parser."""

import unittest

from plaso.formatters import winrestore as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winrestore

from tests.parsers import test_lib


class RestorePointLogParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Restore Point (rp.log) file parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = winrestore.RestorePointLogParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'rp.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 1)

    event_object = event_objects[0]

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
