#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the M365 Activity log table plugin."""

import unittest

from plaso.parsers.csv_plugins import m365_activitylog

from tests.parsers.csv_plugins import test_lib

class M365ActivityLogTest(test_lib.CSVPluginTestCase):
  """Tests for the M365 Activity log table plugin."""

  # pylint: disable=protected-access

  def testParseFileObject(self):
    """Tests the ParseFileObject function."""
    plugin = m365_activitylog.M365ActivityLogPlugin()
    storage_writer = self._ParseCSVFileWithPlugin(
        ['m365_activity_log.csv'],
        plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 15)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'application': 'Microsoft OneDrive for Business',
        'userprincipalname': 'test-user@test-company.tld',
        'data_type': 'm365:activitylog:event',
        'ipaddress': '82.181.16.164'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)

if __name__ == '__main__':
  unittest.main()
