#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Atlassian Bitbucket application log parser."""

import unittest

from plaso.parsers.text_plugins import atlassian_bitbucket

from tests.parsers.text_plugins import test_lib


class AtlassianBitbucketTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Bitbucket application log text parser plugin."""

  def testParse(self):
    """Tests the Process function."""
    plugin = atlassian_bitbucket.AtlassianBitbucketTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-bitbucket.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': (
            'Starting Bitbucket 7.4.0 (204e35a built on Tue Jul 07 14:31:59 '
            'NZST 2020)'),
        'data_type': 'atlassian:bitbucket:line',
        'level': 'INFO',
        'logger_class': 'com.atlassian.bitbucket.internal.boot.log.BuildInfoLogger',
        'thread': 'main',
        'written_time': '2020-09-08T07:53:45.084'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'body': (
            'Caught exception while rendering markup: could not connect to '
            'server'),
        'data_type': 'atlassian:bitbucket:line',
        'level': 'WARN',
        'logger_class': 'c.a.b.m.r.impl.MarkupRendererImpl',
        'thread': 'threadpool:thread-5',
        'written_time': '2020-07-21T14:24:40.658'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
