#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the VirusTotal analysis plugin."""

from __future__ import unicode_literals

import unittest

try:
  import mock  # pylint: disable=import-error
except ImportError:
  from unittest import mock

from dfdatetime import posix_time as dfdatetime_posix_time
from dfvfs.path import fake_path_spec

from plaso.analysis import virustotal
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib

from tests.analysis import test_lib


class MockResponse(dict):
  """A mock object to simulate a response object from the requests library."""

  # Note: that the following functions do not follow the style guide
  # because they are part of the requests response interface.
  # pylint: disable=invalid-name

  def json(self):
    """Provided for compatibility with the requests library."""
    return self

  def raise_for_status(self):
    """Provided for compatibility with the requests library."""
    return


class VirusTotalTest(test_lib.AnalysisPluginTestCase):
  """Tests for the VirusTotal analysis plugin."""

  _EVENT_1_HASH = '90'

  _FAKE_API_KEY = '4'

  _TEST_EVENTS = [{
      'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:00'),
      'sha256_hash': _EVENT_1_HASH}]

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

    if params['resource'] != self._EVENT_1_HASH:
      self.fail('Unexpected parameters to request.get()')

    response = MockResponse()
    response['resource'] = self._EVENT_1_HASH
    response['response_code'] = 1
    response['positives'] = 10
    return response

  def _CreateTestEventObject(self, event_dictionary):
    """Create a test event with a set of attributes.

    Args:
      event_dictionary (dict[str, str]): contains attributes of an event to add
          to the queue.

    Returns:
      EventObject: event with the appropriate attributes for testing.
    """
    date_time = dfdatetime_posix_time.PosixTime(
        timestamp=event_dictionary['timestamp'])
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)

    event.data_type = 'pe:compilation:compilation_time'
    event.pe_type = 'Executable (EXE)'

    for attribute_name, attribute_value in event_dictionary.items():
      if attribute_name == 'timestamp':
        continue

      setattr(event, attribute_name, attribute_value)

    return event

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.requests_patcher = mock.patch('requests.get', self._MockGet)
    self.requests_patcher.start()

  def tearDown(self):
    """Cleans up after running an individual test."""
    self.requests_patcher.stop()

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    events = []
    for event_dictionary in self._TEST_EVENTS:
      event_dictionary['pathspec'] = fake_path_spec.FakePathSpec(
          location='C:\\WINDOWS\\system32\\evil.exe')

      event = self._CreateTestEventObject(event_dictionary)
      events.append(event)

    plugin = virustotal.VirusTotalAnalysisPlugin()
    plugin.SetAPIKey(self._FAKE_API_KEY)

    storage_writer = self._AnalyzeEvents(events, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)
    self.assertEqual(storage_writer.number_of_event_tags, 1)

    report = storage_writer.analysis_reports[0]
    self.assertIsNotNone(report)

    expected_text = (
        'virustotal hash tagging results\n'
        '1 path specifications tagged with label: virustotal_detections_10\n')
    self.assertEqual(report.text, expected_text)

    labels = []
    for event_tag in storage_writer.GetEventTags():
      labels.extend(event_tag.labels)
    self.assertEqual(len(labels), 1)

    expected_labels = ['virustotal_detections_10']
    self.assertEqual(labels, expected_labels)


if __name__ == '__main__':
  unittest.main()
