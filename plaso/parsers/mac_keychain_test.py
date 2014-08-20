#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Tests for Keychain password database parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import mac_keychain as mac_keychain_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import test_lib
from plaso.parsers import mac_keychain


class MacKeychainParserTest(test_lib.ParserTestCase):
  """Tests for keychain file parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = mac_keychain.KeychainParser(pre_obj)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['login.keychain'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEqual(len(event_objects), 5)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-01-26 14:51:48')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(
        event_object.timestamp_desc,
        eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.entry_name, u'Secret Application')
    self.assertEqual(event_object.account_name, u'moxilo')
    expected_ssgp = (u'b8e44863af1cb0785b89681d22e2721997cc'
                     u'fb8adb8853e726aff94c8830b05a')
    self.assertEqual(event_object.ssgp_hash, expected_ssgp)
    self.assertEqual(event_object.text_description, u'N/A')
    expected_msg = u'Name: Secret Application Account: moxilo'
    expected_msg_short = u'Secret Application'
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)
    event_object = event_objects[1]
    self.assertEqual(
        event_object.timestamp_desc,
        eventdata.EventTimestamp.MODIFICATION_TIME)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-01-26 14:52:29')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    event_object = event_objects[2]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-01-26 14:53:29')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.entry_name, u'Secret Note')
    self.assertEqual(event_object.text_description, u'secure note')
    self.assertEqual(len(event_object.ssgp_hash), 1696)
    expected_msg = u'Name: Secret Note'
    expected_msg_short = u'Secret Note'
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[3]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-01-26 14:54:33')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.entry_name, u'plaso.kiddaland.net')
    self.assertEqual(event_object.account_name, u'MrMoreno')
    expected_ssgp = (u'83ccacf55a8cb656d340ec405e9d8b308f'
                     u'ac54bb79c5c9b0219bd0d700c3c521')
    self.assertEqual(event_object.ssgp_hash, expected_ssgp)
    self.assertEqual(event_object.where, u'plaso.kiddaland.net')
    self.assertEqual(event_object.protocol, u'http')
    self.assertEqual(event_object.type_protocol, u'dflt')
    self.assertEqual(event_object.text_description, u'N/A')
    expected_msg = (u'Name: plaso.kiddaland.net Account: MrMoreno Where: '
                    u'plaso.kiddaland.net Protocol: http (dflt)')
    expected_msg_short = u'plaso.kiddaland.net'
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
