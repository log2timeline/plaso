#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the parsers mediator."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import sessions
from plaso.lib import timelib
from plaso.engine import configurations
from plaso.storage import fake_storage

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class ParsersMediatorTest(test_lib.ParserTestCase):
  """Tests for the parsers mediator."""

  # pylint: disable=protected-access

  def testGetEarliestYearFromFileEntry(self):
    """Tests the _GetEarliestYearFromFileEntry function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    earliest_year = parsers_mediator._GetEarliestYearFromFileEntry()
    self.assertIsNone(earliest_year)

    # TODO: improve test coverage.

  # TODO: add tests for _GetInode.

  def testGetLatestYearFromFileEntry(self):
    """Tests the _GetLatestYearFromFileEntry function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    latest_year = parsers_mediator._GetLatestYearFromFileEntry()
    self.assertIsNone(latest_year)

    # TODO: improve test coverage.

  # TODO: add tests for AddEventAttribute.
  # TODO: add tests for AppendToParserChain.
  # TODO: add tests for ClearEventAttributes.
  # TODO: add tests for ClearParserChain.

  @shared_test_lib.skipUnlessHasTestFile([u'syslog.gz'])
  @shared_test_lib.skipUnlessHasTestFile([u'vsstest.qcow2'])
  def testGetDisplayName(self):
    """Tests the GetDisplayName function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    with self.assertRaises(ValueError):
      parsers_mediator.GetDisplayName(file_entry=None)

    test_path = self._GetTestFilePath([u'syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)

    display_name = parsers_mediator.GetDisplayName(file_entry=file_entry)

    expected_display_name = u'OS:{0:s}'.format(test_path)
    self.assertEqual(display_name, expected_display_name)

    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

    display_name = parsers_mediator.GetDisplayName(file_entry=file_entry)

    expected_display_name = u'GZIP:{0:s}'.format(test_path)
    self.assertEqual(display_name, expected_display_name)

    test_path = self._GetTestFilePath([u'vsstest.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    vshadow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/vss2',
        store_index=1, parent=qcow_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=35, location=u'/syslog.gz',
        parent=vshadow_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

    display_name = parsers_mediator.GetDisplayName(file_entry=file_entry)

    expected_display_name = u'VSS2:TSK:/syslog.gz'
    self.assertEqual(display_name, expected_display_name)

    configuration = configurations.EventExtractionConfiguration()
    configuration.text_prepend = u'C:'

    parsers_mediator.SetEventExtractionConfiguration(configuration)
    display_name = parsers_mediator.GetDisplayName(file_entry=file_entry)
    expected_display_name = u'VSS2:TSK:C:/syslog.gz'
    self.assertEqual(display_name, expected_display_name)

    # TODO: add test with relative path.

  def testGetDisplayNameForPathSpec(self):
    """Tests the GetDisplayNameForPathSpec function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    test_path = self._GetTestFilePath([u'syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    expected_display_name = u'OS:{0:s}'.format(test_path)
    display_name = parsers_mediator.GetDisplayNameForPathSpec(os_path_spec)
    self.assertEqual(display_name, expected_display_name)

  def testGetEstimatedYear(self):
    """Tests the GetEstimatedYear function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    expected_estimated_year = timelib.GetCurrentYear()
    estimated_year = parsers_mediator.GetEstimatedYear()
    self.assertEqual(estimated_year, expected_estimated_year)

    # TODO: improve test coverage.

  def testGetFileEntry(self):
    """Tests the GetFileEntry function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    file_entry = parsers_mediator.GetFileEntry()
    self.assertIsNone(file_entry)

  def testGetFilename(self):
    """Tests the GetFilename function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    filename = parsers_mediator.GetFilename()
    self.assertIsNone(filename)

  def testGetLatestYear(self):
    """Tests the GetLatestYear function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    expected_latest_year = timelib.GetCurrentYear()
    latest_year = parsers_mediator.GetLatestYear()
    self.assertEqual(latest_year, expected_latest_year)

  # TODO: add tests for GetParserChain.
  # TODO: add tests for PopFromParserChain.
  # TODO: add tests for ProcessEvent.
  # TODO: add tests for ProduceEvent.
  # TODO: add tests for ProduceEvents.
  # TODO: add tests for ProduceEventSource.
  # TODO: add tests for ProduceEventWithEventData.
  # TODO: add tests for ProduceExtractionError.
  # TODO: add tests for RemoveEventAttribute.

  def testResetFileEntry(self):
    """Tests the ResetFileEntry function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    parsers_mediator.ResetFileEntry()

  # TODO: add tests for SetEventExtractionConfiguration.
  # TODO: add tests for SetInputSourceConfiguration.

  def testSetFileEntry(self):
    """Tests the SetFileEntry function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    parsers_mediator.SetFileEntry(None)

  def testSetStorageWriter(self):
    """Tests the SetStorageWriter function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    parsers_mediator.SetStorageWriter(None)

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    parsers_mediator = self._CreateParserMediator(storage_writer)

    parsers_mediator.SignalAbort()


if __name__ == '__main__':
  unittest.main()
