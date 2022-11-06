#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SSH syslog plugin."""

import unittest

from tests.parsers.syslog_plugins import test_lib


class SSHSyslogPluginTest(test_lib.SyslogPluginTestCase):
  """Tests for the SSH syslog plugin."""

  def testParse(self):
    """Tests the Parse function."""
    storage_writer = self._ParseFileWithPlugin(['syslog_ssh.log'], 'ssh')

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'syslog:line',
        'last_written_time': '0000-03-11T00:00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'address': '192.168.0.1',
        'body': (
            'Accepted publickey for plaso from 192.168.0.1 port 59229 ssh2: '
            'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99'),
        'data_type': 'syslog:ssh:login',
        'fingerprint': 'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99',
        'last_written_time': '0000-03-11T19:26:39'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'address': '001:db8:a0b:12f0::1',
        'data_type': 'syslog:ssh:failed_connection',
        'last_written_time': '0000-03-11T22:55:30',
        'port': '8759'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 3)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'address': '188.124.3.41',
        'data_type': 'syslog:ssh:opened_connection',
        'last_written_time': '0000-03-11T22:55:31'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
