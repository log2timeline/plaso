#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Viper analysis plugin."""

import unittest

import mock

from dfdatetime import posix_time as dfdatetime_posix_time
from dfvfs.path import fake_path_spec

from plaso.analysis import viper
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib

from tests.analysis import test_lib


class MockResponse(dict):
  """A mock object to simulate a response object from the requests library."""

  def json(self):
    """Provided for compatibility with the requests library."""
    return self

  def raise_for_status(self):
    """Provided for compatibility with the requests library."""
    return


class ViperTest(test_lib.AnalysisPluginTestCase):
  """Tests for the Viper analysis plugin."""

  _EVENT_1_HASH = (
      u'2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff')

  _TEST_EVENTS = [{
      u'timestamp': timelib.Timestamp.CopyFromString(u'2015-01-01 17:00:00'),
      u'sha256_hash': _EVENT_1_HASH}]

  def _MockPost(self, unused_url, data=None):
    """Mock funtion to simulate a Viper API request.

    Args:
      url (str): URL being requested.
      data (dict[str, object]): simulated form data for the Viper API request.

    Returns:
      MockResponse: mocked response that simulates a real response object
          returned by the requests library from the Viper API.
    """
    sha256_hash = data.get(u'sha256', None)
    if sha256_hash != self._EVENT_1_HASH:
      self.fail(u'Unexpected data in request.post().')

    response = MockResponse()
    response[u'default'] = ({
        u'sha1': u'13da502ab0d75daca5e5075c60e81bfe3b7a637f',
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
        u'size': 774144},)

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
        timestamp=event_dictionary[u'timestamp'])
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)

    event.data_type = u'pe:compilation:compilation_time'
    event.pe_type = u'Executable (EXE)'

    for attribute_name, attribute_value in event_dictionary.items():
      if attribute_name == u'timestamp':
        continue

      setattr(event, attribute_name, attribute_value)

    return event

  def setUp(self):
    """Makes preparations before running an individual test."""
    self.requests_patcher = mock.patch(u'requests.post', self._MockPost)
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

    plugin = viper.ViperAnalysisPlugin()
    plugin.SetHost(u'localhost')
    plugin.SetPort(8080)
    plugin.SetProtocol(u'http')

    storage_writer = self._AnalyzeEvents(events, plugin)

    self.assertEqual(len(storage_writer.analysis_reports), 1)
    self.assertEqual(len(storage_writer.event_tags), 1)

    report = storage_writer.analysis_reports[0]
    self.assertIsNotNone(report)

    expected_text = (
        u'viper hash tagging results\n'
        u'1 path specifications tagged with label: viper_present\n'
        u'1 path specifications tagged with label: viper_project_default\n'
        u'1 path specifications tagged with label: viper_tag_darkcomet\n'
        u'1 path specifications tagged with label: viper_tag_rat\n')

    self.assertEqual(report.text, expected_text)

    labels = []
    for event_tag in storage_writer.event_tags:
      labels.extend(event_tag.labels)
    self.assertEqual(len(labels), 4)

    expected_labels = [
        u'viper_present', u'viper_project_default', u'viper_tag_darkcomet',
        u'viper_tag_rat']
    self.assertEqual(sorted(labels), expected_labels)


if __name__ == '__main__':
  unittest.main()
