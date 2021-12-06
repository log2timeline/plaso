#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the vsftpd parser."""

import unittest

from plaso.parsers import vsftpd

from tests.parsers import test_lib


class VsftpdLogParserTest(test_lib.ParserTestCase):
  """Tests for the vsftpd parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = vsftpd.VsftpdLogParser()
    storage_writer = self._ParseFile(['vsftpd.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 25)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2016-06-10 14:24:19',
        'data_type': 'vsftpd:log',
        'text': (
            '[pid 3] [jean] OK DOWNLOAD: Client "192.168.1.7", '
            '"/home/jean/trains/how-thomas-the-tank-engine-works-1.jpg", '
            '49283 bytes, 931.38Kbyte/sec')}

    self.CheckEventValues(storage_writer, events[12], expected_event_values)

  def testParseWithTimeZone(self):
    """Tests the Parse function with a time zone."""
    parser = vsftpd.VsftpdLogParser()
    storage_writer = self._ParseFile(['vsftpd.log'], parser, timezone='CET')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 25)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2016-06-10 14:24:19',
        'data_type': 'vsftpd:log',
        'text': (
            '[pid 3] [jean] OK DOWNLOAD: Client "192.168.1.7", '
            '"/home/jean/trains/how-thomas-the-tank-engine-works-1.jpg", '
            '49283 bytes, 931.38Kbyte/sec'),
        'timestamp': '2016-06-10 12:24:19.000000'}

    self.CheckEventValues(storage_writer, events[12], expected_event_values)


if __name__ == '__main__':
  unittest.main()
