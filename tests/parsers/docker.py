#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Docker JSON parser."""

import unittest

from plaso.lib import definitions
from plaso.parsers import docker

from tests.parsers import test_lib


class DockerJSONUnitTest(test_lib.ParserTestCase):
  """Tests for the Docker JSON parser."""

  def testParseContainerLog(self):
    """Tests the _ParseContainerLogJSON function."""
    container_identifier = (
        'e7d0b7ea5ccf08366e2b0c8afa2318674e8aefe802315378125d2bb83fe3110c')

    parser = docker.DockerJSONParser()
    path_segments = [
        'docker', 'containers', container_identifier, 'container-json.log']
    storage_writer = self._ParseFile(path_segments, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 10)

    events = list(storage_writer.GetEvents())

    expected_timestamps = [
        '2016-01-07 16:49:10.000000',
        '2016-01-07 16:49:10.200000',
        '2016-01-07 16:49:10.230000',
        '2016-01-07 16:49:10.237000',
        '2016-01-07 16:49:10.237200',
        '2016-01-07 16:49:10.237220',
        '2016-01-07 16:49:10.237222',
        '2016-01-07 16:49:10.237222', # losing sub microsec info
        '2016-01-07 16:49:10.237222',
        '2016-01-07 16:49:10.237222']

    expected_event_values = {
        'container_id': container_identifier,
        'data_type': 'docker:json:container:log',
        'log_line': (
            '\x1b]0;root@e7d0b7ea5ccf: '
            '/home/plaso\x07root@e7d0b7ea5ccf:/home/plaso# ls\r\n'),
        'log_source': 'stdout'}

    for index, event in enumerate(events):
      self.CheckTimestamp(event.timestamp, expected_timestamps[index])
      self.CheckEventValues(storage_writer, event, expected_event_values)

  def testParseContainerConfig(self):
    """Tests the _ParseContainerConfigJSON function."""
    container_identifier = (
        'e7d0b7ea5ccf08366e2b0c8afa2318674e8aefe802315378125d2bb83fe3110c')

    parser = docker.DockerJSONParser()
    path_segments = [
        'docker', 'containers', container_identifier, 'config.json']
    storage_writer = self._ParseFile(path_segments, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'action': 'Container Started',
        'container_id': container_identifier,
        'container_name': 'e7d0b7ea5ccf',
        'data_type': 'docker:json:container',
        'timestamp': '2016-01-07 16:49:08.674873'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'action': 'Container Created',
        'container_id': container_identifier,
        'container_name': 'e7d0b7ea5ccf',
        'data_type': 'docker:json:container',
        'timestamp': '2016-01-07 16:49:08.507979'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

  def testParseLayerConfig(self):
    """Tests the _ParseLayerConfigJSON function."""
    layer_identifier = (
        '3c9a9d7cc6a235eb2de58ca9ef3551c67ae42a991933ba4958d207b29142902b')

    parser = docker.DockerJSONParser()
    path_segments = ['docker', 'graph', layer_identifier, 'json']
    storage_writer = self._ParseFile(path_segments, parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'command': (
            '/bin/sh -c sed -i \'s/^#\\s*\\(deb.*universe\\)$/\\1/g\' '
            '/etc/apt/sources.list'),
        'data_type': 'docker:json:layer',
        'layer_id': layer_identifier,
        'timestamp': '2015-10-12 17:27:03.079273',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)


if __name__ == '__main__':
  unittest.main()
