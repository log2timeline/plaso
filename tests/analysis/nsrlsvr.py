#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the nsrlsvr analysis plugin."""

from __future__ import unicode_literals

import unittest

try:
  import mock  # pylint: disable=import-error
except ImportError:
  from unittest import mock

from dfvfs.path import fake_path_spec

from plaso.analysis import nsrlsvr
from plaso.lib import definitions
from plaso.lib import timelib

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
      {'data_type': 'fs:stat',
       'pathspec': fake_path_spec.FakePathSpec(
           location='C:\\WINDOWS\\system32\\good.exe'),
       'sha256_hash': _EVENT_1_HASH,
       'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:00'),
       'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION},
      {'data_type': 'fs:stat:ntfs',
       'sha256_hash': _EVENT_2_HASH,
       'pathspec': fake_path_spec.FakePathSpec(
           location='C:\\WINDOWS\\system32\\evil.exe'),
       'timestamp': timelib.Timestamp.CopyFromString('2016-01-01 17:00:00'),
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

    self.assertEqual(len(storage_writer.analysis_reports), 1)
    self.assertEqual(storage_writer.number_of_event_tags, 1)

    report = storage_writer.analysis_reports[0]
    self.assertIsNotNone(report)

    expected_text = (
        'nsrlsvr hash tagging results\n'
        '1 path specifications tagged with label: nsrl_present\n')
    self.assertEqual(report.text, expected_text)

    labels = []
    for event_tag in storage_writer.GetEventTags():
      labels.extend(event_tag.labels)
    self.assertEqual(len(labels), 1)

    expected_labels = ['nsrl_present']
    self.assertEqual(labels, expected_labels)


if __name__ == '__main__':
  unittest.main()
