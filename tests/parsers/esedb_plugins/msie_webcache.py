#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Microsoft Internet Explorer WebCache database."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import msie_webcache as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.esedb_plugins import msie_webcache

from tests.parsers.esedb_plugins import test_lib


class MsieWebCacheESEDBPluginTest(test_lib.ESEDBPluginTestCase):
  """Tests for the MSIE WebCache ESE database plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = msie_webcache.MsieWebCacheESEDBPlugin()
    storage_writer = self._ParseESEDBFileWithPlugin(
        ['WebCacheV01.dat'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1354)

    # The order in which ESEDBPlugin._GetRecordValues() generates events is
    # nondeterministic hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[567]

    self.CheckTimestamp(event.timestamp, '2014-05-12 07:30:25.486199')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.container_identifier, 1)

    expected_message = (
        'Name: Content '
        'Directory: C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
        'INetCache\\IE\\ '
        'Table: Container_1 '
        'Container identifier: 1 '
        'Set identifier: 0')
    expected_short_message = (
        'Directory: C:\\Users\\test\\AppData\\Local\\Microsoft\\Windows\\'
        'INetCache\\IE\\')

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
