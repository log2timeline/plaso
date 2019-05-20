#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Viper analysis plugin."""

from __future__ import unicode_literals

import unittest

try:
  import mock  # pylint: disable=import-error
except ImportError:
  from unittest import mock

from dfvfs.path import fake_path_spec

from plaso.analysis import viper
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


class ViperTest(test_lib.AnalysisPluginTestCase):
  """Tests for the Viper analysis plugin."""

  _EVENT_1_HASH = (
      '2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff')

  _TEST_EVENTS = [{
      'data_type': 'pe:compilation:compilation_time',
      'pathspec': fake_path_spec.FakePathSpec(
          location='C:\\WINDOWS\\system32\\evil.exe'),
      'pe_type': 'Executable (EXE)',
      'sha256_hash': _EVENT_1_HASH,
      'timestamp': timelib.Timestamp.CopyFromString('2015-01-01 17:00:00'),
      'timestamp_desc': definitions.TIME_DESCRIPTION_UNKNOWN}]

  # pylint: disable=unused-argument
  def _MockPost(self, url, data=None):
    """Mock function to simulate a Viper API request.

    Args:
      url (str): URL being requested.
      data (dict[str, object]): simulated form data for the Viper API request.

    Returns:
      MockResponse: mocked response that simulates a real response object
          returned by the requests library from the Viper API.
    """
    sha256_hash = data.get('sha256', None)
    if sha256_hash != self._EVENT_1_HASH:
      self.fail('Unexpected data in request.post().')

    response = MockResponse()
    response['default'] = ({
        'sha1': '13da502ab0d75daca5e5075c60e81bfe3b7a637f',
        'name': 'darkcomet.exe',
        'tags': [
            'rat',
            'darkcomet'],
        'sha512': '7e81e0c4f49f1884ebebdf6e53531e7836721c2ae417'
                  '29cf5bc0340f3369e7d37fe4168a7434b2b0420b299f5c'
                  '1d9a4f482f1bda8e66e40345757d97e5602b2d',
        'created_at': '2015-03-30 23:13:20.595238',
        'crc32': '2238B48E',
        'ssdeep': '12288:D9HFJ9rJxRX1uVVjoaWSoynxdO1FVBaOiRZTERfIhNk'
                  'NCCLo9Ek5C/hlg:NZ1xuVVjfFoynPaVBUR8f+kN10EB/g',
        'sha256': '2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f9'
                  '3aa3855aff',
        'type': 'PE32 executable (GUI) Intel 80386, for MS Windows',
        'id': 10,
        'md5': '9f2520a3056543d49bb0f822d85ce5dd',
        'size': 774144},)

    return response

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.requests_patcher = mock.patch('requests.post', self._MockPost)
    self.requests_patcher.start()

  def tearDown(self):
    """Cleans up after running an individual test."""
    self.requests_patcher.stop()

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    test_events = []
    for event_values in self._TEST_EVENTS:
      event, event_data = self._CreateTestEvent(event_values)
      test_events.append((event, event_data))

    plugin = viper.ViperAnalysisPlugin()
    plugin.SetHost('localhost')
    plugin.SetPort(8080)
    plugin.SetProtocol('http')

    storage_writer = self._AnalyzeEvents(test_events, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)
    self.assertEqual(storage_writer.number_of_event_tags, 1)

    report = storage_writer.analysis_reports[0]
    self.assertIsNotNone(report)

    expected_text = (
        'viper hash tagging results\n'
        '1 path specifications tagged with label: viper_present\n'
        '1 path specifications tagged with label: viper_project_default\n'
        '1 path specifications tagged with label: viper_tag_darkcomet\n'
        '1 path specifications tagged with label: viper_tag_rat\n')

    self.assertEqual(report.text, expected_text)

    labels = []
    for event_tag in storage_writer.GetEventTags():
      labels.extend(event_tag.labels)
    self.assertEqual(len(labels), 4)

    expected_labels = [
        'viper_present', 'viper_project_default', 'viper_tag_darkcomet',
        'viper_tag_rat']
    self.assertEqual(sorted(labels), expected_labels)


if __name__ == '__main__':
  unittest.main()
