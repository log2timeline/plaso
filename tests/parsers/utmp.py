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

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 14)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'linux:utmp:event',
        'exit_status': 0,
        'hostname': 'localhost',
        'ip_address': '0.0.0.0',
        'pid': 1115,
        'terminal_identifier': 52,
        'terminal': 'tty4',
        'type': 6,
        'username': 'LOGIN',
        'written_time': '2013-12-13T14:45:09.000000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)

  def testParseWtmpFile(self):
    """Tests the Parse function on a wtmp file."""
    parser = utmp.UtmpParser()
    storage_writer = self._ParseFile(['wtmp.1'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'linux:utmp:event',
        'exit_status': 0,
        'hostname': '10.10.122.1',
        'ip_address': '10.10.122.1',
        'pid': 20060,
        'terminal': 'pts/32',
        'terminal_identifier': 842084211,
        'type': 7,
        'username': 'userA',
        'written_time': '2011-12-01T17:36:38.432935+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
