#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS keychain password database file event formatter."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import mac_keychain

from tests.formatters import test_lib


class KeychainApplicationRecordFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the keychain application record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_keychain.KeychainApplicationRecordFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_keychain.KeychainApplicationRecordFormatter()

    expected_attribute_names = [
        'entry_name',
        'account_name']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class KeychainInternetRecordFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the keychain Internet record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_keychain.KeychainInternetRecordFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_keychain.KeychainInternetRecordFormatter()

    expected_attribute_names = [
        'entry_name',
        'account_name',
        'where',
        'protocol',
        'type_protocol']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
