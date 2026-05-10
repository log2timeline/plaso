#!/usr/bin/env python3
"""Tests for the Windows XML EventLog (EVTX) parser."""

import unittest

from plaso.parsers import winevtx

from tests.parsers import test_lib


class WinEvtxParserTest(test_lib.ParserTestCase):
  """Tests for the Windows XML EventLog (EVTX) parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = winevtx.WinEvtxParser()
    storage_writer = self._ParseFile(['evtx', 'System.evtx'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 5009)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

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
        '    <TimeCreated SystemTime="2010-11-21T03:55:59.626427100Z"/>\n'
        '    <EventRecordID>1</EventRecordID>\n'
        '    <Correlation/>\n'
        '    <Execution ProcessID="492" ThreadID="1188"/>\n'
        '    <Channel>System</Channel>\n'
        '    <Computer>37L4247F27-26</Computer>\n'
        '    <Security/>\n'
        '  </System>\n'
        '  <EventData>\n'
        '    <Data Name="param1">Windows Event Log</Data>\n'
        '    <Data Name="param2">stopped</Data>\n'
        '    <Binary>6500760065006E0074006C006F0067002F0031000000</Binary>\n'
        '  </EventData>\n'
        '</Event>\n')

    expected_event_values = {
        'creation_time': '2010-11-21T03:55:59.6264271+00:00',
        'computer_name': '37L4247F27-26',
        'data_type': 'windows:evtx:record',
        'event_identifier': 7036,
        'event_level': 4,
        'event_version': 0,
        'message_identifier': 1073748860,
        'provider_identifier': '{555908d1-a6d7-4695-8e1e-26931d2012f4}',
        'record_number': 1,
        'source_name': 'Service Control Manager',
        'strings': [
            'Windows Event Log', 'stopped',
            '6500760065006E0074006C006F0067002F0031000000'],
        'written_time': '2010-11-21T03:55:59.6264271+00:00',
        'xml_string': expected_xml_string}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

  def testParseTruncated(self):
    """Tests the Parse function on a truncated file."""
    parser = winevtx.WinEvtxParser()
    # Be aware of System2.evtx file, it was manually shortened so it probably
    # contains invalid log at the end.
    storage_writer = self._ParseFile(['evtx', 'System2.evtx'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 194)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'windows:evtx:record',
        'creation_time': '2015-08-09T09:15:48.4341250+00:00',
        'event_identifier': 4624,
        'message_identifier': 4624,
        'record_number': 179,
        'written_time': '2015-08-09T09:15:48.4341250+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 178)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
