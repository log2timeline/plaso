#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""This file contains a unit test for ASL securityd log parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import mac_securityd as mac_securityd_formatter
from plaso.lib import eventdata
from plaso.lib import event
from plaso.parsers import mac_securityd as mac_securityd_parser
from plaso.parsers import test_lib
from plaso.pvfs import utils


class MacSecurityUnitTest(test_lib.ParserTestCase):
  """A unit test for the ASL securityd log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    pre_obj.year = 2013
    self._parser = mac_securityd_parser.MacSecuritydLogParser(pre_obj, None)

  def testParseFile(self):
    """Test parsing of a ASL securityd log file."""
    test_file = self._GetTestFilePath(['security.log'])
    events = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(events)

    self.assertEqual(len(event_objects), 9)

    event_object = event_objects[0]
    expected_msg = (u'Sender: secd (1) Level: Error Facility: user '
                    u'Text: securityd_xpc_dictionary_handler EscrowSecurityAl'
                    u'[3273] DeviceInCircle')
    expected_msg_short = (u'Text: securityd_xpc_dictionary_handler '
                          u'EscrowSecurityAl[3273] DeviceInCircle')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)
    # date -u -d"Tue, 26 Feb 2013 19:11:56" +"%s000000"
    self.assertEqual(event_object.timestamp, 1361905916000000)
    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 1)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'unknown')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Error')
    expected_msg = (u'securityd_xpc_dictionary_handler EscrowSecurityAl'
                    u'[3273] DeviceInCircle')
    self.assertEqual(event_object.message, expected_msg)

    event_object = event_objects[1]
    # date -u -d"Thu, 26 Dec 2013 19:11:57" +"%s000000"
    self.assertEqual(event_object.timestamp, 1388085117000000)
    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 11)
    self.assertEqual(event_object.facility, u'serverxpc')
    self.assertEqual(event_object.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Notice')

    event_object = event_objects[2]
    # date -u -d"Thu, 26 Dec 2013 19:11:58" +"%s000000"
    self.assertEqual(event_object.timestamp, 1388085118000000)
    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 111)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'unknown')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Debug')

    event_object = event_objects[3]
    # date -u -d"Thu, 26 Dec 2013 19:11:59" +"%s000000"
    self.assertEqual(event_object.timestamp, 1388085119000000)
    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 1111)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_object.caller, u'C0x7fff872fa482')
    self.assertEqual(event_object.level, u'Error')

    event_object = event_objects[4]
    # date -u -d"Fri, 06 Dec 2013 19:11:01" +"%s000000"
    self.assertEqual(event_object.timestamp, 1386357061000000)
    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 1)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'unknown')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Error')
    self.assertEqual(event_object.message, u'')

    event_object = event_objects[5]
    # date -u -d"Fri, 06 Dec 2013 19:11:02" +"%s000000"
    self.assertEqual(event_object.timestamp, 1386357062000000)
    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 11111)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_object.caller, u'C0x7fff872fa482 F0x106080db0')
    self.assertEqual(event_object.level, u'Error')
    self.assertEqual(event_object.message, u'')

    # date -u -d"Tue, 31 Dec 2013 23:59:59" +"%s000000"
    event_object = event_objects[6]
    self.assertEqual(event_object.timestamp, 1388534399000000)
    # date -u -d"Sat, 01 Mar 2014 00:00:01" +"%s000000"
    event_object = event_objects[7]
    self.assertEqual(event_object.timestamp, 1393632001000000)

    # Repeated line.
    event_object = event_objects[8]
    expected_msg = u'Repeated 3 times: Happy new year!'
    self.assertEqual(event_object.message, expected_msg)


if __name__ == '__main__':
  unittest.main()
