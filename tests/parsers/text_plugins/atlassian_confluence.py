#!/usr/bin/env python3
"""Tests for the atlassian-confluence.log parser."""

import unittest

from plaso.parsers.text_plugins import atlassian_confluence

from tests.parsers.text_plugins import test_lib


class AtlassianConfluenceTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Confluence application log parser."""

  def testParse(self):
    """Main Test parse for Atlassian Confluence."""
    plugin = atlassian_confluence.AtlassianConfluenceTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-confluence.log'], plugin)

    num_event_data = storage_writer.GetNumberOfAttributeContainers('event_data')
    self.assertEqual(num_event_data, 4)

    num_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(num_warnings, 0)

    num_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(num_warnings, 0)

    expected_event_values = {
        'body': 'Starting the cluster.',
        'data_type': 'atlassian:confluence:line',
        'level': 'INFO',
        'logger_class': 'confluence.cluster.hazelcast.HazelcastClusterManager',
        'logger_method': 'startCluster',
        'thread': 'Catalina-utility-1',
        'written_time': '2022-07-12T01:08:59.489'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
