#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows EventLog (EVT) parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winevt as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import winevt

from tests.parsers import test_lib


class WinEvtParserTest(test_lib.ParserTestCase):
  """Tests for the Windows EventLog (EVT) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = winevt.WinEvtParser()
    storage_writer = self._ParseFile(['SysEvent.Evt'], parser)

    # Windows Event Log (EVT) information:
    #	Version                     : 1.1
    #	Number of records           : 6063
    #	Number of recovered records : 438
    #	Log type                    : System

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, (6063 + 438) * 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2011-07-27 06:41:47.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event = events[1]

    # Event number      : 1392
    # Creation time     : Jul 27, 2011 06:41:47 UTC
    # Written time      : Jul 27, 2011 06:41:47 UTC
    # Event type        : Warning event (2)
    # Computer name     : WKS-WINXP32BIT
    # Source name       : LSASRV
    # Event category    : 3
    # Event identifier  : 0x8000a001 (2147524609)
    # Number of strings : 2
    # String: 1         : cifs/CONTROLLER
    # String: 2         : "The system detected a possible attempt to compromise
    #                     security. Please ensure that you can contact the
    #                     server that authenticated you.\r\n (0xc0000388)"

    self.CheckTimestamp(event.timestamp, '2011-07-27 06:41:47.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.record_number, 1392)
    self.assertEqual(event_data.event_type, 2)
    self.assertEqual(event_data.computer_name, 'WKS-WINXP32BIT')
    self.assertEqual(event_data.source_name, 'LSASRV')
    self.assertEqual(event_data.event_category, 3)
    self.assertEqual(event_data.event_identifier, 40961)
    self.assertEqual(event_data.strings[0], 'cifs/CONTROLLER')

    expected_string = (
        '"The system detected a possible attempt to compromise security. '
        'Please ensure that you can contact the server that authenticated you.'
        '\r\n (0xc0000388)"')

    self.assertEqual(event_data.strings[1], expected_string)

    expected_message = (
        '[40961 / 0xa001] '
        'Source Name: LSASRV '
        'Strings: [\'cifs/CONTROLLER\', '
        '\'"The system detected a possible attempt to '
        'compromise security. Please ensure that you can '
        'contact the server that authenticated you. (0xc0000388)"\'] '
        'Computer Name: WKS-WINXP32BIT '
        'Severity: Warning '
        'Record Number: 1392 '
        'Event Type: Information event '
        'Event Category: 3')

    expected_short_message = (
        '[40961 / 0xa001] '
        'Strings: [\'cifs/CONTROLLER\', '
        '\'"The system detected a possibl...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
