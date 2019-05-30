#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome autofill entries database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import chrome_autofill as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import chrome_autofill

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class ChromeAutofillPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome autofill entries database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['Web Data'])
  def testProcess(self):
    """Tests the Process function on a Chrome autofill entries database."""
    plugin = chrome_autofill.ChromeAutofillPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['Web Data'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2018-08-17 19:35:51.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    self.assertEqual(event.field_name, 'repo')
    self.assertEqual(event.value, 'log2timeline/plaso')
    self.assertEqual(event.usage_count, 1)

    expected_message = (
        'Form field name: repo '
        'Entered value: log2timeline/plaso '
        'Times used: 1')
    expected_short_message = (
        'repo: log2timeline/plaso (1)')

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
