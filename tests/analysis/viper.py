#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Viper analysis plugin."""

import unittest

import mock
from dfvfs.path import fake_path_spec

from plaso.analysis import mediator
from plaso.analysis import viper
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


class ViperTest(test_lib.AnalysisPluginTestCase):
  """Tests for the Viper analysis plugin."""

  _EVENT_1_HASH = (
      u'2d79fcc6b02a2e183a0cb30e0e25d103f42badda9fbf86bbee06f93aa3855aff')

  _TEST_EVENTS = [{
      u'timestamp': timelib.Timestamp.CopyFromString(u'2015-01-01 17:00:00'),
      u'sha256_hash': _EVENT_1_HASH,
      u'uuid': u'8'}]

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
    event = pe.PECompilationEvent(
        event_dictionary[u'timestamp'], u'Executable (EXE)', [], u'')

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
    knowledge_base = self._SetUpKnowledgeBase()
    analysis_mediator = mediator.AnalysisMediator(None, knowledge_base)

    plugin = viper.ViperAnalysisPlugin()
    plugin.SetProtocol(u'http')
    plugin.SetHost(u'localhost')

    for event_dictionary in self._TEST_EVENTS:
      event_dictionary[u'pathspec'] = fake_path_spec.FakePathSpec(
          location=u'C:\\WINDOWS\\system32\\evil.exe')

      event = self._CreateTestEventObject(event_dictionary)
      plugin.ExamineEvent(analysis_mediator, event)

    analysis_report = plugin.CompileReport(analysis_mediator)
    self.assertIsNotNone(analysis_report)

    tags = analysis_report.GetTags()
    self.assertEqual(len(tags), 1)

    tag = tags[0]
    self.assertEqual(tag.event_uuid, u'8')

    expected_labels = [
        u'viper_present', u'viper_project_default', u'viper_tag_rat',
        u'viper_tag_darkcomet']

    self.assertEqual(tag.labels, expected_labels)


if __name__ == '__main__':
  unittest.main()
