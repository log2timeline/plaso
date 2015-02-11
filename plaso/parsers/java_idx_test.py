#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Java Cache IDX file parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import java_idx as java_idx_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import java_idx
from plaso.parsers import test_lib


class IDXTest(test_lib.ParserTestCase):
  """Tests for Java Cache IDX file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = java_idx.JavaIDXParser()

  def testParse602(self):
    """Tests the Parse function on a version 602 IDX file."""
    test_file = self._GetTestFilePath(['java_602.idx'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 2)

    event_object = event_objects[0]

    idx_version_expected = 602
    self.assertEqual(event_object.idx_version, idx_version_expected)

    ip_address_expected = u'Unknown'
    self.assertEqual(event_object.ip_address, ip_address_expected)

    url_expected = u'http://www.gxxxxx.com/a/java/xxz.jar'
    self.assertEqual(event_object.url, url_expected)

    description_expected = u'File Hosted Date'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2010-05-05 01:34:19.720')
    self.assertEqual(
        event_object.timestamp, expected_timestamp)

    # Parse second event. Same metadata; different timestamp event.
    event_object = event_objects[1]

    self.assertEqual(event_object.idx_version, idx_version_expected)
    self.assertEqual(event_object.ip_address, ip_address_expected)
    self.assertEqual(event_object.url, url_expected)

    description_expected = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2010-05-05 03:52:31')
    self.assertEqual(event_object.timestamp, expected_timestamp)

  def testParse605(self):
    """Tests the Parse function on a version 605 IDX file."""
    test_file = self._GetTestFilePath(['java.idx'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 2)

    event_object = event_objects[0]

    idx_version_expected = 605
    self.assertEqual(event_object.idx_version, idx_version_expected)

    ip_address_expected = '10.7.119.10'
    self.assertEqual(event_object.ip_address, ip_address_expected)

    url_expected = (
        u'http://xxxxc146d3.gxhjxxwsf.xx:82/forum/dare.php?'
        u'hsh=6&key=b30xxxx1c597xxxx15d593d3f0xxx1ab')
    self.assertEqual(event_object.url, url_expected)

    description_expected = 'File Hosted Date'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2001-07-26 05:00:00'
    )
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Parse second event. Same metadata; different timestamp event.
    event_object = event_objects[1]

    self.assertEqual(event_object.idx_version, idx_version_expected)
    self.assertEqual(event_object.ip_address, ip_address_expected)
    self.assertEqual(event_object.url, url_expected)

    description_expected = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-01-13 16:22:01'
    )
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
