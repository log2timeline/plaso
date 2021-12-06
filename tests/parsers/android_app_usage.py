#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Android Application Usage history parsers."""

import unittest

from plaso.parsers import android_app_usage

from tests.parsers import test_lib


class AndroidAppUsageParserTest(test_lib.ParserTestCase):
  """Tests for the Android Application Usage History parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = android_app_usage.AndroidAppUsageParser()
    storage_writer = self._ParseFile(['usage-history.xml'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 28)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'android:event:last_resume_time',
        'date_time': '2013-12-09 19:28:33.047',
        'component': (
            'com.sec.android.widgetapp.ap.hero.accuweather.menu.MenuAdd'),
        'package': 'com.sec.android.widgetapp.ap.hero.accuweather'}

    self.CheckEventValues(storage_writer, events[22], expected_event_values)

    expected_event_values = {
        'data_type': 'android:event:last_resume_time',
        'date_time': '2013-09-27 19:45:55.675',
        'component': 'com.google.android.gsf.login.NameActivity',
        'package': 'com.google.android.gsf.login'}

    self.CheckEventValues(storage_writer, events[17], expected_event_values)


if __name__ == '__main__':
  unittest.main()
