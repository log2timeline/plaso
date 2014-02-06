#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""Tests for Basic Security Module (BSM) file parser."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import bsm as bsm_formatter
from plaso.lib import event
from plaso.parsers import bsm
from plaso.parsers import test_lib


class BsmParserTest(test_lib.ParserTestCase):
  """Tests for Basic Security Module (BSM) file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    mac_pre_obj = event.PreprocessObject()
    mac_pre_obj.guessed_os = 'MacOSX'
    self._parser_macbsm = bsm.BsmParser(mac_pre_obj, None)

    openbsm_pre_obj = event.PreprocessObject()
    openbsm_pre_obj.guessed_os = 'openbsm'
    self._parser_openbsm = bsm.BsmParser(openbsm_pre_obj, None)

  def testParse(self):
    """Tests the Parse function on a "generic" BSM file."""
    test_file = self._GetTestFilePath(['openbsm.bsm'])
    event_generator = self._ParseFile(self._parser_openbsm, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEqual(len(event_objects), 50)

    expected_extra_tokens = [
        u'[BSM_TOKEN_ARGUMENT32: test_arg32_token(3) is 0xABCDEF00]',
        u'[BSM_TOKEN_DATA: Format data: String, Data: SomeData]',
        u'[BSM_TOKEN_FILE: test, timestamp: 1970-01-01 20:42:45]',
        u'[BSM_TOKEN_ADDR: 192.168.100.15]',
        u'[IPv4_Header: 0x400000145478000040010000c0a8649bc0a86e30]',
        u'[BSM_TOKEN_IPC: object type 1, object id 305419896]',
        u'[BSM_TOKEN_PORT: 20480]',
        u'[BSM_TOKEN_OPAQUE: aabbccdd]',
        u'[BSM_TOKEN_PATH: /test/this/is/a/test]',
        (u'[BSM_TOKEN_PROCESS32: aid(305419896), euid(19088743), '
         u'egid(591751049), uid(2557891634), gid(159868227), '
         u'pid(321140038), session_id(2542171492), '
         u'terminal_port(374945606), terminal_ip(127.0.0.1)]'),
        (u'[BSM_TOKEN_PROCESS64: aid(305419896), euid(19088743), '
         u'egid(591751049), uid(2557891634), gid(159868227), '
         u'pid(321140038), session_id(2542171492), '
         u'terminal_port(374945606), terminal_ip(127.0.0.1)]'),
        (u'[BSM_TOKEN_RETURN32: Invalid argument (22), '
         u'System call status: 305419896]'),
        u'[BSM_TOKEN_SEQUENCE: 305419896]',
        (u'[BSM_TOKEN_AUT_SOCKINET32_EX: '
         u'from 127.0.0.1 port 0 to 127.0.0.1 port 0]'),
        (u'[BSM_TOKEN_SUBJECT32: aid(305419896), euid(19088743), '
         u'egid(591751049), uid(2557891634), gid(159868227), '
         u'pid(321140038), session_id(2542171492), '
         u'terminal_port(374945606), terminal_ip(127.0.0.1)]'),
        (u'[BSM_TOKEN_SUBJECT32_EX: aid(305419896), euid(19088743), '
         u'egid(591751049), uid(2557891634), gid(159868227), '
         u'pid(321140038), session_id(2542171492), '
         u'terminal_port(374945606), terminal_ip(fe80::1)]'),
        u'[BSM_TOKEN_TEXT: This is a test.]',
        u'[BSM_TOKEN_ZONENAME: testzone]',
        (u'[BSM_TOKEN_RETURN32: Argument list too long (7), '
         u'System call status: 4294967295]')]

    extra_tokens = []
    for event_object_index in range(0, 19):
      extra_tokens.append(event_objects[event_object_index].extra_tokens)

    self.assertEqual(extra_tokens, expected_extra_tokens)

  def testParseFileMacOSX(self):
    """Tests the Parse function on a Mac OS X BSM file."""
    test_file = self._GetTestFilePath(['apple.bsm'])
    event_generator = self._ParseFile(self._parser_macbsm, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEqual(len(event_objects), 54)

    event_object = event_objects[0]

    self.assertEqual(event_object.data_type, 'mac:bsm:event')

    expected_msg = (
        u'Type: audit crash recovery (45029) '
        u'Return: [BSM_TOKEN_RETURN32: Success (0), System call status: 0] '
        u'Information: [BSM_TOKEN_TEXT: launchctl::Audit recovery]. '
        u'[BSM_TOKEN_PATH: /var/audit/20131104171720.crash_recovery]')

    expected_msg_short = (
        u'Type: audit crash recovery (45029) '
        u'Return: [BSM_TOKEN_RETURN32: Success (0), ...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    # date -u -d"Mon, 04 Nov 2013 18:36:20" +"%s000381"
    self.assertEqual(event_object.timestamp, 1383590180000381)
    self.assertEqual(event_object.event_type, u'audit crash recovery (45029)')

    expected_extra_tokens = (
        u'[BSM_TOKEN_TEXT: launchctl::Audit recovery]. '
        u'[BSM_TOKEN_PATH: /var/audit/20131104171720.crash_recovery]')
    self.assertEqual(event_object.extra_tokens, expected_extra_tokens)

    expected_return_value = (
        u'[BSM_TOKEN_RETURN32: Success (0), System call status: 0]')
    self.assertEqual(event_object.return_value, expected_return_value)

    event_object = event_objects[15]
    # date -u -d"Mon, 04 Nov 2013 18:36:26" +"%s000171"
    self.assertEqual(event_object.timestamp, 1383590186000171)
    self.assertEqual(event_object.event_type, u'user authentication (45023)')

    expected_extra_tokens = (
        u'[BSM_TOKEN_SUBJECT32: aid(4294967295), euid(92), egid(92), uid(92), '
        u'gid(92), pid(143), session_id(100004), terminal_port(143), '
        u'terminal_ip(0.0.0.0)]. '
        u'[BSM_TOKEN_TEXT: Verify password for record type Users '
        u'\'moxilo\' node \'/Local/Default\']')
    self.assertEqual(event_object.extra_tokens, expected_extra_tokens)

    expected_return_value = (
        u'[BSM_TOKEN_RETURN32: Unknown (255), System call status: 5000]')
    self.assertEqual(event_object.return_value, expected_return_value)

    event_object = event_objects[31]
    # date -u -d"Mon, 04 Nov 2013 18:36:26" +"%s000530"
    self.assertEqual(event_object.timestamp, 1383590186000530)
    self.assertEqual(event_object.event_type, u'SecSrvr AuthEngine (45025)')
    expected_extra_tokens = (
        u'[BSM_TOKEN_SUBJECT32: aid(4294967295), euid(0), egid(0), uid(0), '
        u'gid(0), pid(67), session_id(100004), terminal_port(67), '
        u'terminal_ip(0.0.0.0)]. '
        u'[BSM_TOKEN_TEXT: system.login.done]. '
        u'[BSM_TOKEN_TEXT: system.login.done]')
    self.assertEqual(event_object.extra_tokens, expected_extra_tokens)

    expected_return_value = (
        u'[BSM_TOKEN_RETURN32: Success (0), System call status: 0]')
    self.assertEqual(event_object.return_value, expected_return_value)

    event_object = event_objects[50]

    # date -u -d"Mon, 04 Nov 2013 18:37:36" +"%s000399"
    self.assertEqual(event_object.timestamp, 1383590256000399)
    self.assertEqual(event_object.event_type, u'session end (44903)')

    expected_extra_tokens = (
        u'[BSM_TOKEN_ARGUMENT64: sflags(1) is 0x0]. '
        u'[BSM_TOKEN_ARGUMENT32: am_success(2) is 0x3000]. '
        u'[BSM_TOKEN_ARGUMENT32: am_failure(3) is 0x3000]. '
        u'[BSM_TOKEN_SUBJECT32: aid(4294967295), euid(0), egid(0), uid(0), '
        u'gid(0), pid(0), session_id(100015), terminal_port(0), '
        u'terminal_ip(0.0.0.0)]')
    self.assertEqual(event_object.extra_tokens, expected_extra_tokens)

    expected_return_value = (
        u'[BSM_TOKEN_RETURN32: Success (0), System call status: 0]')
    self.assertEqual(event_object.return_value, expected_return_value)


if __name__ == '__main__':
  unittest.main()
