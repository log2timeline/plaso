#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SSH syslog plugin."""
import unittest

from plaso.lib import timelib

from tests import test_lib as shared_test_lib
from tests.parsers.syslog_plugins import test_lib


class SSHSyslogParserTest(test_lib.SyslogPluginTestCase):
  """Tests for the SSH syslog plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'syslog_ssh.log'])
  def testParse(self):
    """Tests the Parse function."""
    knowledge_base_values = {u'year': 2016}

    storage_writer = self._ParseFileWithPlugin(
        [u'syslog_ssh.log'], u'ssh',
        knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 9)

    events = list(storage_writer.GetSortedEvents())

    event = events[0]
    self.assertEqual(event.data_type, u'syslog:line')

    event = events[1]
    self.assertEqual(event.data_type, u'syslog:ssh:login')
    self.assertEqual(event.address, u'192.168.0.1')

    expected_body = (
        u'Accepted publickey for plaso from 192.168.0.1 port 59229 ssh2: '
        u'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')
    self.assertEqual(expected_body, event.body)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-03-11 19:26:39')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_fingerprint = (
        u'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')
    self.assertEqual(expected_fingerprint, event.fingerprint)

    event = events[2]
    self.assertEqual(event.data_type, u'syslog:ssh:failed_connection')
    self.assertEqual(event.address, u'001:db8:a0b:12f0::1')
    self.assertEqual(event.port, u'8759')

    event = events[4]
    self.assertEqual(event.data_type, u'syslog:ssh:opened_connection')
    self.assertEqual(event.address, u'188.124.3.41')

    event = events[7]
    self.assertEqual(event.address, u'192.0.2.60')
    self.assertEqual(event.port, u'20042')
    self.assertEqual(event.username, u'fred')

if __name__ == '__main__':
  unittest.main()
