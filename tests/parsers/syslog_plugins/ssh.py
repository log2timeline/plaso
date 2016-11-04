#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SSH syslog plugin."""
import unittest

from plaso.lib import timelib
from plaso.parsers import syslog
from plaso.parsers.syslog_plugins import ssh

from tests import test_lib as shared_test_lib
from tests.parsers.syslog_plugins import test_lib


class SSHSyslogParserTest(test_lib.SyslogPluginTestCase):
  """Tests for the SSH syslog plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'syslog_ssh.log'])
  def testParse(self):
    """Tests the Parse function."""
    storage_writer = self._ParseFileWithPlugin(
        [u'syslog_ssh.log'], u'ssh')

    self.assertEqual(len(storage_writer.events), 9)

    event = storage_writer.events[0]

    expected_data_type = syslog.SyslogLineEvent.DATA_TYPE
    self.assertEqual(event.DATA_TYPE, expected_data_type)

    event = storage_writer.events[1]

    expected_data_type = ssh.SSHLoginEvent.DATA_TYPE
    self.assertEqual(event.DATA_TYPE, expected_data_type)

    expected_address = u'192.168.0.1'
    self.assertEqual(expected_address, event.address)

    expected_body = (
        u'Accepted publickey for plaso from 192.168.0.1 port 59229 ssh2: '
        u'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')
    self.assertEqual(expected_body, event.body)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-03-11 19:26:39')
    self.assertEqual(expected_timestamp, event.timestamp)

    expected_fingerprint = (
        u'RSA 00:aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:77:88:99')
    self.assertEqual(expected_fingerprint, event.fingerprint)

    event = storage_writer.events[3]

    expected_data_type = ssh.SSHFailedConnectionEvent.DATA_TYPE
    self.assertEqual(event.DATA_TYPE, expected_data_type)

    expected_address = u'001:db8:a0b:12f0::1'
    self.assertEqual(expected_address, event.address)

    expected_port = u'8759'
    self.assertEqual(expected_port, event.port)

    event = storage_writer.events[4]

    expected_data_type = ssh.SSHOpenedConnectionEvent.DATA_TYPE
    self.assertEqual(event.DATA_TYPE, expected_data_type)

    expected_address = u'188.124.3.41'
    self.assertEqual(expected_address, event.address)

    event = storage_writer.events[7]
    expected_address = u'192.0.2.60'
    self.assertEqual(expected_address, event.address)

    expected_port = u'20042'
    self.assertEqual(expected_port, event.port)

    expected_username = u'fred'
    self.assertEqual(expected_username, event.username)

if __name__ == '__main__':
  unittest.main()
