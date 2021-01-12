#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Zeitgeist activity database plugin."""

import unittest

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

    expected_event_values = {
        'data_type': 'zeitgeist:activity',
        'subject_uri': 'application://rhythmbox.desktop',
        'timestamp': '2013-10-22 08:53:19.477000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
