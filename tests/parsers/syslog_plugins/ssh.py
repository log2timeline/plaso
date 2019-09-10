#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SSH syslog plugin."""

from __future__ import unicode_literals

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

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'syslog:line')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2016-03-11 19:26:39.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'syslog:ssh:login')
    self.assertEqual(event_data.address, '192.168.0.1')

    expected_body = (
        'Accepted publickey for plaso from 192.168.0.1 port 59229 ssh2: '
        'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')
    self.assertEqual(expected_body, event_data.body)

    expected_fingerprint = (
        'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')
    self.assertEqual(expected_fingerprint, event_data.fingerprint)

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2016-03-11 22:55:30.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'syslog:ssh:failed_connection')
    self.assertEqual(event_data.address, '001:db8:a0b:12f0::1')
    self.assertEqual(event_data.port, '8759')

    event = events[4]

    self.CheckTimestamp(event.timestamp, '2016-03-11 22:55:31.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.data_type, 'syslog:ssh:opened_connection')
    self.assertEqual(event_data.address, '188.124.3.41')

    event = events[7]

    self.CheckTimestamp(event.timestamp, '2016-03-11 22:55:34.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.address, '192.0.2.60')
    self.assertEqual(event_data.port, '20042')
    self.assertEqual(event_data.username, 'fred')


if __name__ == '__main__':
  unittest.main()
