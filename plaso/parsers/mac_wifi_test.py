#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""Tests for the Mac wifi.log parser."""

import pytz
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import mac_wifi as mac_wifi_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers import mac_wifi as mac_wifi_parser
from plaso.parsers import test_lib


class MacWifiUnitTest(test_lib.ParserTestCase):
  """Tests for the Mac wifi.log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    pre_obj.year = 2013
    pre_obj.zone = pytz.timezone('UTC')
    self._parser = mac_wifi_parser.MacWifiLogParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['wifi.log'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEqual(len(event_objects), 9)

    event_object = event_objects[0]

    # date -u -d"Thu, 14 Nov 2013 20:36:37.222" +"%s.%N"
    self.assertEqual(event_object.timestamp, 1384461397222000)
    self.assertEqual(event_object.agent, u'airportd[88]')
    self.assertEqual(event_object.function, u'airportdProcessDLILEvent')
    self.assertEqual(event_object.action, u'Interface en0 turn up.')
    self.assertEqual(event_object.text, u'en0 attached (up)')

    expected_msg = (
        u'Action: Interface en0 turn up. '
        u'(airportdProcessDLILEvent) '
        u'Log: en0 attached (up)')
    expected_msg_short = (
        u'Action: Interface en0 turn up.')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[1]

    # date -u -d"Thu, 14 Nov 2013 20:36:43.818" +"%s.%N"
    self.assertEqual(event_object.timestamp, 1384461403818000)
    self.assertEqual(event_object.agent, u'airportd[88]')
    self.assertEqual(event_object.function, u'_doAutoJoin')
    self.assertEqual(event_object.action, u'Wifi connected to SSID CampusNet')

    expected_text = (
        u'Already associated to \u201cCampusNet\u201d. Bailing on auto-join.')
    self.assertEqual(event_object.text, expected_text)

    event_object = event_objects[2]

    # date -u -d"Thu, 14 Nov 2013 21:50:52.395" +"%s.%N"
    self.assertEqual(event_object.timestamp, 1384465852395000)
    self.assertEqual(event_object.agent, u'airportd[88]')
    self.assertEqual(event_object.function, u'_handleLinkEvent')

    expected_string = (
        u'Unable to process link event, op mode request returned -3903 '
        u'(Operation not supported)')

    self.assertEqual(event_object.action, expected_string)
    self.assertEqual(event_object.text, expected_string)

    event_object = event_objects[5]

    # date -u -d"Thu, 14 Nov 2013 21:52:09.883" +"%s.%N"
    self.assertEqual(1384465929883000, event_object.timestamp)
    self.assertEqual(u'airportd[88]', event_object.agent)
    self.assertEqual(u'_processSystemPSKAssoc', event_object.function)

    expected_action = (
        u'New wifi configured. BSSID: 88:30:8a:7a:61:88, SSID: AndroidAP, '
        u'Security: WPA2 Personal.')

    self.assertEqual(event_object.action, expected_action)

    expected_text = (
        u'No password for network <CWNetwork: 0x7fdfe970b250> '
        u'[ssid=AndroidAP, bssid=88:30:8a:7a:61:88, security=WPA2 '
        u'Personal, rssi=-21, channel=<CWChannel: 0x7fdfe9712870> '
        u'[channelNumber=11(2GHz), channelWidth={20MHz}], ibss=0] '
        u'in the system keychain')

    self.assertEqual(event_object.text, expected_text)

    event_object = event_objects[7]

    # date -u -d"Tue, 31 Dec 2013 23:59:38.165" +"%s.%N"
    self.assertEqual(event_object.timestamp, 1388534378165000)

    event_object = event_objects[8]

    # date -u -d"Wed, 1 Jan 2014 01:12:17.311" +"%s.%N"
    self.assertEqual(event_object.timestamp, 1388538737311000)


if __name__ == '__main__':
  unittest.main()
