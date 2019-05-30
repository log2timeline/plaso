#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SSH syslog plugin."""

from __future__ import unicode_literals

import unittest

from tests import test_lib as shared_test_lib
from tests.parsers.syslog_plugins import test_lib


class SSHSyslogPluginTest(test_lib.SyslogPluginTestCase):
  """Tests for the SSH syslog plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['syslog_ssh.log'])
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
    self.assertEqual(event.data_type, 'syslog:line')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2016-03-11 19:26:39.000000')

    self.assertEqual(event.data_type, 'syslog:ssh:login')
    self.assertEqual(event.address, '192.168.0.1')

    expected_body = (
        'Accepted publickey for plaso from 192.168.0.1 port 59229 ssh2: '
        'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')
    self.assertEqual(expected_body, event.body)

    expected_fingerprint = (
        'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')
    self.assertEqual(expected_fingerprint, event.fingerprint)

    event = events[2]
    self.assertEqual(event.data_type, 'syslog:ssh:failed_connection')
    self.assertEqual(event.address, '001:db8:a0b:12f0::1')
    self.assertEqual(event.port, '8759')

    event = events[4]
    self.assertEqual(event.data_type, 'syslog:ssh:opened_connection')
    self.assertEqual(event.address, '188.124.3.41')

    event = events[7]
    self.assertEqual(event.address, '192.0.2.60')
    self.assertEqual(event.port, '20042')
    self.assertEqual(event.username, 'fred')

if __name__ == '__main__':
  unittest.main()
