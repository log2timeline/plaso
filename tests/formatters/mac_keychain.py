#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X keychain password database file event formatter."""

import unittest

from plaso.formatters import mac_keychain

from tests.formatters import test_lib


class KeychainApplicationRecordFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the keychain application record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_keychain.KeychainApplicationRecordFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_keychain.KeychainApplicationRecordFormatter()

    expected_attribute_names = [
        u'entry_name',
        u'account_name']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


class KeychainInternetRecordFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the keychain Internet record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mac_keychain.KeychainInternetRecordFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mac_keychain.KeychainInternetRecordFormatter()

    expected_attribute_names = [
        u'entry_name',
        u'account_name',
        u'where',
        u'protocol',
        u'type_protocol']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
