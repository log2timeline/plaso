#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS local users plist plugin."""

import unittest

from plaso.parsers.plist_plugins import macuser

from tests.parsers.plist_plugins import test_lib


class MacUserPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the MacOS local user plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'user.plist'

    plugin = macuser.MacUserPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

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
        'data_type': 'plist:key',
        'date_time': '2013-12-28 04:35:47',
        'desc': (
            'Last time user (501) changed the password: '
            '$ml$37313$fa6cac1869263baa85cffc5e77a3d4ee164b7'
            '5536cae26ce8547108f60e3f554$a731dbb0e386b169af8'
            '9fbb33c255ceafc083c6bc5194853f72f11c550c42e4625'
            'ef113b66f3f8b51fc3cd39106bad5067db3f7f1491758ff'
            'e0d819a1b0aba20646fd61345d98c0c9a411bfd1144dd4b'
            '3c40ec0f148b66d5b9ab014449f9b2e103928ef21db6e25'
            'b536a60ff17a84e985be3aa7ba3a4c16b34e0d1d2066ae178'),
        'key': 'passwordLastSetTime',
        'root': '/'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
