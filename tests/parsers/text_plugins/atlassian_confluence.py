#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

    expected_event_values_list = [
        {
            'data_type': 'atlassian:confluence:line',
            'written_time': '2022-07-12T01:08:59.489',
            'level': 'INFO',
            'thread': 'Catalina-utility-1',
            'logger_class': (
                'confluence.cluster.hazelcast.HazelcastClusterManager'
                ),
            'logger_method': 'startCluster',
            'body': 'Starting the cluster.'},
        {
            'data_type': 'atlassian:confluence:line',
            'written_time': '2022-07-12T01:09:02.530',
            'level': 'INFO',
            'thread': 'hz.confluence.event-3',
            'logger_class': (
                'confluence.cluster.hazelcast.LoggingClusterMembershipListener'
                ),
            'logger_method': 'memberAdded',
            'body': '[10.0.0.123]:5801 joined the cluster'},
        {
            'data_type': 'atlassian:confluence:line',
            'written_time': '2022-07-12T01:11:24.636',
            'level': 'INFO',
            'thread': 'ThreadPoolAsyncTaskExecutor::Thread 15',
            'logger_class': (
                'plugins.synchrony.bootstrap.DefaultSynchronyProxyMonitor'
                ),
            'logger_method': '<init>',
            'body': (
                'synchrony-proxy healthcheck url: '
                'http://127.0.0.1:8090/synchrony-proxy/healthcheck'
                ),
            },
        {
            'data_type': 'atlassian:confluence:line',
            'written_time': '2022-07-12T01:38:50.696',
            'level': 'WARN',
            'thread': 'support-zip',
            'logger_class': (
                'troubleshooting.healthcheck.concurrent'
                '.SupportHealthCheckProcess'
                ),
            'logger_method': 'lambda$getCompletedStatuses$0',
            'body': (
                '''Health check 'License Expiry' failed with severity '''\
                ''''warning': 'Your subscription will expire in less than '''\
                '''30 days, on 26 Jul 2022. When your subscription expires, '''\
                '''your site will become read-only.' -- event: '''\
                '''com.atlassian.troubleshooting.confluence.zip'''\
                '''.CreateSupportZipEvent[source=null] | '''\
                '''originatingMemberUuid: '''\
                '''ab12cd34-ef56-ab12-cd34-ef56ab12cd34'''\
                )}]

    for index, expected_event_values in enumerate(expected_event_values_list):
      event_data = storage_writer.GetAttributeContainerByIndex(
          'event_data', index)
      self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
