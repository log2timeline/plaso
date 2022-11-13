#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iOS lockdown daemon log files parser."""

import unittest

from plaso.parsers import ios_lockdownd

from tests.parsers import test_lib


class IOSLockdowndLogParserTest(test_lib.ParserTestCase):
  """Tests for the iOS lockdown daemon log files parser."""

  def testParseLog(self):
    """Tests the Parse function."""
    parser = ios_lockdownd.IOSLockdowndLogParser()
    storage_writer = self._ParseFile(['ios_lockdownd.log'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 153)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 153)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': (
            'handle_get_value: AMPDevicesAgent attempting to get '
            '[InternationalMobileSubscriberIdentity2]'),
        'data_type': 'ios:lockdownd_log:entry',
        'process_identifier': 69,
        'written_time': '2021-10-13T07:57:42.869324+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 6)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'body': (
            'spawn_xpc_service_block_invoke: description of xpc reply: '
            '<dictionary: 0x2029c5070> { count = 1, transaction: 0, voucher'
            ' = 0x0, contents =	"XPCErrorDescription" => <string: '
            '0x2029c5230> { length = 22, contents = "Connection '
            'interrupted" }}'),
        'data_type': 'ios:lockdownd_log:entry',
        'process_identifier': 69,
        'written_time': '2021-10-13T07:57:42.950704+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 99)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
