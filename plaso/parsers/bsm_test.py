#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
"""Parser test for Basic Security Module."""

import os
import pytz
import unittest

# pylint: disable=W0611
from plaso.formatters import bsm as bsm_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import bsm as bsm_parser
from plaso.parsers import test_lib
from plaso.pvfs import utils

class BsmParserTest(unittest.TestCase):
  """The unit test for BSM parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    mac_pre_obj = preprocess.PlasoPreprocess()
    mac_pre_obj.guessed_os = 'MacOSX'
    mac_pre_obj.zone = pytz.UTC
    self._parser_macbsm = bsm_parser.BsmParser(mac_pre_obj, None)

    openbsm_pre_obj = preprocess.PlasoPreprocess()
    openbsm_pre_obj.guessed_os = 'openbsm'
    openbsm_pre_obj.zone = pytz.UTC
    self._parser_openbsm = bsm_parser.BsmParser(openbsm_pre_obj, None)

  def testParseFile(self):
    """Read BSM files and make few tests."""

    # Mac OS X BSM
    test_file_mac = os.path.join('test_data', 'apple.bsm')
    events = test_lib.ParseFile(self._parser_macbsm, test_file_mac)

    self.assertEqual(len(events), 54)

    event = events[0]
    expected_type = event.data_type
    self.assertEqual(expected_type, 'mac:bsm:event')
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(event)
    expected_msg = (u'Type: audit crash '
                    u'recovery (45029) Return: [BSM_TOKEN_RETURN32: Success (0)'
                    u', System call status: 0] Information: [BSM_TOKEN_TEXT: '
                    u'launchctl::Audit recovery]. [BSM_TOKEN_PATH: '
                    u'/var/audit/20131104171720.crash_recovery]')
    self.assertEqual(expected_msg, msg)
    # date -u -d"Mon, 04 Nov 2013 18:36:20" +"%s000381"
    self.assertEqual(1383590180000381, event.timestamp)
    self.assertEqual(u'audit crash recovery (45029)', event.event_type)
    expected_msg = (u'[BSM_TOKEN_TEXT: launchctl::Audit recovery]. '
                    u'[BSM_TOKEN_PATH: '
                    u'/var/audit/20131104171720.crash_recovery]')
    self.assertEqual(expected_msg, event.extra_tokens)
    expected_msg = u'[BSM_TOKEN_RETURN32: Success (0), System call status: 0]'
    self.assertEqual(expected_msg, event.return_value)

    event = events[15]
    # date -u -d"Mon, 04 Nov 2013 18:36:26" +"%s000171"
    self.assertEqual(1383590186000171, event.timestamp)
    self.assertEqual(u'user authentication (45023)', event.event_type)
    expected_msg = (u'[BSM_TOKEN_SUBJECT32: aid(4294967295), euid(92), '
                    u'egid(92), uid(92), gid(92), pid(143), '
                    u'session_id(100004), terminal_port(143), '
                    u'terminal_ip(0.0.0.0)]. '
                    u'[BSM_TOKEN_TEXT: Verify password for record type Users '
                    u'\'moxilo\' node \'/Local/Default\']')
    self.assertEqual(expected_msg, event.extra_tokens)
    expected_msg = (u'[BSM_TOKEN_RETURN32: Unknown (255), '
                    u'System call status: 5000]')
    self.assertEqual(expected_msg, event.return_value)

    event = events[31]
    # date -u -d"Mon, 04 Nov 2013 18:36:26" +"%s000530"
    self.assertEqual(1383590186000530, event.timestamp)
    self.assertEqual(u'SecSrvr AuthEngine (45025)', event.event_type)
    expected_msg = (u'[BSM_TOKEN_SUBJECT32: aid(4294967295), euid(0), egid(0), '
                    u'uid(0), gid(0), pid(67), session_id(100004)'
                    u', terminal_port(67), terminal_ip(0.0.0.0)]. '
                    u'[BSM_TOKEN_TEXT: system.login.done]. '
                    u'[BSM_TOKEN_TEXT: system.login.done]')
    self.assertEqual(expected_msg, event.extra_tokens)
    expected_msg = u'[BSM_TOKEN_RETURN32: Success (0), System call status: 0]'
    self.assertEqual(expected_msg, event.return_value)

    event = events[50]
    # date -u -d"Mon, 04 Nov 2013 18:37:36" +"%s000399"
    self.assertEqual(1383590256000399, event.timestamp)
    self.assertEqual(u'session end (44903)', event.event_type)
    expected_msg = (u'[BSM_TOKEN_ARGUMENT64: sflags(1) is 0x0]. '
                    u'[BSM_TOKEN_ARGUMENT32: am_success(2) is 0x3000]. '
                    u'[BSM_TOKEN_ARGUMENT32: am_failure(3) is 0x3000]. '
                    u'[BSM_TOKEN_SUBJECT32: aid(4294967295), euid(0), egid(0), '
                    u'uid(0), gid(0), pid(0), session_id(100015), '
                    u'terminal_port(0), terminal_ip(0.0.0.0)]')
    self.assertEqual(expected_msg, event.extra_tokens)
    expected_msg = u'[BSM_TOKEN_RETURN32: Success (0), System call status: 0]'
    self.assertEqual(expected_msg, event.return_value)

    # Generic BSM
    test_file_openbsm = os.path.join('test_data', 'openbsm.bsm')
    events = test_lib.ParseFile(self._parser_openbsm, test_file_openbsm)

    event = events[0]
    expected_msg = u'[BSM_TOKEN_ARGUMENT32: test_arg32_token(3) is 0xABCDEF00]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[1]
    expected_msg = u'[BSM_TOKEN_DATA: Format data: String, Data: SomeData]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[2]
    expected_msg = u'[BSM_TOKEN_FILE: test, timestamp: 1970-01-01 20:42:45]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[3]
    expected_msg = u'[BSM_TOKEN_ADDR: 192.168.100.15]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[4]
    expected_msg = (u'[IPv4_Header: 0x4000001454780000'
                    u'40010000c0a8649bc0a86e30]')
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[5]
    expected_msg = u'[BSM_TOKEN_IPC: object type 1, object id 305419896]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[6]
    expected_msg = u'[BSM_TOKEN_PORT: 20480]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[7]
    expected_msg = u'[BSM_TOKEN_OPAQUE: aabbccdd]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[8]
    expected_msg = u'[BSM_TOKEN_PATH: /test/this/is/a/test]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[9]
    expected_msg = (u'[BSM_TOKEN_PROCESS32: aid(305419896), euid(19088743), '
                    u'egid(591751049), uid(2557891634), gid(159868227), '
                    u'pid(321140038), session_id(2542171492), '
                    u'terminal_port(374945606), terminal_ip(127.0.0.1)]')
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[10]
    expected_msg = (u'[BSM_TOKEN_PROCESS64: aid(305419896), euid(19088743), '
                    u'egid(591751049), uid(2557891634), gid(159868227), '
                    u'pid(321140038), session_id(2542171492), '
                    u'terminal_port(374945606), terminal_ip(127.0.0.1)]')
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[11]
    expected_msg = (u'[BSM_TOKEN_RETURN32: Invalid argument (22), '
                    u'System call status: 305419896]')
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[12]
    expected_msg = u'[BSM_TOKEN_SEQUENCE: 305419896]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[13]
    expected_msg = (u'[BSM_TOKEN_AUT_SOCKINET32_EX: '
                    u'from 127.0.0.1 port 0 to 127.0.0.1 port 0]')
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[14]
    expected_msg = (u'[BSM_TOKEN_SUBJECT32: aid(305419896), euid(19088743), '
                    u'egid(591751049), uid(2557891634), gid(159868227), '
                    u'pid(321140038), session_id(2542171492), '
                    u'terminal_port(374945606), terminal_ip(127.0.0.1)]')
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[15]
    expected_msg = (u'[BSM_TOKEN_SUBJECT32_EX: aid(305419896), euid(19088743), '
                    u'egid(591751049), uid(2557891634), gid(159868227), '
                    u'pid(321140038), session_id(2542171492), '
                    u'terminal_port(374945606), terminal_ip(fe80::1)]')
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[16]
    expected_msg = u'[BSM_TOKEN_TEXT: This is a test.]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[17]
    expected_msg = u'[BSM_TOKEN_ZONENAME: testzone]'
    self.assertEqual(expected_msg, event.extra_tokens)
    event = events[18]
    expected_msg = (u'[BSM_TOKEN_RETURN32: Argument list too long (7), '
                    u'System call status: 4294967295]')
    self.assertEqual(expected_msg, event.extra_tokens)

    self.assertEqual(len(events), 50)


if __name__ == '__main__':
  unittest.main()
