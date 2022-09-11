#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Apple account plist plugin."""

import unittest

from plaso.lib import definitions
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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    expected_event_values = {
        'account_name': 'email@domain.com',
        'data_type': 'macos:apple_account:entry',
        'date_time': '2013-06-24 20:46:42',
        'first_name': 'Joaquin',
        'last_name': 'Moreno Garijo',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'account_name': 'email@domain.com',
        'data_type': 'macos:apple_account:entry',
        'date_time': '2013-12-25 14:00:32',
        'first_name': 'Joaquin',
        'last_name': 'Moreno Garijo',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CONNECTION_ESTABLISHED}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'account_name': 'email@domain.com',
        'data_type': 'macos:apple_account:entry',
        'date_time': '2013-12-25 14:00:32',
        'first_name': 'Joaquin',
        'last_name': 'Moreno Garijo',
        'timestamp_desc': definitions.TIME_DESCRIPTION_VALIDATION}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)


if __name__ == '__main__':
  unittest.main()
