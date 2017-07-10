#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the PE file parser."""

import unittest

from plaso.formatters import pe  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import pe

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class PECOFFTest(test_lib.ParserTestCase):
  """Tests for the PE file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'test_pe.exe'])
  def testParseFileObjectOnExecutable(self):
    """Tests the ParseFileObject on a PE executable (EXE) file."""
    parser_object = pe.PEParser()
    storage_writer = self._ParseFile([u'test_pe.exe'], parser_object)

    self.assertEqual(storage_writer.number_of_events, 3)

    event_object = storage_writer.events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-04-21 14:53:56')
    self.assertEqual(event_object.pe_type, u'Executable (EXE)')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.data_type, u'pe:compilation:compilation_time')

    event_object = storage_writer.events[1]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-04-21 14:53:55')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.data_type, u'pe:import:import_time')

    event_object = storage_writer.events[2]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-04-21 14:53:54')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.data_type, u'pe:delay_import:import_time')

  @shared_test_lib.skipUnlessHasTestFile([u'test_driver.sys'])
  def testParseFileObjectOnDriver(self):
    """Tests the ParseFileObject on a PE driver (SYS) file."""
    parser_object = pe.PEParser()
    storage_writer = self._ParseFile([u'test_driver.sys'], parser_object)

    self.assertEqual(storage_writer.number_of_events, 1)

    event_object = storage_writer.events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-04-21 14:53:54')
    self.assertEqual(event_object.pe_type, u'Driver (SYS)')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
