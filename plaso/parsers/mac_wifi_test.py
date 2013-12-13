#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a unit test for the Mac wifi.log parser."""

import os
import pytz
import unittest

# pylint: disable=W0611
from plaso.formatters import mac_wifi as mac_wifi_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.lib import putils
from plaso.parsers import mac_wifi as mac_wifi_parser


class MacWifiUnitTest(unittest.TestCase):
  """A unit test for the Mac Wifi log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    test_file = os.path.join('test_data', 'wifi.log')
    self.filehandle = putils.OpenOSFile(test_file)

  def testParseFile(self):
    """Test parsing of a Mac Wifi log file."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.year = 2013
    pre_obj.zone = pytz.timezone('UTC')

    mac_wifi = mac_wifi_parser.MacWifiLogParser(pre_obj, None)
    events = list(mac_wifi.Parse(self.filehandle))

    self.assertEqual(len(events), 9)

    event = events[0]
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(event)
    expected_msg = (u'Action: Interface en0 turn up. '
                    '(airportdProcessDLILEvent) Log: en0 attached (up)')
    self.assertEqual(expected_msg, msg)
    # date -u -d"Thu, 14 Nov 2013 20:36:37" +"%s222000"
    self.assertEqual(1384461397222000, event.timestamp)
    self.assertEqual(u'airportd[88]', event.agent)
    self.assertEqual(u'airportdProcessDLILEvent', event.function)
    self.assertEqual(u'Interface en0 turn up.', event.action)
    self.assertEqual(u'en0 attached (up)', event.text)

    event = events[1]
    # date -u -d"Thu, 14 Nov 2013 20:36:43.818" +"%s818000"
    self.assertEqual(1384461403818000, event.timestamp)
    self.assertEqual(u'airportd[88]', event.agent)
    self.assertEqual(u'_doAutoJoin', event.function)
    self.assertEqual(u'Wifi connected to SSID CampusNet', event.action)
    expected_msg = (u'Already associated to \u201cCampusNet\u201d. '
                    'Bailing on auto-join.')
    self.assertEqual(expected_msg, event.text)

    event = events[2]
    # date -u -d"Thu, 14 Nov 2013 21:50:52.395" +"%s395000"
    self.assertEqual(1384465852395000, event.timestamp)
    self.assertEqual(u'airportd[88]', event.agent)
    self.assertEqual(u'_handleLinkEvent', event.function)
    expected_msg = (u'Unable to process link event, op mode request '
                    'returned -3903 (Operation not supported)')
    self.assertEqual(expected_msg, event.action)
    self.assertEqual(expected_msg, event.text)

    event = events[5]
    # date -u -d"Thu, 14 Nov 2013 21:52:09" +"%s883000"
    self.assertEqual(1384465929883000, event.timestamp)
    self.assertEqual(u'airportd[88]', event.agent)
    self.assertEqual(u'_processSystemPSKAssoc', event.function)
    # TODO: something happens here, it must be checked
    expected_msg = (u'New wifi configured. BSSID: Unknown SSID: '
                    'Unknown, Security: Unknown.')
    self.assertEqual(expected_msg, event.action)
    expected_msg = (u'No password for network <CWNetwork: '
                    '0x7fdfe970b250> [ssid=AndroidAP, bssid='
                    '88:30:8a:7a:61:88, security=WPA2 '
                    'Personal, rssi=-21, channel=<CWChannel: '
                    '0x7fdfe9712870> [channelNumber=11(2GHz), '
                    'channelWidth={20MHz}], ibss=0] in the '
                    'system keychain')
    self.assertEqual(expected_msg, event.text)

    event = events[7]
    # date -u -d"Tue, 31 Dec 2013 23:59:38" +"%s165000"
    self.assertEqual(1388534378165000, event.timestamp)

    event = events[8]
    # date -u -d"Wed, 1 Jan 2014 01:12:17" +"%s311000"
    self.assertEqual(1388538737311000, event.timestamp)


if __name__ == '__main__':
  unittest.main()
