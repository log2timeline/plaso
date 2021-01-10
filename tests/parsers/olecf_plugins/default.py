#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound File (OLECF) default plugin."""

import unittest

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
    expected_event_values = {
        'data_type': 'olecf:item',
        'name': 'Root Entry',
        'timestamp': '2013-05-16 02:29:49.795000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_MODIFICATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Check one other entry.
    expected_event_values = {
        'data_type': 'olecf:item',
        'name': 'MsoDataStore',
        'timestamp': '2013-05-16 02:29:49.704000'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
