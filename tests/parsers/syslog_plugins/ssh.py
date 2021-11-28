#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SSH syslog plugin."""

import unittest

from tests.parsers.syslog_plugins import test_lib


class SSHSyslogPluginTest(test_lib.SyslogPluginTestCase):
  """Tests for the SSH syslog plugin."""

  def testParse(self):
    """Tests the Parse function."""
    knowledge_base_values = {'year': 2016}

    storage_writer = self._ParseFileWithPlugin(
        ['syslog_ssh.log'], 'ssh',
        knowledge_base_values=knowledge_base_values)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'data_type': 'syslog:line'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_body = (
        'Accepted publickey for plaso from 192.168.0.1 port 59229 ssh2: '
        'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')

    expected_fingerprint = (
        'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')

    expected_event_values = {
        'address': '192.168.0.1',
        'body': expected_body,
        'date_time': '2016-03-11 19:26:39',
        'data_type': 'syslog:ssh:login',
        'fingerprint': expected_fingerprint}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'address': '001:db8:a0b:12f0::1',
        'date_time': '2016-03-11 22:55:30',
        'data_type': 'syslog:ssh:failed_connection',
        'port': '8759'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'address': '188.124.3.41',
        'date_time': '2016-03-11 22:55:31',
        'data_type': 'syslog:ssh:opened_connection'}

    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'address': '192.0.2.60',
        'date_time': '2016-03-11 22:55:34',
        'data_type': 'syslog:ssh:login',
        'port': '20042',
        'username': 'fred'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

  def testParseWithTimeZone(self):
    """Tests the Parse function with a time zone."""
    knowledge_base_values = {'year': 2016}

    storage_writer = self._ParseFileWithPlugin(
        ['syslog_ssh.log'], 'ssh',
        knowledge_base_values=knowledge_base_values, timezone='CET')

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetSortedEvents())

    expected_body = (
        'Accepted publickey for plaso from 192.168.0.1 port 59229 ssh2: '
        'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')

    expected_fingerprint = (
        'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')

    expected_event_values = {
        'address': '192.168.0.1',
        'body': expected_body,
        'date_time': '2016-03-11 19:26:39',
        'data_type': 'syslog:ssh:login',
        'fingerprint': expected_fingerprint,
        'timestamp': '2016-03-11 18:26:39.000000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
