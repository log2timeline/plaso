#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Docker JSON parser."""

import unittest

from plaso.lib import definitions
from plaso.parsers import docker

from tests.parsers import test_lib


class DockerJSONUnitTest(test_lib.ParserTestCase):
  """Tests for the Docker JSON parser."""

  def testParseLayerConfig(self):
    """Tests the _ParseLayerConfigJSON function."""
    layer_identifier = (
        '3c9a9d7cc6a235eb2de58ca9ef3551c67ae42a991933ba4958d207b29142902b')

    parser = docker.DockerJSONParser()
    path_segments = ['docker', 'graph', layer_identifier, 'json']
    storage_writer = self._ParseFile(path_segments, parser)

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
        'data_type': 'docker:json:layer',
        'date_time': '2015-10-12 17:27:03.079273',
        'layer_id': layer_identifier,
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
