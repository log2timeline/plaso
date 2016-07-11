#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Android Application Usage history parsers."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import android_app_usage as android_app_usage_formatter
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import android_app_usage

from tests.parsers import test_lib


class AndroidAppUsageParserTest(test_lib.ParserTestCase):
  """Tests for the Android Application Usage History parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser_object = android_app_usage.AndroidAppUsageParser()
    storage_writer = self._ParseFile(
        [u'usage-history.xml'], parser_object)

    self.assertEqual(len(storage_writer.events), 28)

    event_object = storage_writer.events[22]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-09 19:28:33.047000')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.component,
        u'com.sec.android.widgetapp.ap.hero.accuweather.menu.MenuAdd')

    expected_msg = (
        u'Package: '
        u'com.sec.android.widgetapp.ap.hero.accuweather '
        u'Component: '
        u'com.sec.android.widgetapp.ap.hero.accuweather.menu.MenuAdd')
    expected_msg_short = (
        u'Package: com.sec.android.widgetapp.ap.hero.accuweather '
        u'Component: com.sec.and...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = storage_writer.events[17]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-09-27 19:45:55.675000')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.package, u'com.google.android.gsf.login')

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
