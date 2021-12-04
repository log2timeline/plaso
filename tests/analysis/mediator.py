#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the analysis mediator."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.analysis import mediator
from plaso.containers import events
from plaso.containers import sessions
from plaso.lib import definitions
from plaso.storage.fake import writer as fake_writer

from tests.analysis import test_lib
from tests.containers import test_lib as containers_test_lib


class AnalysisMediatorTest(test_lib.AnalysisPluginTestCase):
  """Tests for the analysis mediator."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'windows:registry:key_value',
       'key_path': 'MY AutoRun key',
       'parser': 'UNKNOWN',
       'timestamp': '2012-04-20 22:38:46.929596',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: c:/Temp/evil.exe'},
      {'data_type': 'windows:registry:key_value',
       'key_path': 'HKEY_CURRENT_USER\\Secret\\EvilEmpire\\Malicious_key',
       'parser': 'UNKNOWN',
       'timestamp': '2012-04-20 23:56:46.929596',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: send all the exes to the other world'},
      {'data_type': 'windows:registry:key_value',
       'key_path': 'HKEY_CURRENT_USER\\Windows\\Normal',
       'parser': 'UNKNOWN',
       'timestamp': '2012-04-20 16:44:46',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'values': 'Value: run all the benign stuff'},
      {'data_type': 'text:entry',
       'hostname': 'nomachine',
       'offset': 12,
       'parser': 'UNKNOWN',
       'text': (
           'This is a line by someone not reading the log line properly. And '
           'since this log line exceeds the accepted 80 chars it will be '
           'shortened.'),
       'timestamp': '2009-04-05 12:27:39',
       'timestamp_desc': definitions.TIME_DESCRIPTION_WRITTEN,
       'username': 'johndoe'}]

  def _AddTestEvents(self, storage_writer):
    """Adds tests events to the storage writer.

    Args:
      storage_writer (FakeStorageWriter): storage writer.

    Returns:
      list[EventObject]: test events.
    """
    test_events = []
    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(self._TEST_EVENTS)):
      storage_writer.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      storage_writer.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_writer.AddAttributeContainer(event)

      test_events.append(event)

    return test_events

  def testAddOrUpdateEventTag(self):
    """Tests the _AddOrUpdateEventTag function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base = self._SetUpKnowledgeBase()

    analysis_mediator = mediator.AnalysisMediator(session, knowledge_base)
    analysis_mediator.SetStorageWriter(storage_writer)

    storage_writer.Open()

    try:
      test_events = self._AddTestEvents(storage_writer)

      event_tag = events.EventTag()
      event_identifier = test_events[1].GetIdentifier()
      event_tag.SetEventIdentifier(event_identifier)

      event_tag.AddLabel('Label1')

      number_of_containers = storage_writer.GetNumberOfAttributeContainers(
          event_tag.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 0)

      analysis_mediator._AddOrUpdateEventTag(event_tag)

      number_of_containers = storage_writer.GetNumberOfAttributeContainers(
          event_tag.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 1)

      event_tag = events.EventTag()
      event_identifier = test_events[2].GetIdentifier()
      event_tag.SetEventIdentifier(event_identifier)

      event_tag.AddLabel('Label2')

      analysis_mediator._AddOrUpdateEventTag(event_tag)

      number_of_containers = storage_writer.GetNumberOfAttributeContainers(
          event_tag.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 2)

      event_tag = events.EventTag()
      event_identifier = test_events[1].GetIdentifier()
      event_tag.SetEventIdentifier(event_identifier)

      event_tag.AddLabel('AnotherLabel1')

      analysis_mediator._AddOrUpdateEventTag(event_tag)

      number_of_containers = storage_writer.GetNumberOfAttributeContainers(
          event_tag.CONTAINER_TYPE)
      self.assertEqual(number_of_containers, 2)

      event_tags = list(storage_writer.GetAttributeContainers(
          event_tag.CONTAINER_TYPE))
      self.assertEqual(event_tags[0].labels, ['Label1', 'AnotherLabel1'])
      self.assertEqual(event_tags[1].labels, ['Label2'])

    finally:
      storage_writer.Close()

  def testGetDisplayNameForPathSpec(self):
    """Tests the GetDisplayNameForPathSpec function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base = self._SetUpKnowledgeBase()

    analysis_mediator = mediator.AnalysisMediator(session, knowledge_base)
    analysis_mediator.SetStorageWriter(storage_writer)

    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    expected_display_name = 'OS:{0:s}'.format(test_path)
    display_name = analysis_mediator.GetDisplayNameForPathSpec(os_path_spec)
    self.assertEqual(display_name, expected_display_name)

  # TODO: add test for GetUsernameForPath.
  # TODO: add test for ProduceAnalysisReport.
  # TODO: add test for ProduceEventTag.

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base = self._SetUpKnowledgeBase()

    analysis_mediator = mediator.AnalysisMediator(session, knowledge_base)
    analysis_mediator.SetStorageWriter(storage_writer)

    analysis_mediator.SignalAbort()


if __name__ == '__main__':
  unittest.main()
