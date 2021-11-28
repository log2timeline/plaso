#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows XML EventLog (EVTX) parser."""

import unittest

from plaso.lib import definitions
from plaso.parsers import winevtx

from tests.parsers import test_lib


class WinEvtxParserTest(test_lib.ParserTestCase):
  """Tests for the Windows XML EventLog (EVTX) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = winevtx.WinEvtxParser()
    storage_writer = self._ParseFile(['System.evtx'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3202)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Windows Event Viewer Log (EVTX) information:
    #   Version                     : 3.1
    #   Number of records           : 1601
    #   Number of recovered records : 0
    #   Log type                    : System

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

    expected_string2 = (
        'C:\\Windows\\System32\\Winevt\\Logs\\'
        'Archive-System-2012-03-14-04-17-39-932.evtx')

    expected_event_values = {
        'computer_name': 'WKS-WIN764BITB.shieldbase.local',
        'data_type': 'windows:evtx:record',
        'event_identifier': 105,
        'event_level': 4,
        'message_identifier': 105,
        'provider_identifier': '{fc65ddd8-d6ef-4962-83d5-6e5cfe9ce148}',
        'record_number': 12049,
        'source_name': 'Microsoft-Windows-Eventlog',
        'strings': ['System', expected_string2]}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

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

    expected_event_values = {
        'computer_name': 'WKS-WIN764BITB.shieldbase.local',
        'date_time': '2012-03-14 04:17:38.2763402',
        'data_type': 'windows:evtx:record',
        'event_level': 4,
        'record_number': 12050,
        'source_name': 'Service Control Manager',
        'strings': ['Windows Modules Installer', 'stopped', (
            '540072007500730074006500640049006E007300740061006C006C00650072002F'
            '0031000000')],
        'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
        'xml_string': expected_xml_string}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

  def testParseTruncated(self):
    """Tests the Parse function on a truncated file."""
    parser = winevtx.WinEvtxParser()
    # Be aware of System2.evtx file, it was manually shortened so it probably
    # contains invalid log at the end.
    storage_writer = self._ParseFile(['System2.evtx'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 388)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'windows:evtx:record',
        'event_identifier': 4624,
        'message_identifier': 4624}

    self.CheckEventValues(storage_writer, events[356], expected_event_values)

    expected_event_values = {
        'data_type': 'windows:evtx:record',
        'event_identifier': 4648,
        'message_identifier': 4648}

    self.CheckEventValues(storage_writer, events[360], expected_event_values)


if __name__ == '__main__':
  unittest.main()
