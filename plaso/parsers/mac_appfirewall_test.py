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
"""This file contains a unit test for Mac AppFirewall log parser."""

import os
import pytz
import unittest

# pylint: disable=W0611
from plaso.formatters import mac_appfirewall as mac_appfirewall_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import mac_appfirewall as mac_appfirewall_parser
from plaso.parsers import test_lib
from plaso.pvfs import utils


class MacAppFirewallUnitTest(unittest.TestCase):
  """A unit test for the Mac Wifi log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.year = 2013
    pre_obj.zone = pytz.timezone('UTC')
    self._parser = mac_appfirewall_parser.MacAppFirewallParser(pre_obj, None)

  def testParseFile(self):
    """Test parsing of a Mac Wifi log file."""
    test_file = os.path.join('test_data', 'appfirewall.log')
    events = test_lib.ParseFile(self._parser, test_file)

    self.assertEqual(len(events), 47)

    event = events[0]
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(event)
    expected_msg = (u'Computer: DarkTemplar-2.local Agent: '
                    u'socketfilterfw[112] Status: Error Process name: '
                    u'Logging Log: creating /var/log/appfirewall.log')
    self.assertEqual(expected_msg, msg)
    # date -u -d"Sat, 2 Nov 2013 04:07:35" +"%s222000"
    self.assertEqual(1383365255000000, event.timestamp)
    self.assertEqual(u'socketfilterfw[112]', event.agent)
    self.assertEqual(u'DarkTemplar-2.local', event.computer_name)
    self.assertEqual(u'Error', event.status)
    self.assertEqual(u'Logging', event.process_name)
    self.assertEqual(u'creating /var/log/appfirewall.log', event.action)

    event = events[9]
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(event)
    expected_msg = (u'Computer: DarkTemplar-2.local Agent: '
                    u'socketfilterfw[87] Status: Info Process name: '
                    u'Dropbox Log: Allow TCP LISTEN  (in:0 '
                    u'out:1)')
    self.assertEqual(expected_msg, msg)
    # date -u -d"Sun, 3 Nov 2013 13:25:15" +"%s222000"
    self.assertEqual(1383485115000000, event.timestamp)
    self.assertEqual(u'socketfilterfw[87]', event.agent)
    self.assertEqual(u'DarkTemplar-2.local', event.computer_name)
    self.assertEqual(u'Info', event.status)
    self.assertEqual(u'Dropbox', event.process_name)
    self.assertEqual(u'Allow TCP LISTEN  (in:0 out:1)', event.action)

    # Check repeated lines.
    event = events[38]
    event_rep = events[39]
    self.assertEqual(event_rep.agent, event.agent)
    self.assertEqual(event_rep.computer_name, event.computer_name)
    self.assertEqual(event_rep.status, event.status)
    self.assertEqual(event_rep.process_name, event.process_name)
    self.assertEqual(event_rep.action, event.action)

    # Year changes.
    event = events[45]
    # date -u -d"Tue, 31 Dec 2013 23:59:23" +"%s00"
    self.assertEqual(1388534363000000, event.timestamp)
    event = events[46]
    # date -u -d"Wed, 1 Jan 2014 01:13:23" +"%s00"
    self.assertEqual(1388538803000000, event.timestamp)


if __name__ == '__main__':
  unittest.main()
