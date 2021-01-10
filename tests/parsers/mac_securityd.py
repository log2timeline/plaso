#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This file contains a unit test for MacOS securityd log parser."""

import unittest

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

    expected_event_values = {
        'caller': 'unknown',
        'data_type': 'mac:securityd:line',
        'facility': 'user',
        'level': 'Error',
        'message': (
            'securityd_xpc_dictionary_handler EscrowSecurityAl'
            '[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 virka '
            'l\xedka, setja \xedslensku inn.'),
        'security_api': 'unknown',
        'sender_pid': 1,
        'sender': 'secd',
        'timestamp': '2013-02-26 19:11:56.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'caller': 'unknown',
        'data_type': 'mac:securityd:line',
        'facility': 'serverxpc',
        'level': 'Notice',
        'security_api': 'SOSCCThisDeviceIsInCircle',
        'sender_pid': 11,
        'sender': 'secd',
        'timestamp': '2013-12-26 19:11:57.000000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'caller': 'unknown',
        'data_type': 'mac:securityd:line',
        'facility': 'user',
        'level': 'Debug',
        'security_api': 'unknown',
        'sender_pid': 111,
        'sender': 'secd',
        'timestamp': '2013-12-26 19:11:58.000000'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'caller': 'C0x7fff872fa482',
        'data_type': 'mac:securityd:line',
        'facility': 'user',
        'level': 'Error',
        'security_api': 'SOSCCThisDeviceIsInCircle',
        'sender_pid': 1111,
        'sender': 'secd',
        'timestamp': '2013-12-26 19:11:59.000000'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'caller': 'unknown',
        'data_type': 'mac:securityd:line',
        'facility': 'user',
        'level': 'Error',
        'message': '',
        'security_api': 'unknown',
        'sender_pid': 1,
        'sender': 'secd',
        'timestamp': '2013-12-06 19:11:01.000000'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'caller': 'C0x7fff872fa482 F0x106080db0',
        'data_type': 'mac:securityd:line',
        'facility': 'user',
        'level': 'Error',
        'message': '',
        'security_api': 'SOSCCThisDeviceIsInCircle',
        'sender_pid': 11111,
        'sender': 'secd',
        'timestamp': '2013-12-06 19:11:02.000000'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:securityd:line',
        'timestamp': '2013-12-31 23:59:59.000000'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:securityd:line',
        'timestamp': '2014-03-01 00:00:01.000000'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    # Repeated line.
    expected_event_values = {
        'data_type': 'mac:securityd:line',
        'message': 'Repeated 3 times: Happy new year!'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)


if __name__ == '__main__':
  unittest.main()
