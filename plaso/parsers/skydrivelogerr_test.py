#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SkyDriveLogErr log parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import skydrivelogerr as skydrivelogerr_formatter
from plaso.lib import timelib
from plaso.parsers import skydrivelogerr
from plaso.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class SkyDriveLogErrorUnitTest(test_lib.ParserTestCase):
  """A unit test for the SkyDriveLogErr parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = skydrivelogerr.SkyDriveLogErrorParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'skydriveerr.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 19)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-25 16:03:23.291')
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-25 16:03:24.649')
    self.assertEqual(event_objects[1].timestamp, expected_timestamp)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-08-01 21:27:44.124')
    self.assertEqual(event_objects[18].timestamp, expected_timestamp)

    expected_detail = (
        u'StartLocalTime: 2013-07-25-180323.291 PID=0x8f4 TID=0x718 '
        u'ContinuedFrom=')
    self.assertEqual(event_objects[0].detail, expected_detail)

    expected_string = (
        u'Logging started. Version= 17.0.2011.0627 ({0:s})').format(
            expected_detail)

    expected_string_short = u'Logging started. Version= 17.0.2011.0627'
    self._TestGetMessageStrings(
        event_objects[0], expected_string, expected_string_short)

    expected_string = (
        u'[AUTH authapi.cpp(280)] Sign in failed : '
        u'DRX_E_AUTH_NO_VALID_CREDENTIALS')
    expected_string_short = u'Sign in failed : DRX_E_AUTH_NO_VALID_CREDENTIALS'
    self._TestGetMessageStrings(
        event_objects[1], expected_string, expected_string_short)

    expected_string = (
        u'[WNS absconn.cpp(177)] Received data from server '
        u'(dwID=0x0;dwSize=0x3e;pbData=PNG 9 CON 48  <ping-response>'
        u'<wait>44</wait></ping-response>)')
    expected_string_short = u'Received data from server'
    self._TestGetMessageStrings(
        event_objects[18], expected_string, expected_string_short)

  def testParseUnicode(self):
    """Tests the Parse function on Unicode data."""
    test_file = self._GetTestFilePath([u'skydriveerr-unicode.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 19)

    # TODO: check if this test passes because the encoding on my system
    # is UTF-8.
    expected_text = (
        u'No node found named Passport-Jméno-člena')
    self.assertEqual(event_objects[3].text, expected_text)


if __name__ == '__main__':
  unittest.main()
