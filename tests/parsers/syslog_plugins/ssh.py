#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SSH syslog plugin."""
import unittest

from plaso.lib import timelib
from plaso.parsers import syslog
from plaso.parsers.syslog_plugins import ssh

from tests.parsers.syslog_plugins import test_lib


class SSHSyslogParserTest(test_lib.SyslogPluginTestCase):
  """Tests for the SSH syslog plugin."""

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath([u'syslog_ssh.log'])
    event_queue_consumer = self._ParseFileWithPlugin(u'ssh', test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    event = event_objects[0]

    expected_data_type = syslog.SyslogLineEvent.DATA_TYPE
    self.assertEqual(event.DATA_TYPE, expected_data_type)

    event = event_objects[1]

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

    event = event_objects[3]

    expected_data_type = ssh.SSHFailedConnectionEvent.DATA_TYPE
    self.assertEqual(event.DATA_TYPE, expected_data_type)

    expected_address = u'001:db8:a0b:12f0::1'
    self.assertEqual(expected_address, event.address)

    expected_port = u'8759'
    self.assertEqual(expected_port, event.port)

    event = event_objects[4]

    expected_data_type = ssh.SSHOpenedConnectionEvent.DATA_TYPE
    self.assertEqual(event.DATA_TYPE, expected_data_type)

    expected_address = u'188.124.3.41'
    self.assertEqual(expected_address, event.address)

    self.assertEqual(len(event_objects), 9)


if __name__ == '__main__':
  unittest.main()
