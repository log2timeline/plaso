#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File (OLECF) default plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import olecf  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.olecf_plugins import default

from tests.parsers.olecf_plugins import test_lib


class TestDefaultPluginOLECF(test_lib.OLECFPluginTestCase):
  """Tests for the OLECF default plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = default.DefaultOLECFPlugin()
    storage_writer = self._ParseOLECFFileWithPlugin(['Document.doc'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 5)

    events = list(storage_writer.GetEvents())

    # Check the Root Entry event.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-05-16 02:29:49.795000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.name, 'Root Entry')

    expected_string = (
        'Name: Root Entry')

    self._TestGetMessageStrings(
        event_data, expected_string, expected_string)

    # Check one other entry.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-05-16 02:29:49.704000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_string = 'Name: MsoDataStore'
    self._TestGetMessageStrings(
        event_data, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
