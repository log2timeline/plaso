#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows EventLog (EVT) parser."""

import unittest

from plaso.formatters import winevt  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import winevt

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class WinEvtParserTest(test_lib.ParserTestCase):
  """Tests for the Windows EventLog (EVT) parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'SysEvent.Evt'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = winevt.WinEvtParser()
    storage_writer = self._ParseFile([u'SysEvent.Evt'], parser_object)

    # Windows Event Log (EVT) information:
    #	Version                     : 1.1
    #	Number of records           : 6063
    #	Number of recovered records : 437
    #	Log type                    : System

    self.assertEqual(storage_writer.number_of_events, (6063 + 437) * 2)

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
    event_object = storage_writer.events[1]
    self.assertEqual(event_object.record_number, 1392)
    self.assertEqual(event_object.event_type, 2)
    self.assertEqual(event_object.computer_name, u'WKS-WINXP32BIT')
    self.assertEqual(event_object.source_name, u'LSASRV')
    self.assertEqual(event_object.event_category, 3)
    self.assertEqual(event_object.event_identifier, 40961)
    self.assertEqual(event_object.strings[0], u'cifs/CONTROLLER')

    expected_string = (
        u'"The system detected a possible attempt to compromise security. '
        u'Please ensure that you can contact the server that authenticated you.'
        u'\r\n (0xc0000388)"')

    self.assertEqual(event_object.strings[1], expected_string)

    event_object = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-27 06:41:47')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    event_object = storage_writer.events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-07-27 06:41:47')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(
        event_object.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    expected_msg = (
        u'[40961 / 0xa001] '
        u'Severity: Warning '
        u'Record Number: 1392 '
        u'Event Type: Information event '
        u'Event Category: 3 '
        u'Source Name: LSASRV '
        u'Computer Name: WKS-WINXP32BIT '
        u'Strings: [\'cifs/CONTROLLER\', '
        u'\'"The system detected a possible attempt to '
        u'compromise security. Please ensure that you can '
        u'contact the server that authenticated you. (0xc0000388)"\']')

    expected_msg_short = (
        u'[40961 / 0xa001] '
        u'Strings: [\'cifs/CONTROLLER\', '
        u'\'"The system detected a possibl...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
