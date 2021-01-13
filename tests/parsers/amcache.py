#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the AMCache Registry plugin."""

import unittest

from plaso.parsers import amcache

from tests.parsers import test_lib


class AMCacheParserTest(test_lib.ParserTestCase):
  """Tests for the AMCache Registry plugin."""

  def testParse(self):
    """Tests the Parse function."""
    parser = amcache.AMCacheParser()

    storage_writer = self._ParseFile(['Amcache.hve'], parser)

    # 1178 windows:registry:amcache events
    # 2105 last written time events
    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 3283)

    events = list(storage_writer.GetSortedEvents())

    expected_full_path = (
        'c:\\users\\user\\appdata\\local\\temp\\chocolatey\\'
        'is-f4510.tmp\\idafree50.tmp')

    expected_event_values = {
        'data_type': 'windows:registry:amcache',
        'full_path': expected_full_path,
        'sha1': '82274eef0911a948f91425f5e5b0e730517fe75e',
        'timestamp': '1992-06-19 22:22:17.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'windows:registry:amcache:programs',
        'entry_type': 'AddRemoveProgram',
        'file_paths': [
            'c:\\program files (x86)\\fileinsight\\plugins',
            'c:\\program files (x86)\\fileinsight\\plugins\\anomaly chart',
            'c:\\program files (x86)\\fileinsight'],
        'name': 'FileInsight - File analysis tool',
        'publisher': 'McAfee Inc.',
        'uninstall_key': [
            'HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\Microsoft\\Windows\\'
            'CurrentVersion\\Uninstall\\FileInsight']}

    self.CheckEventValues(storage_writer, events[1285], expected_event_values)

  def testParseWithSystem(self):
    """Tests the Parse function with a SYSTEM Registry file."""
    parser = amcache.AMCacheParser()

    storage_writer = self._ParseFile(['SYSTEM'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 0)


if __name__ == '__main__':
  unittest.main()
