#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Zeitgeist activity database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import zeitgeist as _  # pylint: disable=unused-import
from plaso.parsers.sqlite_plugins import zeitgeist

from tests.parsers.sqlite_plugins import test_lib


class ZeitgeistActivityDatabasePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Zeitgeist activity database plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = zeitgeist.ZeitgeistActivityDatabasePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['activity.sqlite'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 44)

    events = list(storage_writer.GetEvents())

    # Check the first event.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-10-22 08:53:19.477000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.subject_uri, 'application://rhythmbox.desktop')

    expected_message = 'application://rhythmbox.desktop'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
