#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parser test for utmp files."""

import unittest

from plaso.parsers import utmp

from tests.parsers import test_lib


class UtmpParserTest(test_lib.ParserTestCase):
  """The unit test for utmp parser."""

  def testParseUtmpFile(self):
    """Tests the Parse function on a utmp file."""
    parser = utmp.UtmpParser()
    storage_writer = self._ParseFile(['utmp'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 14)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'linux:utmp:event',
        'terminal': 'system boot',
        'type': 2}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'linux:utmp:event',
        'type': 1}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'date_time': '2013-12-13 14:45:09.000000',
        'data_type': 'linux:utmp:event',
        'exit_status': 0,
        'hostname': 'localhost',
        'ip_address': '0.0.0.0',
        'pid': 1115,
        'terminal_identifier': 52,
        'terminal': 'tty4',
        'type': 6,
        'username': 'LOGIN'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'date_time': '2013-12-18 22:46:56.305504',
        'data_type': 'linux:utmp:event',
        'exit_status': 0,
        'hostname': 'localhost',
        'ip_address': '0.0.0.0',
        'pid': 2684,
        'terminal': 'pts/4',
        'terminal_identifier': 13359,
        'type': 7,
        'username': 'moxilo'}

    self.CheckEventValues(storage_writer, events[12], expected_event_values)

  def testParseWtmpFile(self):
    """Tests the Parse function on a wtmp file."""
    parser = utmp.UtmpParser()
    storage_writer = self._ParseFile(['wtmp.1'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'date_time': '2011-12-01 17:36:38.432935',
        'data_type': 'linux:utmp:event',
        'exit_status': 0,
        'hostname': '10.10.122.1',
        'ip_address': '10.10.122.1',
        'pid': 20060,
        'terminal': 'pts/32',
        'terminal_identifier': 842084211,
        'type': 7,
        'username': 'userA'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
