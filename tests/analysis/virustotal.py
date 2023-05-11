#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the VirusTotal analysis plugin."""

import collections
import unittest

from unittest import mock

from dfvfs.path import fake_path_spec

from plaso.analysis import virustotal
from plaso.containers import events
from plaso.containers import reports
from plaso.lib import definitions

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

  # pylint: disable=protected-access

  _EVENT_1_HASH = '90'

  _FAKE_API_KEY = '4'

  _TEST_EVENTS = [{
      '_parser_chain': 'pe',
      'data_type': 'pe:compilation:compilation_time',
      'path_spec': fake_path_spec.FakePathSpec(
          location='C:\\WINDOWS\\system32\\evil.exe'),
      'pe_type': 'Executable (EXE)',
      'sha256_hash': _EVENT_1_HASH,
      'timestamp': '2015-01-01 17:00:00',
      'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  # pylint: disable=unused-argument
  def _MockGet(self, url, params=None, timeout=None):
    """Mock function to simulate a VirusTotal API request.

    Args:
      url (str): URL being requested.
      params (Optional[dict[str, object]]): HTTP parameters for the VirusTotal
          API request.
      timeout (Optional[int]): number of seconds to wait for to establish
          a connection to a remote machine.

    Returns:
      MockResponse: mocked response that simulates a real response object
          returned by the requests library from the VirusTotal API.
    """
    self.assertEqual(
        url, virustotal.VirusTotalAnalysisPlugin._VIRUSTOTAL_API_REPORT_URL)

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

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)
    self.assertIsNotNone(analysis_report)

    self.assertEqual(analysis_report.plugin_name, 'virustotal')

    expected_analysis_counter = collections.Counter({
        'virustotal_detections_10': 1})
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

    expected_labels = ['virustotal_detections_10']
    self.assertEqual(labels, expected_labels)


if __name__ == '__main__':
  unittest.main()
