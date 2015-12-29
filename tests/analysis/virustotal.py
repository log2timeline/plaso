#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the VirusTotal analysis plugin."""

import mock
import unittest

from dfvfs.path import fake_path_spec

from plaso.analysis import virustotal
from plaso.engine import queue
from plaso.engine import single_process
from plaso.lib import timelib
from plaso.parsers import pe

from tests.analysis import test_lib


class VirusTotalTest(test_lib.AnalysisPluginTestCase):
  """Tests for the VirusTotal analysis plugin."""
  EVENT_1_HASH = u'90'
  FAKE_API_KEY = u'4'
  TEST_EVENTS = [
      {u'timestamp': timelib.Timestamp.CopyFromString(u'2015-01-01 17:00:00'),
       u'sha256_hash': EVENT_1_HASH,
       u'uuid': u'8'
      }
  ]

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.requests_patcher = mock.patch(u'requests.get', self._MockGet)
    self.requests_patcher.start()

  def tearDown(self):
    """Cleans up after running an individual test."""
    self.requests_patcher.stop()

  def _MockGet(self, url, params):
    """A mock method to simulate making an API request to VirusTotal.

    Args:
      url: The URL (string) being requested.
      params: HTTP parameters (instance of dict) for the VirusTotal API request.

    Returns:
      A mocked response object (instance of MockResponse) that
      simulates a real response object returned by the requests library from the
      VirusTotal API.
    """
    # pylint: disable=protected-access
    self.assertEqual(
        url, virustotal.VirusTotalAnalyzer._VIRUSTOTAL_API_REPORT_URL)
    if params[u'resource'] == self.EVENT_1_HASH:
      response = MockResponse()
      response[u'resource'] = self.EVENT_1_HASH
      response[u'response_code'] = 1
      response[u'positives'] = 10
      return response
    self.fail(u'Unexpected parameters to request.get()')

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
        pe_event[u'timestamp'], u'Executable (EXE)', [], u'')
    event_object.pathspec = test_pathspec
    event_object.sha256_hash = pe_event[u'sha256_hash']
    event_object.uuid = pe_event[u'uuid']
    return event_object

  def testVirusTotalLookup(self):
    """Tests for the VirusTotal analysis plugin."""
    event_queue = single_process.SingleProcessQueue()
    knowledge_base = self._SetUpKnowledgeBase()

    # Fill the incoming queue with events.
    test_queue_producer = queue.ItemQueueProducer(event_queue)
    events = [self._CreateTestEventObject(test_event)
              for test_event
              in self.TEST_EVENTS]
    test_queue_producer.ProduceItems(events)
    analysis_plugin = virustotal.VirusTotalAnalysisPlugin(event_queue)
    analysis_plugin.SetAPIKey(self.FAKE_API_KEY)

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
    self.assertEqual(tag.tags[0], u'virustotal_detections_10')


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
