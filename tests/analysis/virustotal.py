#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the VirusTotal analysis plugin."""

from __future__ import unicode_literals

import unittest

try:
  import mock  # pylint: disable=import-error
except ImportError:
  from unittest import mock

from dfvfs.path import fake_path_spec

from plaso.analysis import virustotal
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
      'data_type': 'pe:compilation:compilation_time',
      'pathspec': fake_path_spec.FakePathSpec(
          location='C:\\WINDOWS\\system32\\evil.exe'),
      'pe_type': 'Executable (EXE)',
      'sha256_hash': _EVENT_1_HASH,
      'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:00'),
      'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

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

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.requests_patcher = mock.patch('requests.get', self._MockGet)
    self.requests_patcher.start()

  def tearDown(self):
    """Cleans up after running an individual test."""
    self.requests_patcher.stop()

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    plugin = virustotal.VirusTotalAnalysisPlugin()
    plugin.SetAPIKey(self._FAKE_API_KEY)

    storage_writer = self._AnalyzeEvents(self._TEST_EVENTS, plugin)

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
