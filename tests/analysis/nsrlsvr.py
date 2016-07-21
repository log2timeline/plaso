#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the nsrlsvr analysis plugin."""
import unittest

import mock
from dfvfs.path import fake_path_spec

from plaso.analysis import nsrlsvr
from plaso.engine import plaso_queue
from plaso.engine import single_process
from plaso.lib import timelib
from plaso.parsers import pe

from tests.analysis import test_lib

class MockNsrlsvrSocket(object):
  """Mock socket object for testing."""

  def __init__(self):
    super(MockNsrlsvrSocket, self).__init__()
    self._data = None

  def recv(self, unused_buffer_size):
    if self._data == u'QUERY {0:s}'.format(NsrlSvrTest.EVENT_1_HASH):
      self._data = None
      return u'OK 1'
    else:
      self._data = None
      return u'OK 0'

  def sendall(self, data):
    self._data = data

class NsrlSvrTest(test_lib.AnalysisPluginTestCase):
  """Tests for the Nsrlsvr analysis plugin."""
  EVENT_1_HASH = (
      u'2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff')
  TEST_EVENTS = [{
      u'timestamp': timelib.Timestamp.CopyFromString(u'2015-01-01 17:00:00'),
      u'sha256_hash': EVENT_1_HASH,
      u'uuid': u'8'}]


  def setUp(self):
    """Makes preparations before running an individual test."""
    self.requests_patcher = mock.patch(
        'socket.create_connection', self._MockCreateConnection)
    self.requests_patcher.start()


  def tearDown(self):
    """Cleans up after running an individual test."""
    self.requests_patcher.stop()

  def _MockCreateConnection(self, unused_connection_information):
    """Mocks the socket create_connection call"""
    return MockNsrlsvrSocket()

  def _CreateTestEventObject(self, pe_event):
    """Create a test event object with a particular path.

    Args:
      pe_event: A hash containing attributes of an event to add to the
                     queue.

    Returns:
      An event object (instance of EventObject) that contains the necessary
      attributes for testing.
    """
    test_pathspec = fake_path_spec.FakePathSpec(
        location=u'C:\\WINDOWS\\system32\\evil.exe')
    event_object = pe.PECompilationEvent(
        pe_event[u'timestamp'], u'Executable (EXE)', [], '')
    event_object.pathspec = test_pathspec
    event_object.sha256_hash = pe_event[u'sha256_hash']
    event_object.uuid = pe_event[u'uuid']
    return event_object


  def testNsrlsvrLookup(self):
    """Tests for the nsrlsvr analysis plugin."""
    event_queue = single_process.SingleProcessQueue()
    knowledge_base = self._SetUpKnowledgeBase()
  
    # Fill the incoming queue with events.
    test_queue_producer = plaso_queue.ItemQueueProducer(event_queue)
    events = [self._CreateTestEventObject(test_event) for test_event in
              self.TEST_EVENTS]
    test_queue_producer.ProduceItems(events)
  
    # Set up the plugin.
    analysis_plugin = nsrlsvr.NsrlsvrAnalysisPlugin(event_queue)
    analysis_plugin.SetHost(u'127.0.0.1')
    analysis_plugin.SetPort(u'9120')
  
    # Run the analysis plugin.
    analysis_report_queue_consumer = self._RunAnalysisPlugin(analysis_plugin,
      knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
      analysis_report_queue_consumer)
  
    self.assertEqual(len(analysis_reports), 1)
    report = analysis_reports[0]
    tags = report.GetTags()
    self.assertEqual(len(tags), 1)
    tag = tags[0]
    self.assertEqual(tag.event_uuid, u'8')
    expected_labels = [u'nsrl_present']
    self.assertEqual(tag.labels, expected_labels)


if __name__ == '__main__':
  unittest.main()