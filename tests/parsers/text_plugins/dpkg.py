#!/usr/bin/env python3
# -*_ coding: utf-8 -*-
"""Tests for the dpkg.log text parser plugin."""

import unittest

from plaso.parsers.text_plugins import dpkg

from tests.parsers.text_plugins import test_lib


class DpkgTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the dpkg log text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = dpkg.DpkgTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['dpkg.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'added_time': '2009-02-25T11:45:23',
        'body': 'conffile /etc/X11/Xsession keep',
        'data_type': 'linux:dpkg_log:entry'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
