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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 6)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'mac:utmpx:event',
        'hostname': 'localhost',
        'pid': 1,
        'terminal_identifier': 0,
        'timestamp': '2013-11-13 17:52:34.000000',
        'type': 2}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:utmpx:event',
        'hostname': 'localhost',
        'pid': 67,
        'terminal': 'console',
        'terminal_identifier': 65583,
        'timestamp': '2013-11-13 17:52:41.736713',
        'type': 7,
        'username': 'moxilo'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:utmpx:event',
        'hostname': 'localhost',
        'pid': 6899,
        'terminal': 'ttys002',
        'terminal_identifier': 842018931,
        'timestamp': '2013-11-14 04:32:56.641464',
        'type': 8,
        'username': 'moxilo'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)


if __name__ == '__main__':
  unittest.main()
