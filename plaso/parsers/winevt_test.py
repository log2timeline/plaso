#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""Tests for the Windows EventLog (EVT) parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import winevt as winevt_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import test_lib
from plaso.parsers import winevt


class WinEvtParserTest(test_lib.ParserTestCase):
  """Tests for the Windows EventLog (EVT) parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = winevt.WinEvtParser()

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['SysEvent.Evt'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    # Windows Event Log (EVT) information:
    #	Version                     : 1.1
    #	Number of records           : 6063
    #	Number of recovered records : 437
    #	Log type                    : System

    self.assertEquals(len(event_objects), (6063 + 437) * 2)

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
    event_object = event_objects[1]
    self.assertEquals(event_object.record_number, 1392)
    self.assertEquals(event_object.event_type, 2)
    self.assertEquals(event_object.computer_name, u'WKS-WINXP32BIT')
    self.assertEquals(event_object.source_name, u'LSASRV')
    self.assertEquals(event_object.event_category, 3)
    self.assertEquals(event_object.event_identifier, 0x8000a001)
    self.assertEquals(event_object.strings[0], u'cifs/CONTROLLER')

    expected_string = (
        u'"The system detected a possible attempt to compromise security. '
        u'Please ensure that you can contact the server that authenticated you.'
        u'\r\n (0xc0000388)"')

    self.assertEquals(event_object.strings[1], expected_string)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2011-07-27 06:41:47')
    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    event_object = event_objects[1]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2011-07-27 06:41:47')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.WRITTEN_TIME)

    expected_msg = (
        u'[2147524609 / 0x8000a001] '
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

    expected_msg_short = (
        u'[0x8000a001] '
        u'Strings: [u\'cifs/CONTROLLER\', '
        u'u\'"The system detected a possible ...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
