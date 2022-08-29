#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Android logcat output parser."""

import unittest

from plaso.parsers import android_logcat

from tests.parsers import test_lib


class AndroidLogcatUnitTest(test_lib.ParserTestCase):
  """Tests for Android Logcat output parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = android_logcat.AndroidLogcatParser()
    storage_writer = self._ParseFile(['android_logcat.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 15)

    events = list(storage_writer.GetSortedEvents())

    # A default threadtime logcat line
    expected_event_values = {
        'data_type': 'android:logcat',
        'pid': '1234',
        'tid': '1234',
        'priority': 'D',
        'tag': 'Test',
        'message': 'test message'}

    events[0].date_time.CopyToDateTimeString().endswith('-01-01 01:02:03.123')
    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # A default time logcat line
    expected_event_values = {
        'data_type': 'android:logcat',
        'pid': '190',
        'tid': None,
        'priority': 'I',
        'tag': 'sometag',
        'message': 'Some other test message'}

    events[1].date_time.CopyToDateTimeString().endswith('-01-02 01:02:04.156')
    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'date_time': '2022-01-02 17:20:08.875325',
        'data_type': 'android:logcat',
        'pid': '9346',
        'tid': '9346' ,
        'priority': 'E',
        'tag': 'ndroid.calendar',
        'uid': None,
        'message':
        'Not starting debugger since process cannot load the jdwp agent.'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'date_time': '2022-01-02 07:20:09.171000',
        'data_type': 'android:logcat',
        'pid': '1885',
        'tid': '3066' ,
        'priority': 'E',
        'tag': 'App',
        'message': 'Bad call made by uid 1010158.'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'date_time': '2022-01-02 07:20:09.171000',
        'data_type': 'android:logcat',
        'pid': '1885',
        'tid': '3066' ,
        'priority': 'E',
        'tag': 'App',
        'uid': '1000',
        'message': 'Bad call made by uid 1010158.'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'date_time': '2022-01-02 17:42:10.613472',
        'data_type': 'android:logcat',
        'pid': '1080',
        'tid': None,
        'priority': 'I',
        'tag': 'CHRE',
        'message': '@ 1210504.750: [ImuCal] [GYRO_RPS] (s0) Temp Intercept: '
            '-.001133, -.000088, -.001676'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)


if __name__ == '__main__':
  unittest.main()
