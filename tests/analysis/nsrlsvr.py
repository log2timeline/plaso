#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the nsrlsvr analysis plugin."""
import unittest

import mock
from dfvfs.path import fake_path_spec

from plaso.analysis import nsrlsvr
from plaso.containers import events
from plaso.engine import plaso_queue
from plaso.engine import single_process
from plaso.lib import eventdata
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
  EVENT_2_HASH = (
      u'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
  TEST_EVENTS = [
      {u'timestamp': timelib.Timestamp.CopyFromString(u'2015-01-01 17:00:00'),
       u'sha256_hash': EVENT_1_HASH, u'uuid': u'8', u'data_type': u'fs:stat',
       u'pathspec': fake_path_spec.FakePathSpec(
           location=u'C:\\WINDOWS\\system32\\good.exe')
      },
      {u'timestamp': timelib.Timestamp.CopyFromString(u'2016-01-01 17:00:00'),
       u'sha256_hash': EVENT_2_HASH, u'uuid': u'9',
       u'data_type': u'fs:stat:ntfs', u'pathspec': fake_path_spec.FakePathSpec(
           location=u'C:\\WINDOWS\\system32\\evil.exe')}]

  def _CreateTestEventObject(self, event_dictionary):
    """Create a test event with a set of attributes.

    Args:
      event_dictionary (dict[str, str]: contains attributes of an event to add
          to the queue.

    Returns:
      An event object (instance of EventObject) that contains the necessary
      attributes for testing.
    """
    event = events.EventObject()
    event.timestamp = event_dictionary[u'timestamp']
    event.timestamp_description = eventdata.EventTimestamp.CREATION_TIME
    event.data_type = event_dictionary[u'data_type']
    event.pathspec = event_dictionary[u'pathspec']
    event.sha256_hash = event_dictionary[u'sha256_hash']
    event.uuid = event_dictionary[u'uuid']
    return event

  def _MockCreateConnection(
      self, unused_connection_information, unused_timeout):
    """Mocks the socket create_connection call"""
    return _MockNsrlsvrSocket()

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.socket_patcher = mock.patch(
        'socket.create_connection', self._MockCreateConnection)
    self.socket_patcher.start()

  def tearDown(self):
    """Cleans up after running an individual test."""
    self.socket_patcher.stop()

  def testNsrlsvrLookup(self):
    """Tests for the nsrlsvr analysis plugin."""
    event_queue = single_process.SingleProcessQueue()
    knowledge_base = self._SetUpKnowledgeBase()

    # Fill the incoming queue with events.
    test_queue_producer = plaso_queue.ItemQueueProducer(event_queue)
    event_objects = [self._CreateTestEventObject(test_event) for test_event in
                     self.TEST_EVENTS]
    test_queue_producer.ProduceItems(event_objects)

    # Set up the plugin.
    analysis_plugin = nsrlsvr.NsrlsvrAnalysisPlugin(event_queue)
    analysis_plugin.SetHost(u'127.0.0.1')
    analysis_plugin.SetPort(9120)

    # Run the analysis plugin.
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEqual(len(analysis_reports), 1)
    report = analysis_reports[0]
    tags = report.GetTags()
    self.assertEqual(len(tags), 2)
    tag = tags[0]
    self.assertEqual(tag.event_uuid, u'8')
    expected_labels = [u'nsrl_present']
    self.assertEqual(tag.labels, expected_labels)
    tag = tags[1]
    self.assertEqual(tag.event_uuid, u'9')
    expected_labels = [u'nsrl_not_present']
    self.assertEqual(tag.labels, expected_labels)


if __name__ == '__main__':
  unittest.main()
