#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome autofill entries database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import chrome_autofill

from tests.parsers.sqlite_plugins import test_lib


class ChromeAutofillPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome autofill entries database plugin."""

  def testProcess(self):
    """Tests the Process function on a Chrome autofill entries database."""
    plugin = chrome_autofill.ChromeAutofillPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['Web Data'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 3)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'creation_time': '2018-08-17T19:35:51+00:00',
        'data_type': 'chrome:autofill:entry',
        'field_name': 'repo',
        'last_used_time': '2018-08-17T19:35:51+00:00',
        'usage_count': 1,
        'value': 'log2timeline/plaso'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
