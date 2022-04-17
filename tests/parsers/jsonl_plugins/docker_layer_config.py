#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the JSON-L parser plugin for Docker layer config files."""

import unittest

from plaso.lib import definitions
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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'command': (
            '/bin/sh -c sed -i \'s/^#\\s*\\(deb.*universe\\)$/\\1/g\' '
            '/etc/apt/sources.list'),
        'date_time': '2015-10-12 17:27:03.079273',
        'data_type': 'docker:layer:configuration',
        'layer_identifier': layer_identifier,
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
