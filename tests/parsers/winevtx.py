#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows XML EventLog (EVTX) parser."""

import unittest

from plaso.formatters import winevtx as _  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winevtx

from tests.parsers import test_lib


class WinEvtxParserTest(test_lib.ParserTestCase):
  """Tests for the Windows XML EventLog (EVTX) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser_object = winevtx.WinEvtxParser()
    storage_writer = self._ParseFile(
        [u'System.evtx'], parser_object)

    # Windows Event Viewer Log (EVTX) information:
    #   Version                     : 3.1
    #   Number of records           : 1601
    #   Number of recovered records : 0
    #   Log type                    : System

    self.assertEqual(len(storage_writer.events), 1601)

    # Event number        : 12049
    # Written time        : Mar 14, 2012 04:17:43.354562700 UTC
    # Event level         : Information (4)
    # Computer name       : WKS-WIN764BITB.shieldbase.local
    # Provider identifier : {fc65ddd8-d6ef-4962-83d5-6e5cfe9ce148}
    # Source name         : Microsoft-Windows-Eventlog
    # Event identifier    : 0x00000069 (105)
    # Number of strings   : 2
    # String: 1           : System
    # String: 2           : C:\Windows\System32\Winevt\Logs\
    #                     : Archive-System-2012-03-14-04-17-39-932.evtx

    event_object = storage_writer.events[0]

    self.assertEqual(event_object.record_number, 12049)
    expected_computer_name = u'WKS-WIN764BITB.shieldbase.local'
    self.assertEqual(event_object.computer_name, expected_computer_name)
    self.assertEqual(event_object.source_name, u'Microsoft-Windows-Eventlog')
    self.assertEqual(event_object.event_level, 4)
    self.assertEqual(event_object.event_identifier, 105)

    self.assertEqual(event_object.strings[0], u'System')

    expected_string = (
        u'C:\\Windows\\System32\\Winevt\\Logs\\'
        u'Archive-System-2012-03-14-04-17-39-932.evtx')

    self.assertEqual(event_object.strings[1], expected_string)

    event_object = storage_writer.events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-14 04:17:38.276340')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.WRITTEN_TIME)

    expected_xml_string = (
        u'<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/'
        u'event">\n'
        u'  <System>\n'
        u'    <Provider Name="Service Control Manager" '
        u'Guid="{555908d1-a6d7-4695-8e1e-26931d2012f4}" '
        u'EventSourceName="Service Control Manager"/>\n'
        u'    <EventID Qualifiers="16384">7036</EventID>\n'
        u'    <Version>0</Version>\n'
        u'    <Level>4</Level>\n'
        u'    <Task>0</Task>\n'
        u'    <Opcode>0</Opcode>\n'
        u'    <Keywords>0x8080000000000000</Keywords>\n'
        u'    <TimeCreated SystemTime="2012-03-14T04:17:38.276340200Z"/>\n'
        u'    <EventRecordID>12050</EventRecordID>\n'
        u'    <Correlation/>\n'
        u'    <Execution ProcessID="548" ThreadID="1340"/>\n'
        u'    <Channel>System</Channel>\n'
        u'    <Computer>WKS-WIN764BITB.shieldbase.local</Computer>\n'
        u'    <Security/>\n'
        u'  </System>\n'
        u'  <EventData>\n'
        u'    <Data Name="param1">Windows Modules Installer</Data>\n'
        u'    <Data Name="param2">stopped</Data>\n'
        u'    <Binary>540072007500730074006500640049006E007300740061006C006C00'
        u'650072002F0031000000</Binary>\n'
        u'  </EventData>\n'
        u'</Event>\n')

    self.assertEqual(event_object.xml_string, expected_xml_string)

    expected_msg = (
        u'[7036 / 0x1b7c] '
        u'Record Number: 12050 '
        u'Event Level: 4 '
        u'Source Name: Service Control Manager '
        u'Computer Name: WKS-WIN764BITB.shieldbase.local '
        u'Message string: The Windows Modules Installer service entered '
        u'the stopped state. '
        u'Strings: [\'Windows Modules Installer\', \'stopped\', '
        u'\'540072007500730074006500640049006E00'
        u'7300740061006C006C00650072002F0031000000\']')

    expected_msg_short = (
        u'[7036 / 0x1b7c] '
        u'Strings: [\'Windows Modules Installer\', \'stopped\', '
        u'\'5400720075...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
