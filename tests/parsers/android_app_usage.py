#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android Application Usage history parsers."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import android_app_usage as _  # pylint: disable=unused-import
from plaso.parsers import android_app_usage

from tests.parsers import test_lib


class AndroidAppUsageParserTest(test_lib.ParserTestCase):
  """Tests for the Android Application Usage History parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = android_app_usage.AndroidAppUsageParser()
    storage_writer = self._ParseFile(
        ['usage-history.xml'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 28)

    events = list(storage_writer.GetEvents())

    event = events[22]

    self.CheckTimestamp(event.timestamp, '2013-12-09 19:28:33.047000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(
        event_data.component,
        'com.sec.android.widgetapp.ap.hero.accuweather.menu.MenuAdd')

    expected_message = (
        'Package: '
        'com.sec.android.widgetapp.ap.hero.accuweather '
        'Component: '
        'com.sec.android.widgetapp.ap.hero.accuweather.menu.MenuAdd')
    expected_short_message = (
        'Package: com.sec.android.widgetapp.ap.hero.accuweather '
        'Component: com.sec.and...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[17]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.CheckTimestamp(event.timestamp, '2013-09-27 19:45:55.675000')

    self.assertEqual(event_data.package, 'com.google.android.gsf.login')

    expected_message = (
        'Package: '
        'com.google.android.gsf.login '
        'Component: '
        'com.google.android.gsf.login.NameActivity')
    expected_short_message = (
        'Package: com.google.android.gsf.login '
        'Component: com.google.android.gsf.login...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
