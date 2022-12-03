#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the JSON-L parser plugin for Docker layer config files."""

import unittest

from plaso.parsers.jsonl_plugins import docker_layer_config

from tests.parsers.jsonl_plugins import test_lib


class DockerLayerLogJSONLPluginTest(test_lib.JSONLPluginTestCase):
  """Tests for the JSON-L parser plugin for Docker layer config files."""

  def testProcess(self):
    """Tests the Process function."""
    layer_identifier = (
        '3c9a9d7cc6a235eb2de58ca9ef3551c67ae42a991933ba4958d207b29142902b')
    path_segments = ['docker', 'graph', layer_identifier, 'json']

    plugin = docker_layer_config.DockerLayerConfigurationJSONLPlugin()
    storage_writer = self._ParseJSONLFileWithPlugin(path_segments, plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'command': (
            '/bin/sh -c sed -i \'s/^#\\s*\\(deb.*universe\\)$/\\1/g\' '
            '/etc/apt/sources.list'),
        'creation_time': '2015-10-12T17:27:03.079273+00:00',
        'data_type': 'docker:layer:configuration',
        'layer_identifier': layer_identifier}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
