#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Sophos Anti-Virus log (SAV.txt) parser."""

import unittest

from plaso.parsers import sophos_av

from tests.parsers import test_lib


class SophosAVLogParserTest(test_lib.ParserTestCase):
  """Tests for the Sophos Anti-Virus log (SAV.txt) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = sophos_av.SophosAVLogParser()
    storage_writer = self._ParseFile(['sav.txt'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2010-07-20 18:38:14',
        'data_type': 'sophos:av:log',
        'text': (
            'File "C:\\Documents and Settings\\Administrator\\Desktop\\'
            'sxl_test_50.com" belongs to virus/spyware \'LiveProtectTest\'.')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseWithTimeZone(self):
    """Tests the Parse function with a time zone."""
    parser = sophos_av.SophosAVLogParser()
    storage_writer = self._ParseFile(['sav.txt'], parser, timezone='CET')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2010-07-20 18:38:14',
        'data_type': 'sophos:av:log',
        'text': (
            'File "C:\\Documents and Settings\\Administrator\\Desktop\\'
            'sxl_test_50.com" belongs to virus/spyware \'LiveProtectTest\'.'),
        'timestamp': '2010-07-20 16:38:14.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
