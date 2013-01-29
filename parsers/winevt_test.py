#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Tests for the Windows EventLog (EVT) parser."""
import os
import unittest

from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import winevt


class WinEvtParserTest(unittest.TestCase):
  """Tests for the Windows EventLog (EVT) parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.test_parser = winevt.WinEvtParser(pre_obj)

  def testWinEvtParserFile(self):
    """Reads and parses a test Windows EventLog (EVT) file."""
    test_file = os.path.join('test_data', 'SysEvent.Evt')

    events = []
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    # Windows Event Log (EVT) information:
    #	Version				: 1.1
    #	Number of records		: 6063
    #	Number of recovered records	: 437
    #	Log type			: System

    expected_number_of_events = 6063 + 437
    self.assertEquals(len(events), expected_number_of_events)

    event_container = events[0]
    self.assertEquals(len(event_container), 2)

    # Event number                    : 1392
    # Creation time                   : Jul 27, 2011 06:41:47 UTC
    # Written time                    : Jul 27, 2011 06:41:47 UTC
    # Event type                      : Warning event (2)
    # Computer name                   : WKS-WINXP32BIT
    # Source name                     : LSASRV
    # Event category                  : 3
    # Event identifier                : 0x8000a001 (2147524609)
    # Number of strings               : 2
    # String: 1                       : cifs/CONTROLLER
    # String: 2                       : "The system detected a possible attempt
    #                                   to compromise security. Please ensure
    #                                   that you can contact the server that
    #                                   authenticated you.\r\n (0xc0000388)"

    self.assertEquals(event_container.record_number, 1392)
    self.assertEquals(event_container.event_type, 2)
    self.assertEquals(event_container.computer_name, 'WKS-WINXP32BIT')
    self.assertEquals(event_container.source_name, 'LSASRV')
    self.assertEquals(event_container.event_category, 3)
    self.assertEquals(event_container.event_identifier, 0x8000a001)
    self.assertEquals(event_container.strings[0], 'cifs/CONTROLLER')

    expected_string = (
        u'"The system detected a possible attempt to compromise security. '
        u'Please ensure that you can contact the server that authenticated you.'
        u'\r\n (0xc0000388)"')

    self.assertEquals(event_container.strings[1], expected_string)

    event_object = event_container.events[0]

    # date -u -d"Jul 27, 2011 06:41:47 UTC" +"%s.%N"
    self.assertEquals(event_object.timestamp, 1311748907 * 1000000)
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.CREATION_TIME)

    event_object = event_container.events[1]

    self.assertEquals(event_object.timestamp, 1311748907 * 1000000)
    self.assertEquals(event_object.timestamp_desc,
                      eventdata.EventTimestamp.WRITTEN_TIME)

    # Test the event specific formatter.
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    expected_msg = (u'[0x8000a001] '
                    u'Record Number: 1392 '
                    u'Event Type: Information event '
                    u'Event Category: 3 '
                    u'Source Name: LSASRV '
                    u'Computer Name: WKS-WINXP32BIT '
                    u'Strings: [u\'cifs/CONTROLLER\', '
                    u'u\'"The system detected a possible attempt to '
                    u'compromise security. Please ensure that you can '
                    u'contact the server that authenticated you.\\r\\n '
                    u'(0xc0000388)"\']')

    self.assertEquals(msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
