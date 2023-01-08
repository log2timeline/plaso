#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the nsrlsvr analysis plugin."""

import collections
import unittest

from unittest import mock

from dfvfs.path import fake_path_spec

from plaso.analysis import nsrlsvr
from plaso.containers import events
from plaso.containers import reports
from plaso.lib import definitions

from tests.analysis import test_lib


class _MockNsrlsvrSocket(object):
  """Mock socket object for testing."""

  _EXPECTED_DATA = (
      b'QUERY 2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff'
      b'\n')

  def __init__(self):
    """Initializes a mock socket."""
    super(_MockNsrlsvrSocket, self).__init__()
    self._data = None

  # Note: that the following functions do not follow the style guide
  # because they are part of the socket interface.
  # pylint: disable=invalid-name

  # pylint: disable=unused-argument
  def recv(self, buffer_size):
    """Mocks the socket.recv method."""
    expected_data = self._data == self._EXPECTED_DATA
    self._data = None

    if expected_data:
      return b'OK 1'

    return b'OK 0'

  def sendall(self, data):
    """Mocks the socket.sendall method"""
    self._data = data

  def close(self):
    """Mocks the socket.close method"""
    return


class NsrlSvrTest(test_lib.AnalysisPluginTestCase):
  """Tests for the nsrlsvr analysis plugin."""

  _EVENT_1_HASH = (
      '2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff')

  _EVENT_2_HASH = (
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')

  _TEST_EVENTS = [
      {'_parser_chain': 'filestat',
       'data_type': 'fs:stat',
       'path_spec': fake_path_spec.FakePathSpec(
           location='C:\\WINDOWS\\system32\\good.exe'),
       'sha256_hash': _EVENT_1_HASH,
       'timestamp': '2015-01-01 17:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION},
      {'_parser_chain': 'filestat',
       'data_type': 'fs:stat:ntfs',
       'path_spec': fake_path_spec.FakePathSpec(
           location='C:\\WINDOWS\\system32\\evil.exe'),
       'sha256_hash': _EVENT_2_HASH,
       'timestamp': '2016-01-01 17:00:00',
       'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}]

  # pylint: disable=unused-argument
  def _MockCreateConnection(self, connection_information, timeout):
    """Mocks the socket create_connection call

    Args:
      connection_information (object): unused connection information.
      timeout (int): unused timeout

    Returns:
      _MockNsrlsvrSocket: a socket that mocks an open socket to an nsrlsvr
          instance.
    """
    return _MockNsrlsvrSocket()

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._socket_patcher = mock.patch(
        'socket.create_connection', self._MockCreateConnection)
    self._socket_patcher.start()

  def tearDown(self):
    """Cleans up after running an individual test."""
    self._socket_patcher.stop()

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    plugin = nsrlsvr.NsrlsvrAnalysisPlugin()
    plugin.SetHost('localhost')
    plugin.SetPort(9120)
    plugin.SetLabel('nsrl_present')

    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)
    self.assertIsNotNone(analysis_report)

    self.assertEqual(analysis_report.plugin_name, 'nsrlsvr')

    expected_analysis_counter = collections.Counter({
        'nsrl_present': 1})
    self.assertEqual(
        analysis_report.analysis_counter, expected_analysis_counter)

    number_of_event_tags = storage_writer.GetNumberOfAttributeContainers(
        'event_tag')
    self.assertEqual(number_of_event_tags, 1)

    labels = []
    for event_tag in storage_writer.GetAttributeContainers(
        events.EventTag.CONTAINER_TYPE):
      labels.extend(event_tag.labels)
    self.assertEqual(len(labels), 1)

    expected_labels = ['nsrl_present']
    self.assertEqual(labels, expected_labels)


if __name__ == '__main__':
  unittest.main()
