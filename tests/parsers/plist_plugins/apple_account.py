#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple account plist plugin."""

import unittest

from plaso.parsers.plist_plugins import apple_account

from tests.parsers.plist_plugins import test_lib


class AppleAccountPlistPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Apple account plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = (
        'com.apple.coreservices.appleidauthenticationinfo.'
        'ABC0ABC1-ABC0-ABC0-ABC0-ABC0ABC1ABC2.plist')

    plugin = apple_account.AppleAccountPlistPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'account_name': 'email@domain.com',
        'data_type': 'macos:apple_account:entry',
        'creation_time': '2013-06-24T20:46:42.000000+00:00',
        'first_name': 'Joaquin',
        'last_connected_time': '2013-12-25T14:00:32.000000+00:00',
        'last_name': 'Moreno Garijo',
        'validation_time': '2013-12-25T14:00:32.000000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
