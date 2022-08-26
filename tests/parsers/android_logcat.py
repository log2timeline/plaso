#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Android logcat output parser."""

import unittest

from plaso.containers import warnings
from plaso.parsers import android_logcat

from tests.parsers import test_lib


class AndroidLogcatUnitTest(test_lib.ParserTestCase):
  """Tests for Android Logcat output parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = android_logcat.AndroidLogcatParser()
    storage_writer = self._ParseFile(['android_logcat.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
      'date_time': '2022-01-01 01:02:03.123',
      'data_type': 'android:logcat',
      'pid': '1234',
      'tid': '1234',
      'priority': 'D',
      'tag': 'Test',
      'message': 'test message'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
