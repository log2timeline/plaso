#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This file contains a unit test for MacOS securityd log parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_securityd as _  # pylint: disable=unused-import
from plaso.parsers import mac_securityd

from tests.parsers import test_lib


class MacOSSecurityUnitTest(test_lib.ParserTestCase):
  """A unit test for the MacOS securityd log parser."""

  def testParseFile(self):
    """Test parsing of a MacOS securityd log file."""
    parser = mac_securityd.MacOSSecuritydLogParser()
    knowledge_base_values = {'year': 2013}
    storage_writer = self._ParseFile(
        ['security.log'], parser,
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-02-26 19:11:56.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.sender, 'secd')
    self.assertEqual(event_data.sender_pid, 1)
    self.assertEqual(event_data.facility, 'user')
    self.assertEqual(event_data.security_api, 'unknown')
    self.assertEqual(event_data.caller, 'unknown')
    self.assertEqual(event_data.level, 'Error')
    expected_message = (
        'securityd_xpc_dictionary_handler EscrowSecurityAl'
        '[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 virka '
        'l\xedka, setja \xedslensku inn.')
    self.assertEqual(event_data.message, expected_message)

    expected_message = (
        'Sender: secd (1) Level: Error Facility: user '
        'Text: securityd_xpc_dictionary_handler EscrowSecurityAl'
        '[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 '
        'virka l\xedka, setja \xedslensku inn.')
    expected_short_message = (
        'Text: securityd_xpc_dictionary_handler '
        'EscrowSecurityAl[3273] DeviceInCircle ...')
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-12-26 19:11:57.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.sender, 'secd')
    self.assertEqual(event_data.sender_pid, 11)
    self.assertEqual(event_data.facility, 'serverxpc')
    self.assertEqual(event_data.security_api, 'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_data.caller, 'unknown')
    self.assertEqual(event_data.level, 'Notice')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2013-12-26 19:11:58.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.sender, 'secd')
    self.assertEqual(event_data.sender_pid, 111)
    self.assertEqual(event_data.facility, 'user')
    self.assertEqual(event_data.security_api, 'unknown')
    self.assertEqual(event_data.caller, 'unknown')
    self.assertEqual(event_data.level, 'Debug')

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2013-12-26 19:11:59.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.sender, 'secd')
    self.assertEqual(event_data.sender_pid, 1111)
    self.assertEqual(event_data.facility, 'user')
    self.assertEqual(event_data.security_api, 'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_data.caller, 'C0x7fff872fa482')
    self.assertEqual(event_data.level, 'Error')

    event = events[4]

    self.CheckTimestamp(event.timestamp, '2013-12-06 19:11:01.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.sender, 'secd')
    self.assertEqual(event_data.sender_pid, 1)
    self.assertEqual(event_data.facility, 'user')
    self.assertEqual(event_data.security_api, 'unknown')
    self.assertEqual(event_data.caller, 'unknown')
    self.assertEqual(event_data.level, 'Error')
    self.assertEqual(event_data.message, '')

    event = events[5]

    self.CheckTimestamp(event.timestamp, '2013-12-06 19:11:02.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.sender, 'secd')
    self.assertEqual(event_data.sender_pid, 11111)
    self.assertEqual(event_data.facility, 'user')
    self.assertEqual(event_data.security_api, 'SOSCCThisDeviceIsInCircle')
    self.assertEqual(event_data.caller, 'C0x7fff872fa482 F0x106080db0')
    self.assertEqual(event_data.level, 'Error')
    self.assertEqual(event_data.message, '')

    event = events[6]

    self.CheckTimestamp(event.timestamp, '2013-12-31 23:59:59.000000')

    event = events[7]

    self.CheckTimestamp(event.timestamp, '2014-03-01 00:00:01.000000')

    # Repeated line.
    event = events[8]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.message, 'Repeated 3 times: Happy new year!')


if __name__ == '__main__':
  unittest.main()
