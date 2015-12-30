#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the for mactime parser."""

import unittest

from plaso.formatters import mactime as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import mactime
from plaso.serializer import protobuf_serializer

from tests.parsers import test_lib


class MactimeUnitTest(test_lib.ParserTestCase):
  """Tests the for mactime parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = mactime.MactimeParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'mactime.body'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # The file contains 13 lines x 4 timestamps per line, which should be
    # 52 events in total. However several of these events have an empty
    # timestamp value and are omitted.
    # Total entries: 11 * 3 + 2 * 4 = 41
    self.assertEqual(len(event_objects), 41)

    # Test this entry:
    # 0|/a_directory/another_file|16|r/rrw-------|151107|5000|22|1337961583|
    # 1337961584|1337961585|0
    event_object = event_objects[6]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:43')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEqual(event_object.inode, 16)

    event_object = event_objects[6]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:43')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)

    expected_string = u'/a_directory/another_file'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[8]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:44')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    event_object = event_objects[7]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:45')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CHANGE_TIME)
    self.assertEqual(event_object.filename, u'/a_directory/another_file')
    self.assertEqual(event_object.mode_as_string, u'r/rrw-------')

    event_object = event_objects[37]

    self.assertEqual(event_object.inode, 4)

    # Serialize the event objects.
    serialized_events = []
    serializer = protobuf_serializer.ProtobufEventObjectSerializer
    for event_object in event_objects:
      serialized_events.append(serializer.WriteSerialized(event_object))

    self.assertEqual(len(serialized_events), len(event_objects))


if __name__ == '__main__':
  unittest.main()
