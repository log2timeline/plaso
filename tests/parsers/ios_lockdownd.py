#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iOS lockdown daemon log files parser."""

import unittest

from plaso.parsers import ios_lockdownd

from tests.parsers import test_lib


class IOSLockdownLogUnitTest(test_lib.ParserTestCase):
  """Tests for the iOS lockdown daemon log files parser."""

  def testParseLog(self):
    """Tests the Parse function."""
    parser = ios_lockdownd.IOSLockdownParser()
    storage_writer = self._ParseFile(['ios_lockdownd.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 153)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'body': (
            'handle_get_value: AMPDevicesAgent attempting to get '
            '[InternationalMobileSubscriberIdentity2]'),
        'process_identifier': '69',
        'timestamp': '2021-10-13 07:57:42.869324'}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'body': (
            'spawn_xpc_service_block_invoke: description of xpc reply: '
            '<dictionary: 0x2029c5070> { count = 1, transaction: 0, voucher'
            ' = 0x0, contents =	"XPCErrorDescription" => <string: '
            '0x2029c5230> { length = 22, contents = "Connection '
            'interrupted" }}'),
        'process_identifier': '69',
        'timestamp': '2021-10-13 07:57:42.950704'}

    self.CheckEventValues(storage_writer, events[99], expected_event_values)


if __name__ == '__main__':
  unittest.main()
