#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the PE file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import pe as _  # pylint: disable=unused-import
from plaso.parsers import pe

from tests.parsers import test_lib


class PECOFFTest(test_lib.ParserTestCase):
  """Tests for the PE file parser."""

  def testParseFileObjectOnExecutable(self):
    """Tests the ParseFileObject on a PE executable (EXE) file."""
    parser = pe.PEParser()
    storage_writer = self._ParseFile(['test_pe.exe'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 3)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2015-04-21 14:53:56.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'pe:compilation:compilation_time')
    self.assertEqual(event_data.pe_type, 'Executable (EXE)')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2015-04-21 14:53:55.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'pe:import:import_time')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2015-04-21 14:53:54.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'pe:delay_import:import_time')

  def testParseFileObjectOnDriver(self):
    """Tests the ParseFileObject on a PE driver (SYS) file."""
    parser = pe.PEParser()
    storage_writer = self._ParseFile(['test_driver.sys'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2015-04-21 14:53:54.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.pe_type, 'Driver (SYS)')


if __name__ == '__main__':
  unittest.main()
