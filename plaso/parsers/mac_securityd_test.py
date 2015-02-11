#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains a unit test for ASL securityd log parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import mac_securityd as mac_securityd_formatter
from plaso.lib import timelib_test
from plaso.parsers import mac_securityd as mac_securityd_parser
from plaso.parsers import test_lib


class MacSecurityUnitTest(test_lib.ParserTestCase):
  """A unit test for the ASL securityd log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = mac_securityd_parser.MacSecuritydLogParser()

  def testParseFile(self):
    """Test parsing of a ASL securityd log file."""
    knowledge_base_values = {'year': 2013}
    test_file = self._GetTestFilePath(['security.log'])
    events = self._ParseFile(
        self._parser, test_file, knowledge_base_values=knowledge_base_values)
    event_objects = self._GetEventObjectsFromQueue(events)

    self.assertEqual(len(event_objects), 9)

    event_object = event_objects[0]
    expected_msg = (
        u'Sender: secd (1) Level: Error Facility: user '
        u'Text: securityd_xpc_dictionary_handler EscrowSecurityAl'
        u'[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 '
        u'virka l\xedka, setja \xedslensku inn.')
    expected_msg_short = (
        u'Text: securityd_xpc_dictionary_handler '
        u'EscrowSecurityAl[3273] DeviceInCircle ...')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-02-26 19:11:56')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 1)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'unknown')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Error')
    expected_msg = (
        u'securityd_xpc_dictionary_handler EscrowSecurityAl'
        u'[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 virka '
        u'l\xedka, setja \xedslensku inn.')
    self.assertEqual(event_object.message, expected_msg)

    event_object = event_objects[1]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-12-26 19:11:57')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 11)
    self.assertEqual(event_object.facility, u'serverxpc')
    self.assertEqual(event_object.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Notice')

    event_object = event_objects[2]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-12-26 19:11:58')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 111)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'unknown')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Debug')

    event_object = event_objects[3]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-12-26 19:11:59')
    self.assertEqual(event_object.timestamp, 1388085119000000)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 1111)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_object.caller, u'C0x7fff872fa482')
    self.assertEqual(event_object.level, u'Error')

    event_object = event_objects[4]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-12-06 19:11:01')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 1)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'unknown')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Error')
    self.assertEqual(event_object.message, u'')

    event_object = event_objects[5]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-12-06 19:11:02')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 11111)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_object.caller, u'C0x7fff872fa482 F0x106080db0')
    self.assertEqual(event_object.level, u'Error')
    self.assertEqual(event_object.message, u'')

    event_object = event_objects[6]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-12-31 23:59:59')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    event_object = event_objects[7]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-03-01 00:00:01')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Repeated line.
    event_object = event_objects[8]
    expected_msg = u'Repeated 3 times: Happy new year!'
    self.assertEqual(event_object.message, expected_msg)


if __name__ == '__main__':
  unittest.main()
