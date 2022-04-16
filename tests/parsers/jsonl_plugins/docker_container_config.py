#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the JSON-L parser plugin for Docker container config files."""

import unittest

from plaso.parsers.jsonl_plugins import docker_container_config

from tests.parsers.jsonl_plugins import test_lib


class DockerContainerLogJSONLPluginTest(test_lib.JSONLPluginTestCase):
  """Tests for the JSON-L parser plugin for Docker container config files."""

  def testProcess(self):
    """Tests the Process function."""
    container_identifier = (
        'e7d0b7ea5ccf08366e2b0c8afa2318674e8aefe802315378125d2bb83fe3110c')
    path_segments = [
        'docker', 'containers', container_identifier, 'config.json']

    plugin = docker_container_config.DockerContainerConfigurationJSONLPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin(path_segments, plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 2)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'action': 'Container Started',
        'container_identifier': container_identifier,
        'container_name': 'e7d0b7ea5ccf',
        'data_type': 'docker:container:configuration',
        'date_time': '2016-01-07 16:49:08.674873'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'action': 'Container Created',
        'container_identifier': container_identifier,
        'container_name': 'e7d0b7ea5ccf',
        'data_type': 'docker:container:configuration',
        'date_time': '2016-01-07 16:49:08.507979'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
