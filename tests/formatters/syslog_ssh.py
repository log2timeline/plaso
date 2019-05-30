#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SSH event formatters."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import ssh

from tests.formatters import test_lib


class SSHLoginEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the SSH login event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ssh.SSHLoginEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ssh.SSHLoginEventFormatter()

    expected_attribute_names = [
        'username', 'address', 'port', 'authentication_method', 'pid']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class SSHFailedConnectionEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the SSH failed connection event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ssh.SSHFailedConnectionEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ssh.SSHFailedConnectionEventFormatter()

    expected_attribute_names = [
        'username', 'address', 'port', 'authentication_method', 'pid']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


class SSHOpenedConnectionEventFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the SSH opened connection event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = ssh.SSHOpenedConnectionEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = ssh.SSHOpenedConnectionEventFormatter()

    expected_attribute_names = ['address', 'port', 'pid']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.
  # TODO: add test for GetSources.


if __name__ == '__main__':
  unittest.main()
