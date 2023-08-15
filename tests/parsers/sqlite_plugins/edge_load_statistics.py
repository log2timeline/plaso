# -*- coding: utf-8 -*-
"""Tests for Microsoft Edge load statistics plugin."""

import unittest

from plaso.parsers.sqlite_plugins import edge_load_statistics
from tests.parsers.sqlite_plugins import test_lib


class EdgeLoadStatisticsTest(test_lib.SQLitePluginTestCase):
  """Tests for edge load statistics database plugin."""

  def testProcess(self):
    """Test the Process function on a Edge Load Statistics file."""
    plugin_object = edge_load_statistics.EdgeLoadStatisticsPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['load_statistics.db'], plugin_object)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data , 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'edge:resources:load_statistics',
        'last_update': '2023-03-13T01:50:33.620419+00:00',
        'resource_hostname': 'sb.scorecardresearch.com',
        'resource_type': 4,
        'top_level_hostname': 'ntp.msn.com'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
