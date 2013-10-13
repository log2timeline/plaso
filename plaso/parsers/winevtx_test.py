#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the Windows XML EventLog (EVTX) parser."""
import os
import unittest

from plaso.formatters import winevtx
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import winevtx


class WinEvtxParserTest(unittest.TestCase):
  """Tests for the Windows XML EventLog (EVTX) parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.test_parser = winevtx.WinEvtxParser(pre_obj)

  def testWinEvtxParserFile(self):
    """Reads and parses a test Windows EventLog (EVT) file."""
    test_file = os.path.join('test_data', 'System.evtx')

    events = []
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    # Windows Event Viewer Log (EVTX) information:
    #   Version				: 3.1
    #   Number of records		: 1601
    #   Number of recovered records	: 0
    #   Log type			: System

    expected_number_of_events = 1601
    self.assertEquals(len(events), expected_number_of_events)

    # Event number                    : 12049
    # Written time                    : Mar 14, 2012 04:17:43.354562700 UTC
    # Event level                     : Information (4)
    # Computer name                   : WKS-WIN764BITB.shieldbase.local
    # Provider identifier             : {fc65ddd8-d6ef-4962-83d5-6e5cfe9ce148}
    # Source name                     : Microsoft-Windows-Eventlog
    # Event identifier                : 0x00000069 (105)
    # Number of strings               : 2
    # String: 1                       : System
    # String: 2                       : C:\Windows\System32\Winevt\Logs\
    #                                 : Archive-System-2012-03-14-04-17-39-932
    #                                 : .evtx

    event_object = events[0]

    self.assertEquals(event_object.record_number, 12049)
    self.assertEquals(event_object.computer_name,
                      'WKS-WIN764BITB.shieldbase.local')
    self.assertEquals(event_object.source_name, 'Microsoft-Windows-Eventlog')
    self.assertEquals(event_object.event_level, 4)
    self.assertEquals(event_object.event_identifier, 0x00000069)

    expected_string = u'System'

    self.assertEquals(event_object.strings[0], expected_string)

    expected_string = (
        u'C:\\Windows\\System32\\Winevt\\Logs\\'
        u'Archive-System-2012-03-14-04-17-39-932.evtx')

    self.assertEquals(event_object.strings[1], expected_string)

    # date -u -d"Mar 14, 2012 04:17:38.276340200" +"%s.%N"
    event_object = events[1]

    self.assertEquals(event_object.timestamp,
                      (1331698658 * 1000000) + (276340200 / 1000))
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.WRITTEN_TIME)

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

    self.assertEquals(event_object.xml_string, expected_xml_string)

    # Test the event specific formatter.
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (
        u'[7036 / 0x00001b7c] '
        u'Record Number: 12050 '
        u'Event Level: 4 '
        u'Source Name: Service Control Manager '
        u'Computer Name: WKS-WIN764BITB.shieldbase.local '
        u'Strings: [u\'Windows Modules Installer\', '
        u'u\'stopped\', u\'540072007500730074006500640049006E00'
        u'7300740061006C006C00650072002F0031000000\']')

    expected_msg_short = (
        u'[0x00001b7c] '
        u'Strings: [u\'Windows Modules Installer\', '
        u'u\'stopped\', u\'5400720075...')

    self.assertEquals(msg, expected_msg)
    self.assertEquals(msg_short, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
