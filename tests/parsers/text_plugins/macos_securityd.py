#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the MacOS security daemon (securityd) log file text parser plugin."""

import unittest

from plaso.parsers.text_plugins import macos_securityd

from tests.parsers.text_plugins import test_lib


class MacOSSecuritydLogTextPluginTest(test_lib.TextPluginTestCase):
  """Tests the MacOS security daemon (securityd) log file text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = macos_securityd.MacOSSecuritydLogTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['security.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 9)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '0000-02-26T19:11:56+00:00',
        'caller': None,
        'data_type': 'macos:securityd_log:entry',
        'facility': 'user',
        'level': 'Error',
        'message': (
            'securityd_xpc_dictionary_handler EscrowSecurityAl'
            '[3273] DeviceInCircle \xdeetta \xe6tti a\xf0 virka '
            'l\xedka, setja \xedslensku inn.'),
        'security_api': None,
        'sender_pid': 1,
        'sender': 'secd'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    # Check repeated line.
    expected_event_values = {
        'added_time': '0001-12-24T01:21:47+00:00',
        'caller': None,
        'data_type': 'macos:securityd_log:entry',
        'facility': 'user',
        'level': 'Error',
        'message': 'Repeated 3 times: Happy new year!',
        'security_api': None,
        'sender_pid': 456,
        'sender': 'secd'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 8)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
