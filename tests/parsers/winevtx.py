#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows XML EventLog (EVTX) parser."""

import unittest

from plaso.formatters import winevtx  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import winevtx

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class WinEvtxParserTest(test_lib.ParserTestCase):
  """Tests for the Windows XML EventLog (EVTX) parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'System.evtx'])
  def testParse(self):
    """Tests the Parse function."""
    parser = winevtx.WinEvtxParser()
    storage_writer = self._ParseFile([u'System.evtx'], parser)

    # Windows Event Viewer Log (EVTX) information:
    #   Version                     : 3.1
    #   Number of records           : 1601
    #   Number of recovered records : 0
    #   Log type                    : System

    self.assertEqual(storage_writer.number_of_events, 1601)

    events = list(storage_writer.GetEvents())

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

    event = events[0]

    self.assertEqual(event.record_number, 12049)
    expected_computer_name = u'WKS-WIN764BITB.shieldbase.local'
    self.assertEqual(event.computer_name, expected_computer_name)
    self.assertEqual(event.source_name, u'Microsoft-Windows-Eventlog')
    self.assertEqual(event.event_level, 4)
    self.assertEqual(event.event_identifier, 105)

    self.assertEqual(event.strings[0], u'System')

    expected_string = (
        u'C:\\Windows\\System32\\Winevt\\Logs\\'
        u'Archive-System-2012-03-14-04-17-39-932.evtx')

    self.assertEqual(event.strings[1], expected_string)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-14 04:17:38.276340')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

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

    self.assertEqual(event.xml_string, expected_xml_string)

    expected_message = (
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

    expected_short_message = (
        u'[7036 / 0x1b7c] '
        u'Strings: [\'Windows Modules Installer\', \'stopped\', '
        u'\'5400720075...')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'System2.evtx'])
  def testParseTruncated(self):
    """Tests the Parse function on a truncated file."""
    parser = winevtx.WinEvtxParser()
    # Be aware of System2.evtx file, it was manually shortened so it probably
    # contains invalid log at the end.
    storage_writer = self._ParseFile([u'System2.evtx'], parser)

    self.assertEqual(storage_writer.number_of_events, 194)

    events = list(storage_writer.GetEvents())

    event = events[178]

    expected_strings_parsed = [
        (u'source_user_id', u'S-1-5-18'),
        (u'source_user_name', u'GREENDALEGOLD$'),
        (u'target_machine_ip', u'-'),
        (u'target_machine_name', None),
        (u'target_user_id', u'S-1-5-18'),
        (u'target_user_name', u'SYSTEM')]

    strings_parsed = sorted(event.strings_parsed.items())
    self.assertEqual(strings_parsed, expected_strings_parsed)

    self.assertEqual(event.event_identifier, 4624)

    event = events[180]

    expected_strings_parsed = [
        (u'source_user_id', u'S-1-5-21-1539974973-2753941131-3212641383-1000'),
        (u'source_user_name', u'gold_administrator'),
        (u'target_machine_ip', u'-'),
        (u'target_machine_name', u'DC1.internal.greendale.edu'),
        (u'target_user_name', u'administrator')]

    strings_parsed = sorted(event.strings_parsed.items())
    self.assertEqual(strings_parsed, expected_strings_parsed)

    self.assertEqual(event.event_identifier, 4648)


if __name__ == '__main__':
  unittest.main()
