#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for UTMPX file parser."""

import unittest

from plaso.parsers import utmpx

from tests.parsers import test_lib


class UtmpxParserTest(test_lib.ParserTestCase):
  """Tests for utmpx file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = utmpx.UtmpxParser()
    storage_writer = self._ParseFile(['utmpx_mac'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2013-11-13 17:52:34.000000',
        'data_type': 'mac:utmpx:event',
        'hostname': 'localhost',
        'pid': 1,
        'terminal_identifier': 0,
        'type': 2}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'date_time': '2013-11-13 17:52:41.736713',
        'data_type': 'mac:utmpx:event',
        'hostname': 'localhost',
        'pid': 67,
        'terminal': 'console',
        'terminal_identifier': 65583,
        'type': 7,
        'username': 'moxilo'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'date_time': '2013-11-14 04:32:56.641464',
        'data_type': 'mac:utmpx:event',
        'hostname': 'localhost',
        'pid': 6899,
        'terminal': 'ttys002',
        'terminal_identifier': 842018931,
        'type': 8,
        'username': 'moxilo'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)


if __name__ == '__main__':
  unittest.main()
