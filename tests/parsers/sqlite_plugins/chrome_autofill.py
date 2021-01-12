#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome autofill entries database plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import chrome_autofill

from tests.parsers.sqlite_plugins import test_lib


class ChromeAutofillPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome autofill entries database plugin."""

  def testProcess(self):
    """Tests the Process function on a Chrome autofill entries database."""
    plugin = chrome_autofill.ChromeAutofillPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['Web Data'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'chrome:autofill:entry',
        'field_name': 'repo',
        'timestamp': '2018-08-17 19:35:51.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
        'usage_count': 1,
        'value': 'log2timeline/plaso'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)


if __name__ == '__main__':
  unittest.main()
