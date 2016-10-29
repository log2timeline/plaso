#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains a unit test for ASL securityd log parser."""

import unittest

from plaso.formatters import mac_securityd  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import mac_securityd

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MacSecurityUnitTest(test_lib.ParserTestCase):
  """A unit test for the ASL securityd log parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'security.log'])
  def testParseFile(self):
    """Test parsing of a ASL securityd log file."""
    parser_object = mac_securityd.MacSecuritydLogParser()
    knowledge_base_values = {u'year': 2013}
    storage_writer = self._ParseFile(
        [u'security.log'], parser_object,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(len(storage_writer.events), 9)

    event_object = storage_writer.events[0]
    expected_msg = (
        u'Sender: secd (1) Level: Error Facility: user '
        u'Text: securityd_xpc_dictionary_handler EscrowSecurityAl'
        u'[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 '
        u'virka l\xedka, setja \xedslensku inn.')
    expected_msg_short = (
        u'Text: securityd_xpc_dictionary_handler '
        u'EscrowSecurityAl[3273] DeviceInCircle ...')
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-02-26 19:11:56')
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

    event_object = storage_writer.events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-26 19:11:57')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 11)
    self.assertEqual(event_object.facility, u'serverxpc')
    self.assertEqual(event_object.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Notice')

    event_object = storage_writer.events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-26 19:11:58')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 111)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'unknown')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Debug')

    event_object = storage_writer.events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-26 19:11:59')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 1111)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_object.caller, u'C0x7fff872fa482')
    self.assertEqual(event_object.level, u'Error')

    event_object = storage_writer.events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-06 19:11:01')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 1)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'unknown')
    self.assertEqual(event_object.caller, u'unknown')
    self.assertEqual(event_object.level, u'Error')
    self.assertEqual(event_object.message, u'')

    event_object = storage_writer.events[5]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-06 19:11:02')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.sender, u'secd')
    self.assertEqual(event_object.sender_pid, 11111)
    self.assertEqual(event_object.facility, u'user')
    self.assertEqual(event_object.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_object.caller, u'C0x7fff872fa482 F0x106080db0')
    self.assertEqual(event_object.level, u'Error')
    self.assertEqual(event_object.message, u'')

    event_object = storage_writer.events[6]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-31 23:59:59')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    event_object = storage_writer.events[7]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-03-01 00:00:01')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Repeated line.
    event_object = storage_writer.events[8]
    expected_msg = u'Repeated 3 times: Happy new year!'
    self.assertEqual(event_object.message, expected_msg)


if __name__ == '__main__':
  unittest.main()
