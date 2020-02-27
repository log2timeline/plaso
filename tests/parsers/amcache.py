#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the AMCache Registry plugin."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import amcache

from tests.parsers import test_lib


class AMCacheParserTest(test_lib.ParserTestCase):
  """Tests for the AMCache Registry plugin."""

  def testParse(self):
    """Tests the Parse function."""
    parser = amcache.AMCacheParser()

    storage_writer = self._ParseFile(['Amcache.hve'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1179)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '1992-06-19 22:22:17.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    expected_full_path = (
        'c:\\users\\user\\appdata\\local\\temp\\chocolatey\\'
        'is-f4510.tmp\\idafree50.tmp')
    self.assertEqual(event_data.full_path, expected_full_path)

    self.assertEqual(
        event_data.sha1, '82274eef0911a948f91425f5e5b0e730517fe75e')

    event = events[1148]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.name, 'FileInsight - File analysis tool')
    self.assertEqual(event_data.publisher, 'McAfee Inc.')

    expected_message = (
        'name: FileInsight - File analysis tool '
        'publisher: McAfee Inc. '
        'entry_type: AddRemoveProgram '
        'uninstall_key: [\'HKEY_LOCAL_MACHINE\\\\Software\\\\Wow6432Node\\\\'
        'Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\FileInsight\'] '
        'file_paths: [\'c:\\\\program files (x86)\\\\fileinsight\\\\plugins\', '
        '\'c:\\\\program files (x86)\\\\fileinsight\\\\plugins\\\\'
        'anomaly chart\', \'c:\\\\program files (x86)\\\\fileinsight\']')
    expected_short_message = 'name: FileInsight - File analysis tool'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseWithSystem(self):
    """Tests the Parse function with a SYSTEM Registry file."""
    parser = amcache.AMCacheParser()

    storage_writer = self._ParseFile(['SYSTEM'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 0)


if __name__ == '__main__':
  unittest.main()
