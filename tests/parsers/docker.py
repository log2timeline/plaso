#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Docker JSON parser."""

import unittest

from plaso.lib import timelib
from plaso.parsers import docker

from tests.parsers import test_lib


class DockerJSONUnitTest(test_lib.ParserTestCase):
  """Tests for the Docker JSON parser."""

  def testParseContainerLog(self):
    """Tests the _ParseContainerLogJSON function."""
    container_id = (
        u'e7d0b7ea5ccf08366e2b0c8afa2318674e8aefe802315378125d2bb83fe3110c')

    parser_object = docker.DockerJSONParser()
    path_segments = [
        u'docker', u'containers', container_id, u'container-json.log']
    storage_writer = self._ParseFile(path_segments, parser_object)

    self.assertEqual(len(storage_writer.events), 10)

    expected_times = [
        u'2016-01-07 16:49:10.000000',
        u'2016-01-07 16:49:10.200000',
        u'2016-01-07 16:49:10.230000',
        u'2016-01-07 16:49:10.237000',
        u'2016-01-07 16:49:10.237200',
        u'2016-01-07 16:49:10.237220',
        u'2016-01-07 16:49:10.237222',
        u'2016-01-07 16:49:10.237222', # losing sub microsec info
        u'2016-01-07 16:49:10.237222',
        u'2016-01-07 16:49:10.237222']

    expected_log = (
        u'\x1b]0;root@e7d0b7ea5ccf: '
        u'/home/plaso\x07root@e7d0b7ea5ccf:/home/plaso# ls\r\n')

    expected_msg = (
        u'Text: '
        u'\x1b]0;root@e7d0b7ea5ccf: /home/plaso\x07root@e7d0b7ea5ccf:'
        u'/home/plaso# ls, Container ID: %s, '
        u'Source: stdout'%container_id)
    expected_msg_short = (
        u'Text: '
        u'\x1b]0;root@e7d0b7ea5ccf: /home/plaso\x07root@e7d0b7ea5ccf:'
        u'/home/plaso# ls, C...'
        )

    for index, event_object in enumerate(storage_writer.events):
      self.assertEqual(event_object.timestamp,
                       timelib.Timestamp.CopyFromString(expected_times[index]))
      self.assertEqual(event_object.container_id, container_id)
      self.assertEqual(event_object.log_line, expected_log)
      self.assertEqual(event_object.log_source, u'stdout')
      self._TestGetMessageStrings(
          event_object, expected_msg, expected_msg_short)

  def testParseContainerConfig(self):
    """Tests the _ParseContainerConfigJSON function."""
    container_id = (
        u'e7d0b7ea5ccf08366e2b0c8afa2318674e8aefe802315378125d2bb83fe3110c')

    parser_object = docker.DockerJSONParser()
    path_segments = [u'docker', u'containers', container_id, u'config.json']
    storage_writer = self._ParseFile(path_segments, parser_object)

    self.assertEqual(len(storage_writer.events), 2)

    event_object = storage_writer.events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-01-07 16:49:08.674873')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.action, u'Container Started')
    self.assertEqual(event_object.container_id, container_id)
    self.assertEqual(event_object.container_name, u'e7d0b7ea5ccf')

    event_object = storage_writer.events[1]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-01-07 16:49:08.507979')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(event_object.action, u'Container Created')
    self.assertEqual(event_object.container_id, container_id)
    self.assertEqual(event_object.container_name, u'e7d0b7ea5ccf')

  def testParseLayerConfig(self):
    """Tests the _ParseLayerConfigJSON function."""

    layer_id = (
        u'3c9a9d7cc6a235eb2de58ca9ef3551c67ae42a991933ba4958d207b29142902b')

    parser_object = docker.DockerJSONParser()
    path_segments = [u'docker', u'graph', layer_id, u'json']
    storage_writer = self._ParseFile(path_segments, parser_object)

    self.assertEqual(len(storage_writer.events), 1)

    event_object = storage_writer.events[0]

    expected_command = (
        u'/bin/sh -c sed -i \'s/^#\\s*\\(deb.*universe\\)$/\\1/g\' '
        u'/etc/apt/sources.list')
    self.assertEqual(event_object.command, expected_command)
    self.assertEqual(event_object.layer_id, layer_id)
    self.assertEqual(event_object.timestamp, 1444670823079273)
    self.assertEqual(event_object.timestamp_desc, u'Creation Time')


if __name__ == '__main__':
  unittest.main()
