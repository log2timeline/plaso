#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the skydrivelog parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import skydrivelog as skydrivelog_formatter
from plaso.lib import timelib_test
from plaso.parsers import skydrivelog
from plaso.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveLogUnitTest(test_lib.ParserTestCase):
  """Tests for the skydrivelog parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = skydrivelog.SkyDriveLogParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['skydrive.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEquals(len(event_objects), 18)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-08-01 21:22:28.999')
    self.assertEquals(event_objects[0].timestamp, expected_timestamp)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-08-01 21:22:29.702')
    self.assertEquals(event_objects[1].timestamp, expected_timestamp)
    self.assertEquals(event_objects[2].timestamp, expected_timestamp)
    self.assertEquals(event_objects[3].timestamp, expected_timestamp)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-08-01 21:22:58.344')
    self.assertEquals(event_objects[4].timestamp, expected_timestamp)
    self.assertEquals(event_objects[5].timestamp, expected_timestamp)

    expected_msg = (
        u'[global.cpp:626!logVersionInfo] (DETAIL) 17.0.2011.0627 (Ship)')
    expected_msg_short = (
        u'17.0.2011.0627 (Ship)')
    self._TestGetMessageStrings(
        event_objects[0], expected_msg, expected_msg_short)

    expected_msg = (
        u'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
        u'103%3bLR%3d12345678905623%3aEP%3d2')
    expected_msg_short = (
        u'SyncToken = LM%3d12345678905670%3bID%3d1234567890E059C0!'
        u'103%3bLR%3d1234567890...')
    self._TestGetMessageStrings(
        event_objects[3], expected_msg, expected_msg_short)

    expected_string = (
        u'SyncToken = Not a sync token (\xe0\xe8\xec\xf2\xf9)!')
    self._TestGetMessageStrings(
        event_objects[17], expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
