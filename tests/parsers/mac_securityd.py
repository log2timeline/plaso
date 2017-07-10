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
    parser = mac_securityd.MacSecuritydLogParser()
    knowledge_base_values = {u'year': 2013}
    storage_writer = self._ParseFile(
        [u'security.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    event = events[0]
    expected_message = (
        u'Sender: secd (1) Level: Error Facility: user '
        u'Text: securityd_xpc_dictionary_handler EscrowSecurityAl'
        u'[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 '
        u'virka l\xedka, setja \xedslensku inn.')
    expected_short_message = (
        u'Text: securityd_xpc_dictionary_handler '
        u'EscrowSecurityAl[3273] DeviceInCircle ...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-02-26 19:11:56')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, u'secd')
    self.assertEqual(event.sender_pid, 1)
    self.assertEqual(event.facility, u'user')
    self.assertEqual(event.security_api, u'unknown')
    self.assertEqual(event.caller, u'unknown')
    self.assertEqual(event.level, u'Error')
    expected_message = (
        u'securityd_xpc_dictionary_handler EscrowSecurityAl'
        u'[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 virka '
        u'l\xedka, setja \xedslensku inn.')
    self.assertEqual(event.message, expected_message)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-26 19:11:57')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, u'secd')
    self.assertEqual(event.sender_pid, 11)
    self.assertEqual(event.facility, u'serverxpc')
    self.assertEqual(event.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event.caller, u'unknown')
    self.assertEqual(event.level, u'Notice')

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-26 19:11:58')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, u'secd')
    self.assertEqual(event.sender_pid, 111)
    self.assertEqual(event.facility, u'user')
    self.assertEqual(event.security_api, u'unknown')
    self.assertEqual(event.caller, u'unknown')
    self.assertEqual(event.level, u'Debug')

    event = events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-26 19:11:59')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, u'secd')
    self.assertEqual(event.sender_pid, 1111)
    self.assertEqual(event.facility, u'user')
    self.assertEqual(event.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event.caller, u'C0x7fff872fa482')
    self.assertEqual(event.level, u'Error')

    event = events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-06 19:11:01')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, u'secd')
    self.assertEqual(event.sender_pid, 1)
    self.assertEqual(event.facility, u'user')
    self.assertEqual(event.security_api, u'unknown')
    self.assertEqual(event.caller, u'unknown')
    self.assertEqual(event.level, u'Error')
    self.assertEqual(event.message, u'')

    event = events[5]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-06 19:11:02')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, u'secd')
    self.assertEqual(event.sender_pid, 11111)
    self.assertEqual(event.facility, u'user')
    self.assertEqual(event.security_api, u'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event.caller, u'C0x7fff872fa482 F0x106080db0')
    self.assertEqual(event.level, u'Error')
    self.assertEqual(event.message, u'')

    event = events[6]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-31 23:59:59')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[7]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-03-01 00:00:01')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Repeated line.
    event = events[8]
    expected_message = u'Repeated 3 times: Happy new year!'
    self.assertEqual(event.message, expected_message)


if __name__ == '__main__':
  unittest.main()
