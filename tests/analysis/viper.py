#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Viper analysis plugin."""

import mock
import unittest

from dfvfs.path import fake_path_spec

from plaso.analysis import viper
from plaso.engine import queue
from plaso.engine import single_process
from plaso.lib import timelib
from plaso.parsers import pe

from tests.analysis import test_lib


class ViperTest(test_lib.AnalysisPluginTestCase):
  """Tests for the Viper analysis plugin."""
  EVENT_1_HASH = (
      u'2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff')
  TEST_EVENTS = [{
      u'timestamp': timelib.Timestamp.CopyFromString(u'2015-01-01 17:00:00'),
      u'sha256_hash': EVENT_1_HASH,
      u'uuid': u'8'}]

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.requests_patcher = mock.patch('requests.post', self._MockPost)
    self.requests_patcher.start()

  def tearDown(self):
    """Cleans up after running an individual test."""
    self.requests_patcher.stop()

  def _MockPost(self, unused_url, data=None):
    """A mock method to simulate making an API request to Viper.

    Args:
      unused_url: The URL (string) being requested.
      data: Simulated form data (instance of dict) for the Viper API request.

    Returns:
      A mocked response object (instance of MockResponse) that
      simulates a real response object returned by the requests library from the
      Viper API.
    """
    if data.get(u'sha256', None) != self.EVENT_1_HASH:
      self.fail(u'Unexpected data in request.post().')

    response = MockResponse()
    response[u'default'] = (
        {u'sha1': u'13da502ab0d75daca5e5075c60e81bfe3b7a637f',
         u'name': u'darkcomet.exe',
         u'tags': [
             u'rat',
             u'darkcomet'],
         u'sha512': u'7e81e0c4f49f1884ebebdf6e53531e7836721c2ae417'
                    u'29cf5bc0340f3369e7d37fe4168a7434b2b0420b299f5c'
                    u'1d9a4f482f1bda8e66e40345757d97e5602b2d',
         u'created_at': u'2015-03-30 23:13:20.595238',
         u'crc32': u'2238B48E',
         u'ssdeep': u'12288:D9HFJ9rJxRX1uVVjoaWSoynxdO1FVBaOiRZTERfIhNk'
                    u'NCCLo9Ek5C/hlg:NZ1xuVVjfFoynPaVBUR8f+kN10EB/g',
         u'sha256': u'2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f9'
                    u'3aa3855aff',
         u'type': u'PE32 executable (GUI) Intel 80386, for MS Windows',
         u'id': 10,
         u'md5': u'9f2520a3056543d49bb0f822d85ce5dd',
         u'size': 774144
        },)
    return response

  def _CreateTestEventObject(self, pe_event):
    """Create a test event object with a particular path.

    Args:
      service_event: A hash containing attributes of an event to add to the
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

  def testViperLookup(self):
    """Tests for the Viper analysis plugin."""
    event_queue = single_process.SingleProcessQueue()
    knowledge_base = self._SetUpKnowledgeBase()

    # Fill the incoming queue with events.
    test_queue_producer = queue.ItemQueueProducer(event_queue)
    events = [self._CreateTestEventObject(test_event)
              for test_event
              in self.TEST_EVENTS]
    test_queue_producer.ProduceItems(events)

    # Set up the plugin.
    analysis_plugin = viper.ViperAnalysisPlugin(event_queue)
    analysis_plugin.SetProtocol(u'http')
    analysis_plugin.SetHost(u'localhost')

    # Run the analysis plugin.
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEqual(len(analysis_reports), 1)
    report = analysis_reports[0]
    tags = report.GetTags()
    self.assertEqual(len(tags), 1)
    tag = tags[0]
    self.assertEqual(tag.event_uuid, u'8')
    expected_labels = [
        u'viper_present', u'viper_project_default', u'viper_tag_rat',
        u'viper_tag_darkcomet'
    ]
    self.assertEqual(tag.labels, expected_labels)


class MockResponse(dict):
  """An object to simulate a response object from the requests library."""
  def json(self):
    """Provided for compatibility with the requests library."""
    return self

  def raise_for_status(self):
    """Provided for compatibility with the requests library."""
    return


if __name__ == '__main__':
  unittest.main()
