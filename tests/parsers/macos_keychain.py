#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Keychain password database parser."""

import unittest

from plaso.parsers import macos_keychain

from tests.parsers import test_lib


class MacKeychainParserTest(test_lib.ParserTestCase):
  """Tests for keychain file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = macos_keychain.KeychainParser()
    storage_writer = self._ParseFile(['login.keychain'], parser)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Test keychain application event data.
    expected_ssgp = (
        'b8e44863af1cb0785b89681d22e2721997ccfb8adb8853e726aff94c8830b05a')

    expected_event_values = {
        'account_name': 'moxilo',
        'data_type': 'macos:keychain:application',
        'creation_time': '2014-01-26T14:51:48+00:00',
        'entry_name': 'Secret Application',
        'modification_time': '2014-01-26T14:52:29+00:00',
        'ssgp_hash': expected_ssgp}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Test keychain internet event data.
    expected_ssgp = (
        '83ccacf55a8cb656d340ec405e9d8b308fac54bb79c5c9b0219bd0d700c3c521')

    expected_event_values = {
        'account_name': 'MrMoreno',
        'data_type': 'macos:keychain:internet',
        'creation_time': '2014-01-26T14:54:33+00:00',
        'entry_name': 'plaso.kiddaland.net',
        'modification_time': '2014-01-26T14:54:33+00:00',
        'protocol': 'http',
        'ssgp_hash': expected_ssgp,
        'type_protocol': 'dflt',
        'where': 'plaso.kiddaland.net'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
