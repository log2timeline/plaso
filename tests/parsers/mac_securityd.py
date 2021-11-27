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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'caller': 'unknown',
        'data_type': 'mac:securityd:line',
        'date_time': '2013-02-26 19:11:56',
        'facility': 'user',
        'level': 'Error',
        'message': (
            'securityd_xpc_dictionary_handler EscrowSecurityAl'
            '[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 virka '
            'l\xedka, setja \xedslensku inn.'),
        'security_api': 'unknown',
        'sender_pid': 1,
        'sender': 'secd'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'caller': 'unknown',
        'data_type': 'mac:securityd:line',
        'date_time': '2013-12-26 19:11:57',
        'facility': 'serverxpc',
        'level': 'Notice',
        'security_api': 'SOSCCThisDeviceIsInCircle',
        'sender_pid': 11,
        'sender': 'secd'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'caller': 'unknown',
        'data_type': 'mac:securityd:line',
        'date_time': '2013-12-26 19:11:58',
        'facility': 'user',
        'level': 'Debug',
        'security_api': 'unknown',
        'sender_pid': 111,
        'sender': 'secd'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'caller': 'C0x7fff872fa482',
        'data_type': 'mac:securityd:line',
        'date_time': '2013-12-26 19:11:59',
        'facility': 'user',
        'level': 'Error',
        'security_api': 'SOSCCThisDeviceIsInCircle',
        'sender_pid': 1111,
        'sender': 'secd'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'caller': 'unknown',
        'data_type': 'mac:securityd:line',
        'date_time': '2013-12-06 19:11:01',
        'facility': 'user',
        'level': 'Error',
        'message': '',
        'security_api': 'unknown',
        'sender_pid': 1,
        'sender': 'secd'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'caller': 'C0x7fff872fa482 F0x106080db0',
        'data_type': 'mac:securityd:line',
        'date_time': '2013-12-06 19:11:02',
        'facility': 'user',
        'level': 'Error',
        'message': '',
        'security_api': 'SOSCCThisDeviceIsInCircle',
        'sender_pid': 11111,
        'sender': 'secd'}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:securityd:line',
        'date_time': '2013-12-31 23:59:59'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'data_type': 'mac:securityd:line',
        'date_time': '2014-03-01 00:00:01'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    # Repeated line.
    expected_event_values = {
        'data_type': 'mac:securityd:line',
        'message': 'Repeated 3 times: Happy new year!'}

    self.CheckEventValues(storage_writer, events[8], expected_event_values)


if __name__ == '__main__':
  unittest.main()
