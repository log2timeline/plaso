#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the ssh event formatters."""

import unittest

from plaso.formatters import syslog_ssh

from tests.formatters import test_lib


class SSHLoginEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the ssh login event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = syslog_ssh.SSHLoginEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = syslog_ssh.SSHLoginEventFormatter()

    expected_attribute_names = [
        u'username', u'address', u'port', u'authentication_method', u'pid']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.

class SSHFailedConnectionEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the ssh failed connection event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = syslog_ssh.SSHFailedConnectionEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = syslog_ssh.SSHFailedConnectionEventFormatter()

    expected_attribute_names = [
        u'username', u'address', u'port', u'authentication_method', u'pid']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.

class SSHOpenedConnectionEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the ssh opened connection event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = syslog_ssh.SSHOpenedConnectionEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = syslog_ssh.SSHOpenedConnectionEventFormatter()

    expected_attribute_names = [u'address', u'port', u'pid']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.

if __name__ == '__main__':
  unittest.main()
