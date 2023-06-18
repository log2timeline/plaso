#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the output mediator object."""

import unittest

from plaso.containers import artifacts
from plaso.lib import definitions
from plaso.storage.fake import writer as fake_writer
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
       'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION,
       'username': 'root'}]

  # TODO: add tests for _GetWinevtRcDatabaseReader

  def testReadMessageFormattersFile(self):
    """Tests the _ReadMessageFormattersFile function."""
    test_file_path = self._GetTestFilePath(['formatters', 'format_test.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      output_mediator = mediator.OutputMediator(storage_writer)

      output_mediator._ReadMessageFormattersFile(test_file_path)
      self.assertEqual(len(output_mediator._message_formatters), 2)
    finally:
      storage_writer.Close()

  # TODO: add tests for _ReadSourceMappings

  # TODO: add tests for GetDisplayNameForPathSpec

  def testGetHostname(self):
    """Tests the GetHostname function."""
    system_configuration = artifacts.SystemConfigurationArtifact()
    system_configuration.hostname = artifacts.HostnameArtifact(name='myhost')

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      storage_writer.AddAttributeContainer(system_configuration)

      output_mediator = mediator.OutputMediator(storage_writer)

      _, event_data, _ = containers_test_lib.CreateEventFromValues(
          self._TEST_EVENTS[0])

      hostname = output_mediator.GetHostname(event_data)
      self.assertEqual(hostname, 'ubuntu')

      event_data.hostname = None

      hostname = output_mediator.GetHostname(event_data)
      self.assertEqual(hostname, 'myhost')

    finally:
      storage_writer.Close()

  def testGetMACBRepresentation(self):
    """Tests the GetMACBRepresentation function."""
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      output_mediator = mediator.OutputMediator(storage_writer)

      event, event_data, _ = containers_test_lib.CreateEventFromValues(
          self._TEST_EVENTS[0])
      macb_representation = output_mediator.GetMACBRepresentation(
          event, event_data)
      self.assertEqual(macb_representation, '..C.')

    finally:
      storage_writer.Close()

  # TODO: add tests for GetMACBRepresentationFromDescriptions
  # TODO: add tests for GetMessageFormatter
  # TODO: add tests for GetRelativePathForPathSpec

  def testGetUsername(self):
    """Tests the GetUsername function."""
    test_user1 = artifacts.UserAccountArtifact(
        identifier='1000', path_separator='\\',
        user_directory='C:\\Users\\testuser1',
        username='testuser1')

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      output_mediator = mediator.OutputMediator(storage_writer)

      storage_writer.AddAttributeContainer(test_user1)

      _, event_data, _ = containers_test_lib.CreateEventFromValues(
          self._TEST_EVENTS[0])

      username = output_mediator.GetUsername(event_data)
      self.assertEqual(username, 'root')

      event_data.username = None
      setattr(event_data, 'user_sid', '1000')

      username = output_mediator.GetUsername(event_data)
      self.assertEqual(username, 'testuser1')

      setattr(event_data, 'user_sid', '1001')

      username = output_mediator.GetUsername(event_data)
      self.assertEqual(username, '-')

    finally:
      storage_writer.Close()

  # TODO: add tests for GetWindowsEventMessage

  def testReadMessageFormattersFromDirectory(self):
    """Tests the ReadMessageFormattersFromDirectory function."""
    test_directory_path = self._GetTestFilePath(['formatters'])
    self._SkipIfPathNotExists(test_directory_path)

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      output_mediator = mediator.OutputMediator(storage_writer)

      output_mediator.ReadMessageFormattersFromDirectory(test_directory_path)
      self.assertEqual(len(output_mediator._message_formatters), 2)

    finally:
      storage_writer.Close()

  def testReadMessageFormattersFromFile(self):
    """Tests the ReadMessageFormattersFromFile function."""
    test_file_path = self._GetTestFilePath(['formatters', 'format_test.yaml'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      output_mediator = mediator.OutputMediator(storage_writer)

      output_mediator.ReadMessageFormattersFromFile(test_file_path)
      self.assertEqual(len(output_mediator._message_formatters), 2)

      with self.assertRaises(KeyError):
        output_mediator.ReadMessageFormattersFromFile(test_file_path)

      output_mediator.ReadMessageFormattersFromFile(
          test_file_path, override_existing=True)
      self.assertEqual(len(output_mediator._message_formatters), 2)

    finally:
      storage_writer.Close()

  # TODO: add tests for SetPreferredLanguageIdentifier
  # TODO: add tests for SetTimezone


if __name__ == '__main__':
  unittest.main()
