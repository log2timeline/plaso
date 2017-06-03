#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the nsrlsvr analysis plugin."""
import unittest

import mock
from dfvfs.path import fake_path_spec

from plaso.analysis import nsrlsvr
from plaso.lib import definitions
from plaso.lib import timelib

from tests.analysis import test_lib


class _MockNsrlsvrSocket(object):
  """Mock socket object for testing."""

  def __init__(self):
    """Initializes a mock socket."""
    super(_MockNsrlsvrSocket, self).__init__()
    self._data = None

  # These methods are part of the socket interface, hence their names do not
  # follow the Plaso style guide.
  def recv(self, unused_buffer_size):
    """Mocks the socket.recv method."""
    if self._data == u'QUERY {0:s}\n'.format(NsrlSvrTest.EVENT_1_HASH):
      self._data = None
      return u'OK 1'
    else:
      self._data = None
      return u'OK 0'

  def sendall(self, data):
    """Mocks the socket.sendall method"""
    self._data = data

  def close(self):
    """Mocks the socket.close method"""
    pass


class NsrlSvrTest(test_lib.AnalysisPluginTestCase):
  """Tests for the nsrlsvr analysis plugin."""
  EVENT_1_HASH = (
      u'2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff')

  _EVENT_2_HASH = (
      u'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')

  _TEST_EVENTS = [
      {u'timestamp': timelib.Timestamp.CopyFromString(u'2015-01-01 17:00:00'),
       u'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
       u'sha256_hash': EVENT_1_HASH,
       u'data_type': u'fs:stat',
       u'pathspec': fake_path_spec.FakePathSpec(
           location=u'C:\\WINDOWS\\system32\\good.exe')
      },
      {u'timestamp': timelib.Timestamp.CopyFromString(u'2016-01-01 17:00:00'),
       u'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION,
       u'sha256_hash': _EVENT_2_HASH,
       u'data_type': u'fs:stat:ntfs',
       u'pathspec': fake_path_spec.FakePathSpec(
           location=u'C:\\WINDOWS\\system32\\evil.exe')}]

  def _MockCreateConnection(
      self, unused_connection_information, unused_timeout):
    """Mocks the socket create_connection call

    Returns:
      _MockNsrlsvrSocket: a socket that mocks an open socket to an nsrlsvr
          instance.
    """
    return _MockNsrlsvrSocket()

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._socket_patcher = mock.patch(
        u'socket.create_connection', self._MockCreateConnection)
    self._socket_patcher.start()

  def tearDown(self):
    """Cleans up after running an individual test."""
    self._socket_patcher.stop()

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    events = []
    for event_dictionary in self._TEST_EVENTS:
      event = self._CreateTestEventObject(event_dictionary)
      events.append(event)

    plugin = nsrlsvr.NsrlsvrAnalysisPlugin()
    plugin.SetHost(u'localhost')
    plugin.SetPort(9120)
    plugin.SetLabel(u'nsrl_present')

    storage_writer = self._AnalyzeEvents(events, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)
    self.assertEqual(len(storage_writer.event_tags), 1)

    report = storage_writer.analysis_reports[0]
    self.assertIsNotNone(report)

    expected_text = (
        u'nsrlsvr hash tagging results\n'
        u'1 path specifications tagged with label: nsrl_present\n')
    self.assertEqual(report.text, expected_text)

    labels = []
    for event_tag in storage_writer.event_tags:
      labels.extend(event_tag.labels)
    self.assertEqual(len(labels), 1)

    expected_labels = [u'nsrl_present']
    self.assertEqual(labels, expected_labels)


if __name__ == '__main__':
  unittest.main()
