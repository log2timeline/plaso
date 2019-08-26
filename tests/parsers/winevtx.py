#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows XML EventLog (EVTX) parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winevtx as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import winevtx

from tests.parsers import test_lib


class WinEvtxParserTest(test_lib.ParserTestCase):
  """Tests for the Windows XML EventLog (EVTX) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = winevtx.WinEvtxParser()
    storage_writer = self._ParseFile(['System.evtx'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)

    # Windows Event Viewer Log (EVTX) information:
    #   Version                     : 3.1
    #   Number of records           : 1601
    #   Number of recovered records : 0
    #   Log type                    : System

    self.assertEqual(storage_writer.number_of_events, 3202)

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

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.record_number, 12049)
    self.assertEqual(
        event_data.computer_name, 'WKS-WIN764BITB.shieldbase.local')
    self.assertEqual(event_data.source_name, 'Microsoft-Windows-Eventlog')
    self.assertEqual(event_data.event_level, 4)
    self.assertEqual(event_data.event_identifier, 105)

    self.assertEqual(event_data.strings[0], 'System')

    expected_string = (
        'C:\\Windows\\System32\\Winevt\\Logs\\'
        'Archive-System-2012-03-14-04-17-39-932.evtx')

    self.assertEqual(event_data.strings[1], expected_string)

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2012-03-14 04:17:38.276340')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_WRITTEN)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_xml_string = (
        '<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/'
        'event">\n'
        '  <System>\n'
        '    <Provider Name="Service Control Manager" '
        'Guid="{555908d1-a6d7-4695-8e1e-26931d2012f4}" '
        'EventSourceName="Service Control Manager"/>\n'
        '    <EventID Qualifiers="16384">7036</EventID>\n'
        '    <Version>0</Version>\n'
        '    <Level>4</Level>\n'
        '    <Task>0</Task>\n'
        '    <Opcode>0</Opcode>\n'
        '    <Keywords>0x8080000000000000</Keywords>\n'
        '    <TimeCreated SystemTime="2012-03-14T04:17:38.276340200Z"/>\n'
        '    <EventRecordID>12050</EventRecordID>\n'
        '    <Correlation/>\n'
        '    <Execution ProcessID="548" ThreadID="1340"/>\n'
        '    <Channel>System</Channel>\n'
        '    <Computer>WKS-WIN764BITB.shieldbase.local</Computer>\n'
        '    <Security/>\n'
        '  </System>\n'
        '  <EventData>\n'
        '    <Data Name="param1">Windows Modules Installer</Data>\n'
        '    <Data Name="param2">stopped</Data>\n'
        '    <Binary>540072007500730074006500640049006E007300740061006C006C00'
        '650072002F0031000000</Binary>\n'
        '  </EventData>\n'
        '</Event>\n')

    self.assertEqual(event_data.xml_string, expected_xml_string)

    expected_message = (
        '[7036 / 0x1b7c] '
        'Source Name: Service Control Manager '
        'Message string: The Windows Modules Installer service entered '
        'the stopped state. '
        'Strings: [\'Windows Modules Installer\', \'stopped\', '
        '\'540072007500730074006500640049006E00'
        '7300740061006C006C00650072002F0031000000\'] '
        'Computer Name: WKS-WIN764BITB.shieldbase.local '
        'Record Number: 12050 '
        'Event Level: 4'
    )

    expected_short_message = (
        '[7036 / 0x1b7c] '
        'Strings: [\'Windows Modules Installer\', \'stopped\', '
        '\'5400720075...')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParseTruncated(self):
    """Tests the Parse function on a truncated file."""
    parser = winevtx.WinEvtxParser()
    # Be aware of System2.evtx file, it was manually shortened so it probably
    # contains invalid log at the end.
    storage_writer = self._ParseFile(['System2.evtx'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 388)

    events = list(storage_writer.GetEvents())

    event = events[356]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_strings_parsed = [
        ('source_user_id', 'S-1-5-18'),
        ('source_user_name', 'GREENDALEGOLD$'),
        ('target_machine_ip', '-'),
        ('target_machine_name', None),
        ('target_user_id', 'S-1-5-18'),
        ('target_user_name', 'SYSTEM')]

    strings_parsed = sorted(event_data.strings_parsed.items())
    self.assertEqual(strings_parsed, expected_strings_parsed)

    self.assertEqual(event_data.event_identifier, 4624)

    event = events[360]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_strings_parsed = [
        ('source_user_id', 'S-1-5-21-1539974973-2753941131-3212641383-1000'),
        ('source_user_name', 'gold_administrator'),
        ('target_machine_ip', '-'),
        ('target_machine_name', 'DC1.internal.greendale.edu'),
        ('target_user_name', 'administrator')]

    strings_parsed = sorted(event_data.strings_parsed.items())
    self.assertEqual(strings_parsed, expected_strings_parsed)

    self.assertEqual(event_data.event_identifier, 4648)


if __name__ == '__main__':
  unittest.main()
