#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the atlassian-jira.log parser."""

import unittest

from plaso.parsers.text_plugins import atlassian_jira

from tests.parsers.text_plugins import test_lib


class AtlassianJiraTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Jira application log parser."""

  def testParse(self):
    """Main Test parse for Atlassian Jira."""
    plugin = atlassian_jira.AtlassianJiraTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-jira.log'], plugin)

    num_event_data = storage_writer.GetNumberOfAttributeContainers('event_data')
    self.assertEqual(num_event_data, 5)

    num_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(num_warnings, 0)

    num_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(num_warnings, 0)

    expected_event_values = {
        'body': (
            'Jira starting up. Version : 9.2.0, Mode : EAR, Build Number : '
            '904000, Build Date : 2022-08-25, Build UID : '
            'abc12345-dead-beef-cafe-1234567890ab'),
        'data_type': 'atlassian:jira:line',
        'level': 'INFO',
        'logger_class': 'com.atlassian.jira.startup.JiraStartupLogger',
        'logger_method': 'start',
        'thread': 'main',
        'written_time': '2022-10-03T09:00:01.042'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'body': (
            "Login attempted by user 'admin' from host '192.168.1.10'"),
        'data_type': 'atlassian:jira:line',
        'level': 'INFO',
        'logger_class': 'com.atlassian.jira.web.filters.JiraLoginFilter',
        'logger_method': 'doFilter',
        'thread': 'http-nio-8080-exec-1',
        'written_time': '2022-10-03T09:00:45.317'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'body': (
            "Lock 'CLUSTER_UPGRADE_LOCK' is held by node 'node1'. "
            "Cannot acquire."),
        'data_type': 'atlassian:jira:line',
        'level': 'WARN',
        'logger_class': 'com.atlassian.jira.cluster.ClusterManager',
        'logger_method': 'checkClusterLock',
        'thread': 'Caesium-1-4',
        'written_time': '2022-10-03T09:01:12.884'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 2)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
