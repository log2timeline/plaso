#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the atlassian-confluence.log parser."""

import unittest

from plaso.parsers.text_plugins import atlassian_confluence

from tests.parsers import test_lib


class AtlassianConfluenceTest(test_lib.ParserTestCase):
  """Tests for the Atlassian Confluence application log parser."""

  def testParse(self):
    parser = atlassian_confluence.AtlassianConfluenceTextPlugin()
    storage_writer = self._ParseFile(['atlassian-confluence.log'], parser)

    num_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(num_events, 4)

    num_warnings = storage_writer.GetNumberOfAttributeContainers('extraction_warning')
    self.assertEqual(num_warnings, 0)

    num_warnings = storage_writer.GetNumberOfAttributeContainers('recovery_warning')
    self.assertEqual(num_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values_list = [
        {
            'data_type': 'atlassian:confluence:line',
            'date_time': '2022-07-12 01:08:59.489',
            'level': 'INFO',
            'thread': 'Catalina-utility-1',
            'logger_class': 'confluence.cluster.hazelcast.HazelcastClusterManager',
            'logger_method': 'startCluster',
            'body': 'Starting the cluster.'},
        {
            'data_type': 'atlassian:confluence:line',
            'date_time': '2022-07-12 01:09:02.530',
            'level': 'INFO',
            'thread': 'hz.confluence.event-3',
            'logger_class': 'confluence.cluster.hazelcast.LoggingClusterMembershipListener',
            'logger_method': 'memberAdded',
            'body': '[10.0.0.123]:5801 joined the cluster'},
        {
            'data_type': 'atlassian:confluence:line',
            'date_time': '2022-07-12 01:11:24.636',
            'level': 'INFO',
            'thread': 'ThreadPoolAsyncTaskExecutor::Thread 15',
            'logger_class': 'plugins.synchrony.bootstrap.DefaultSynchronyProxyMonitor',
            'logger_method': '<init>',
            'body': 'synchrony-proxy healthcheck url: http://127.0.0.1:8090/synchrony-proxy/healthcheck'},
        {
            'data_type': 'atlassian:confluence:line',
            'date_time': '2022-07-12 01:38:50.696',
            'level': 'WARN',
            'thread': 'support-zip',
            'logger_class': 'troubleshooting.healthcheck.concurrent.SupportHealthCheckProcess',
            'logger_method': 'lambda$getCompletedStatuses$0',
            'body': '''Health check 'License Expiry' failed with severity 'warning': 'Your subscription will expire in less than 30 days, on 26 Jul 2022. When your subscription expires, your site will become read-only.'
 -- event: com.atlassian.troubleshooting.confluence.zip.CreateSupportZipEvent[source=null] | originatingMemberUuid: ab12cd34-ef56-ab12-cd34-ef56ab12cd34'''}]

    for event, expected_event_values in zip(events, expected_event_values_list):
      self.CheckEventValues(storage_writer, event, expected_event_values)


if __name__ == '__main__':
  unittest.main()
