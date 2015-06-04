#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the PE file parser."""

import unittest

from plaso.formatters import pe as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import pe

from tests.parsers import test_lib


class PECOFFTest(test_lib.ParserTestCase):
  """Tests for the PE file parser."""

  def testParseFileObjectEXE(self):
    """Tests the ParseFileObject method against an EXE PE file."""
    test_path = self._GetTestFilePath([u'test_pe.exe'])
    parser = pe.PEParser()

    event_queue_consumer = self._ParseFile(parser, test_path)
    events = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(events), 3)
    first_event = events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-04-21 14:53:56')
    self.assertEqual(first_event.pe_type, u'Executable (EXE)')
    self.assertEqual(first_event.timestamp, expected_timestamp)
    self.assertEqual(first_event.data_type, u'pe:compilation:compilation_time')

    second_event = events[1]
    expected_timestamp2 = timelib.Timestamp.CopyFromString(
        u'2015-04-21 14:53:55')
    self.assertEqual(second_event.timestamp, expected_timestamp2)
    self.assertEqual(second_event.data_type, u'pe:import:import_time')

    third_event = events[2]
    expected_timestamp3 = timelib.Timestamp.CopyFromString(
        u'2015-04-21 14:53:54')
    self.assertEqual(third_event.timestamp, expected_timestamp3)
    self.assertEqual(third_event.data_type, u'pe:delay_import:import_time')

  def testDriver(self):
    """Tests the ParseFileObject method against a driver (SYS) PE file."""
    test_path = self._GetTestFilePath([u'test_driver.sys'])
    parser = pe.PEParser()

    event_queue_consumer = self._ParseFile(parser, test_path)
    events = self._GetEventObjectsFromQueue(event_queue_consumer)
    self.assertEqual(len(events), 1)
    first_event = events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-04-21 14:53:54')
    self.assertEqual(first_event.pe_type, u'Driver (SYS)')
    self.assertEqual(first_event.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
