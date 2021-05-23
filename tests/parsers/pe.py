#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the PE file parser."""

import unittest

from plaso.parsers import pe

from tests.parsers import test_lib


class PECOFFTest(test_lib.ParserTestCase):
  """Tests for the PE file parser."""

  def testParseFileObjectOnExecutable(self):
    """Tests the ParseFileObject on a PE executable (EXE) file."""
    parser = pe.PEParser()
    storage_writer = self._ParseFile(['test_pe.exe'], parser)

    self.assertEqual(storage_writer.number_of_events, 3)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'pe:compilation:compilation_time',
        'pe_type': 'Executable (EXE)',
        'timestamp': '2015-04-21 14:53:56.000000'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'pe:import:import_time',
        'timestamp': '2015-04-21 14:53:55.000000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'pe:delay_import:import_time',
        'dll_name': 'USER32.dll',
        'imphash': '8d0739063fc8f9955cc6696b462544ab',
        'pe_type': 'Executable (EXE)',
        'timestamp': '2015-04-21 14:53:54.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

  def testParseFileObjectOnDriver(self):
    """Tests the ParseFileObject on a PE driver (SYS) file."""
    parser = pe.PEParser()
    storage_writer = self._ParseFile(['test_driver.sys'], parser)

    self.assertEqual(storage_writer.number_of_events, 1)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    # Note that pefile pre 2021.5.13 indicated pe_type is 'Driver (SYS)'
    expected_event_values = {
        'data_type': 'pe:compilation:compilation_time',
        'pe_type': 'Executable (EXE)',
        'timestamp': '2015-04-21 14:53:54.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
