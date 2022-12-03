#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the JSON-L parser plugin for Docker container log files."""

import unittest

from plaso.parsers.jsonl_plugins import docker_container_log

from tests.parsers.jsonl_plugins import test_lib


class DockerContainerLogJSONLPluginTest(test_lib.JSONLPluginTestCase):
  """Tests for the JSON-L parser plugin for Docker container log files."""

  def testProcess(self):
    """Tests the Process function."""
    container_identifier = (
        'e7d0b7ea5ccf08366e2b0c8afa2318674e8aefe802315378125d2bb83fe3110c')
    path_segments = [
        'docker', 'containers', container_identifier, 'container-json.log']

    plugin = docker_container_log.DockerContainerLogJSONLPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin(path_segments, plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'container_identifier': container_identifier,
        'data_type': 'docker:container:log:entry',
        'log_line': (
            '\x1b]0;root@e7d0b7ea5ccf: '
            '/home/plaso\x07root@e7d0b7ea5ccf:/home/plaso# ls\r\n'),
        'log_source': 'stdout',
        'written_time': '2016-01-07T16:49:10.000000+00:00'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
