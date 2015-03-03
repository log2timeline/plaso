#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android Application Usage history parsers."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import android_app_usage as android_app_usage_formatter
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import android_app_usage
from plaso.parsers import test_lib


class AndroidAppUsageParserTest(test_lib.ParserTestCase):
  """Tests for the Android Application Usage History parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = android_app_usage.AndroidAppUsageParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'usage-history.xml'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 28)

    event_object = event_objects[22]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-09 19:28:33.047000')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.component,
        'com.sec.android.widgetapp.ap.hero.accuweather.menu.MenuAdd')

    expected_msg = (
        u'Package: '
        u'com.sec.android.widgetapp.ap.hero.accuweather '
        u'Component: '
        u'com.sec.android.widgetapp.ap.hero.accuweather.menu.MenuAdd')
    expected_msg_short = (
        u'Package: com.sec.android.widgetapp.ap.hero.accuweather '
        u'Component: com.sec.and...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[17]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-09-27 19:45:55.675000')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(event_object.package, 'com.google.android.gsf.login')

    expected_msg = (
        u'Package: '
        u'com.google.android.gsf.login '
        u'Component: '
        u'com.google.android.gsf.login.NameActivity')
    expected_msg_short = (
        u'Package: com.google.android.gsf.login '
        u'Component: com.google.android.gsf.login...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
