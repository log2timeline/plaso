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

  def _GetEventObjectsFromQueue(self, event_queue_consumer):
    """Retrieves the event objects from the queue consumer.

    Args:
      event_queue_consumer: an event object queue consumer object (instance of
                            TestItemQueueConsumer).

    Returns:
      A list of event objects (instances of EventObject).
    """
    # The inner workings of csv does not provide a predictable order
    # of events. Hence sort the resulting event objects to make sure they are
    # predictable for the tests.
    event_objects = super(MactimeTest, self)._GetEventObjectsFromQueue(
        event_queue_consumer)
    return sorted(
        event_objects, key=lambda event_object: event_object.timestamp)

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
    event_object = event_objects[21]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:43')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.ACCESS_TIME)
    self.assertEqual(event_object.inode, 16)

    expected_string = u'/a_directory/another_file'
    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[22]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:44')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)

    event_object = event_objects[23]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-05-25 15:59:45')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CHANGE_TIME)
    self.assertEqual(event_object.filename, u'/a_directory/another_file')
    self.assertEqual(event_object.mode_as_string, u'r/rrw-------')


if __name__ == '__main__':
  unittest.main()
