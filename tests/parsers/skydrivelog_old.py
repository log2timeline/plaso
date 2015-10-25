#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the skydrivelog_old parser."""

import unittest

from plaso.formatters import skydrivelog_old  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import skydrivelog_old as skydrivelog_old_parser

from tests.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveOldLogUnitTest(test_lib.ParserTestCase):
  """Tests for the skydrivelog_old parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = skydrivelog_old_parser.SkyDriveOldLogParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'skydrive_old.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 18)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:22:28.999')
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:22:29.702')
    self.assertEqual(event_objects[1].timestamp, expected_timestamp)
    self.assertEqual(event_objects[2].timestamp, expected_timestamp)
    self.assertEqual(event_objects[3].timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:22:58.344')
    self.assertEqual(event_objects[4].timestamp, expected_timestamp)
    self.assertEqual(event_objects[5].timestamp, expected_timestamp)

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
