#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output mediator object."""

import unittest

from plaso.containers import artifacts
from plaso.engine import knowledge_base
from plaso.lib import definitions
from plaso.output import mediator

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class OutputMediatorTest(test_lib.OutputModuleTestCase):
  """Tests for the output mediator object."""

  # pylint: disable=protected-access

  _TEST_EVENTS = [
      {'data_type': 'test:event',
       'filename': 'log/syslog.1',
       'hostname': 'ubuntu',
       'text': (
           'Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n '
           'closed for user root)'),
       'timestamp': '2012-06-27 18:17:01',
       'timestamp_desc': definitions.TIME_DESCRIPTION_CHANGE,
       'username': 'root'}]

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._knowledge_base = knowledge_base.KnowledgeBase()

    hostname_artifact = artifacts.HostnameArtifact(name='myhost')
    self._knowledge_base.SetHostname(hostname_artifact)

  # TODO: add tests for _GetWinevtRcDatabaseReader

  def testReadMessageFormattersFile(self):
    """Tests the _ReadMessageFormattersFile function."""
    test_file_path = self._GetTestFilePath(['formatters', 'format_test.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    output_mediator = mediator.OutputMediator(self._knowledge_base, None)

    output_mediator._ReadMessageFormattersFile(test_file_path)
    self.assertEqual(len(output_mediator._message_formatters), 2)

  # TODO: add tests for GetDisplayNameForPathSpec

  def testGetHostname(self):
    """Tests the GetHostname function."""
    output_mediator = mediator.OutputMediator(self._knowledge_base, None)

    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])

    hostname = output_mediator.GetHostname(event_data)
    self.assertEqual(hostname, 'ubuntu')

  def testGetMACBRepresentation(self):
    """Tests the GetMACBRepresentation function."""
    output_mediator = mediator.OutputMediator(self._knowledge_base, None)

    event, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    macb_representation = output_mediator.GetMACBRepresentation(
        event, event_data)
    self.assertEqual(macb_representation, '..C.')

  # TODO: add tests for GetMACBRepresentationFromDescriptions
  # TODO: add tests for GetMessageFormatter
  # TODO: add tests for GetRelativePathForPathSpec

  def testGetUsername(self):
    """Tests the GetUsername function."""
    output_mediator = mediator.OutputMediator(self._knowledge_base, None)

    _, event_data, _ = containers_test_lib.CreateEventFromValues(
        self._TEST_EVENTS[0])
    username = output_mediator.GetUsername(event_data)
    self.assertEqual(username, 'root')

  # TODO: add tests for GetWindowsEventMessage

  def testReadMessageFormattersFromDirectory(self):
    """Tests the ReadMessageFormattersFromDirectory function."""
    test_directory_path = self._GetTestFilePath(['formatters'])
    self._SkipIfPathNotExists(test_directory_path)

    output_mediator = mediator.OutputMediator(self._knowledge_base, None)

    output_mediator.ReadMessageFormattersFromDirectory(test_directory_path)
    self.assertEqual(len(output_mediator._message_formatters), 2)

  def testReadMessageFormattersFromFile(self):
    """Tests the ReadMessageFormattersFromFile function."""
    test_file_path = self._GetTestFilePath(['formatters', 'format_test.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    output_mediator = mediator.OutputMediator(self._knowledge_base, None)

    output_mediator.ReadMessageFormattersFromFile(test_file_path)
    self.assertEqual(len(output_mediator._message_formatters), 2)

  # TODO: add tests for SetPreferredLanguageIdentifier
  # TODO: add tests for SetTimezone


if __name__ == '__main__':
  unittest.main()
