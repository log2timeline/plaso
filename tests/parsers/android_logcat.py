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

    storage_writer = self._ParseFile(
        ['android_logcat.log'], parser, knowledge_base_values={'year': 1990})

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 8)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'date_time': '1990-01-01 01:02:03.123000',
        'data_type': 'android:logcat',
        'pid': '1234',
        'tid': '1234',
        'priority': 'D',
        'tag': 'threadtime',
        'message': 'test of default threadtime format'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'date_time': '1990-01-02 01:02:04.156000',
        'data_type': 'android:logcat',
        'pid': '190',
        'tid': None,
        'priority': 'I',
        'tag': 'sometag',
        'message': 'test of default time format'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'date_time': '2022-01-02 01:20:03.171000',
        'data_type': 'android:logcat',
        'pid': '1885',
        'tid': '3066' ,
        'priority': 'E',
        'tag': 'App',
        'uid': None,
        'message': 'test of threadtime w/ UTC and year'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'date_time': '2022-01-02 01:20:03.171000',
        'data_type': 'android:logcat',
        'pid': '1885',
        'tid': '3066' ,
        'priority': 'E',
        'tag': 'App',
        'uid': '1000',
        'message': 'test of threadtime w/ UTC, year and uid'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'date_time': '2022-01-02 01:20:07.171997',
        'data_type': 'android:logcat',
        'pid': '1885',
        'tid': '3066' ,
        'priority': 'E',
        'tag': 'App',
        'uid': '1000',
        'message': 'test of threadtime w/ year, uid, usec'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'date_time': '2022-01-02 11:20:07.171997',
        'data_type': 'android:logcat',
        'pid': '9346',
        'tid': '9347' ,
        'priority': 'E',
        'tag': 'AppTag',
        'uid': None,
        'message': 'test of threadtime w/ year, zone, usec'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'date_time': '2022-01-02 11:42:10.613472',
        'data_type': 'android:logcat',
        'pid': '1179',
        'tid': None,
        'priority': 'I',
        'tag': 'AppTag',
        'uid': '1080',
        'message': 'test of time w/ zone, uid, year'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'date_time': '2022-01-02 11:44:23.183801',
        'data_type': 'android:logcat',
        'pid': '1179',
        'tid': None,
        'priority': 'I',
        'tag': 'AppTag',
        'uid': None,
        'message': 'test of time w/ zone, year'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)


if __name__ == '__main__':
  unittest.main()
