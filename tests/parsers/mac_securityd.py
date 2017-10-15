#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains a unit test for ASL securityd log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_securityd as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers import mac_securityd

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class MacSecurityUnitTest(test_lib.ParserTestCase):
  """A unit test for the ASL securityd log parser."""

  @shared_test_lib.skipUnlessHasTestFile(['security.log'])
  def testParseFile(self):
    """Test parsing of a ASL securityd log file."""
    parser = mac_securityd.MacSecuritydLogParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['security.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    event = events[0]
    expected_message = (
        'Sender: secd (1) Level: Error Facility: user '
        'Text: securityd_xpc_dictionary_handler EscrowSecurityAl'
        '[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 '
        'virka l\xedka, setja \xedslensku inn.')
    expected_short_message = (
        'Text: securityd_xpc_dictionary_handler '
        'EscrowSecurityAl[3273] DeviceInCircle ...')
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-02-26 19:11:56')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, 'secd')
    self.assertEqual(event.sender_pid, 1)
    self.assertEqual(event.facility, 'user')
    self.assertEqual(event.security_api, 'unknown')
    self.assertEqual(event.caller, 'unknown')
    self.assertEqual(event.level, 'Error')
    expected_message = (
        'securityd_xpc_dictionary_handler EscrowSecurityAl'
        '[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 virka '
        'l\xedka, setja \xedslensku inn.')
    self.assertEqual(event.message, expected_message)

    event = events[1]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-12-26 19:11:57')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, 'secd')
    self.assertEqual(event.sender_pid, 11)
    self.assertEqual(event.facility, 'serverxpc')
    self.assertEqual(event.security_api, 'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event.caller, 'unknown')
    self.assertEqual(event.level, 'Notice')

    event = events[2]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-12-26 19:11:58')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, 'secd')
    self.assertEqual(event.sender_pid, 111)
    self.assertEqual(event.facility, 'user')
    self.assertEqual(event.security_api, 'unknown')
    self.assertEqual(event.caller, 'unknown')
    self.assertEqual(event.level, 'Debug')

    event = events[3]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-12-26 19:11:59')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, 'secd')
    self.assertEqual(event.sender_pid, 1111)
    self.assertEqual(event.facility, 'user')
    self.assertEqual(event.security_api, 'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event.caller, 'C0x7fff872fa482')
    self.assertEqual(event.level, 'Error')

    event = events[4]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-12-06 19:11:01')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, 'secd')
    self.assertEqual(event.sender_pid, 1)
    self.assertEqual(event.facility, 'user')
    self.assertEqual(event.security_api, 'unknown')
    self.assertEqual(event.caller, 'unknown')
    self.assertEqual(event.level, 'Error')
    self.assertEqual(event.message, '')

    event = events[5]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-12-06 19:11:02')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.sender, 'secd')
    self.assertEqual(event.sender_pid, 11111)
    self.assertEqual(event.facility, 'user')
    self.assertEqual(event.security_api, 'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event.caller, 'C0x7fff872fa482 F0x106080db0')
    self.assertEqual(event.level, 'Error')
    self.assertEqual(event.message, '')

    event = events[6]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-12-31 23:59:59')
    self.assertEqual(event.timestamp, expected_timestamp)

    event = events[7]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2014-03-01 00:00:01')
    self.assertEqual(event.timestamp, expected_timestamp)

    # Repeated line.
    event = events[8]
    expected_message = 'Repeated 3 times: Happy new year!'
    self.assertEqual(event.message, expected_message)


if __name__ == '__main__':
  unittest.main()
