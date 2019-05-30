#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Docker JSON parser."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import docker

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class DockerJSONUnitTest(test_lib.ParserTestCase):
  """Tests for the Docker JSON parser."""

  @shared_test_lib.skipUnlessHasTestFile([
      'docker', 'containers',
      'e7d0b7ea5ccf08366e2b0c8afa2318674e8aefe802315378125d2bb83fe3110c',
      'container-json.log'])
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

    expected_times = [
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

    expected_log = (
        '\x1b]0;root@e7d0b7ea5ccf: '
        '/home/plaso\x07root@e7d0b7ea5ccf:/home/plaso# ls\r\n')

    expected_message = (
        'Text: '
        '\x1b]0;root@e7d0b7ea5ccf: /home/plaso\x07root@e7d0b7ea5ccf:'
        '/home/plaso# ls, Container ID: {0:s}, '
        'Source: stdout').format(container_identifier)
    expected_short_message = (
        'Text: '
        '\x1b]0;root@e7d0b7ea5ccf: /home/plaso\x07root@e7d0b7ea5ccf:'
        '/home/plaso# ls, C...'
        )

    for index, event in enumerate(events):
      self.CheckTimestamp(event.timestamp, expected_times[index])

      self.assertEqual(event.container_id, container_identifier)
      self.assertEqual(event.log_line, expected_log)
      self.assertEqual(event.log_source, 'stdout')
      self._TestGetMessageStrings(
          event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([
      'docker', 'containers',
      'e7d0b7ea5ccf08366e2b0c8afa2318674e8aefe802315378125d2bb83fe3110c',
      'container-json.log'])
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

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2016-01-07 16:49:08.674873')

    self.assertEqual(event.action, 'Container Started')
    self.assertEqual(event.container_id, container_identifier)
    self.assertEqual(event.container_name, 'e7d0b7ea5ccf')

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2016-01-07 16:49:08.507979')

    self.assertEqual(event.action, 'Container Created')
    self.assertEqual(event.container_id, container_identifier)
    self.assertEqual(event.container_name, 'e7d0b7ea5ccf')

  @shared_test_lib.skipUnlessHasTestFile([
      'docker', 'graph',
      '3c9a9d7cc6a235eb2de58ca9ef3551c67ae42a991933ba4958d207b29142902b',
      'json'])
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

    event = events[0]

    expected_command = (
        '/bin/sh -c sed -i \'s/^#\\s*\\(deb.*universe\\)$/\\1/g\' '
        '/etc/apt/sources.list')
    self.assertEqual(event.command, expected_command)
    self.assertEqual(event.layer_id, layer_identifier)
    self.assertEqual(event.timestamp, 1444670823079273)
    self.assertEqual(event.timestamp_desc, 'Creation Time')


if __name__ == '__main__':
  unittest.main()
