#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the VirusTotal analysis plugin."""

import unittest

import mock
from dfvfs.path import fake_path_spec

from plaso.analysis import virustotal
from plaso.lib import timelib
from plaso.parsers import pe

from tests.analysis import test_lib


class MockResponse(dict):
  """A mock object to simulate a response object from the requests library."""

  def json(self):
    """Provided for compatibility with the requests library."""
    return self

  def raise_for_status(self):
    """Provided for compatibility with the requests library."""
    return


class VirusTotalTest(test_lib.AnalysisPluginTestCase):
  """Tests for the VirusTotal analysis plugin."""

  _EVENT_1_HASH = u'90'

  _FAKE_API_KEY = u'4'

  _TEST_EVENTS = [{
      u'timestamp': timelib.Timestamp.CopyFromString(u'2015-01-01 17:00:00'),
      u'sha256_hash': _EVENT_1_HASH,
      u'uuid': u'8'}]

  def _MockGet(self, url, params):
    """Mock function to simulate a VirusTotal API request.

    Args:
      url (str): URL being requested.
      params (dict[str, object]): HTTP parameters for the VirusTotal API
          request.

    Returns:
      MockResponse: mocked response that simulates a real response object
          returned by the requests library from the VirusTotal API.
    """
    # pylint: disable=protected-access
    self.assertEqual(
        url, virustotal.VirusTotalAnalyzer._VIRUSTOTAL_API_REPORT_URL)
    if params[u'resource'] == self._EVENT_1_HASH:
      response = MockResponse()
      response[u'resource'] = self._EVENT_1_HASH
      response[u'response_code'] = 1
      response[u'positives'] = 10
      return response
    self.fail(u'Unexpected parameters to request.get()')

  def _CreateTestEventObject(self, event_dictionary):
    """Create a test event with a set of attributes.

    Args:
      event_dictionary (dict[str, str]): contains attributes of an event to add
          to the queue.

    Returns:
      EventObject: event with the appropriate attributes for testing.
    """
    event = pe.PECompilationEvent(
        event_dictionary[u'timestamp'], u'Executable (EXE)', [], u'')

    for attribute_name, attribute_value in event_dictionary.items():
      if attribute_name == u'timestamp':
        continue

      setattr(event, attribute_name, attribute_value)

    return event

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.requests_patcher = mock.patch(u'requests.get', self._MockGet)
    self.requests_patcher.start()

  def tearDown(self):
    """Cleans up after running an individual test."""
    self.requests_patcher.stop()

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    events = []
    for event_dictionary in self._TEST_EVENTS:
      event_dictionary[u'pathspec'] = fake_path_spec.FakePathSpec(
          location=u'C:\\WINDOWS\\system32\\evil.exe')

      event = self._CreateTestEventObject(event_dictionary)
      events.append(event)

    plugin = virustotal.VirusTotalAnalysisPlugin()
    plugin.SetAPIKey(self._FAKE_API_KEY)

    storage_writer = self._AnalyzeEvents(events, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    tags = analysis_report.GetTags()
    self.assertEqual(len(tags), 1)

    tag = tags[0]
    self.assertEqual(tag.event_uuid, u'8')
    self.assertEqual(tag.labels[0], u'virustotal_detections_10')


if __name__ == '__main__':
  unittest.main()
