#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the parsers mediator."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import events
from plaso.parsers import mediator
from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class ParsersMediatorTest(test_lib.ParserTestCase):
  """Tests for the parsers mediator."""

  # pylint: disable=protected-access

  # TODO: add tests for AppendToParserChain.
  # TODO: add tests for ClearParserChain.

  def testGetCodePage(self):
    """Tests the GetCodePage function."""
    parser_mediator = mediator.ParserMediator()

    code_page = parser_mediator.GetCodePage()
    self.assertEqual(code_page, 'cp1252')

    # TODO: improve test coverage.

  def testGetDisplayName(self):
    """Tests the GetDisplayName function."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    with self.assertRaises(ValueError):
      parser_mediator.GetDisplayName(file_entry=None)

    test_file_path = self._GetTestFilePath(['syslog.gz'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)

    display_name = parser_mediator.GetDisplayName(file_entry=file_entry)

    expected_display_name = 'OS:{0:s}'.format(test_file_path)
    self.assertEqual(display_name, expected_display_name)

    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

    display_name = parser_mediator.GetDisplayName(file_entry=file_entry)

    expected_display_name = 'GZIP:{0:s}'.format(test_file_path)
    self.assertEqual(display_name, expected_display_name)

    test_file_path = self._GetTestFilePath(['vsstest.qcow2'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    vshadow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location='/vss2',
        store_index=1, parent=qcow_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=35, location='/syslog.gz',
        parent=vshadow_path_spec)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(tsk_path_spec)

    display_name = parser_mediator.GetDisplayName(file_entry=file_entry)

    self.assertEqual(display_name, 'VSS2:TSK:/syslog.gz')

    # TODO: add test with relative path.

  def testGetDisplayNameForPathSpec(self):
    """Tests the GetDisplayNameForPathSpec function."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    test_file_path = self._GetTestFilePath(['syslog.gz'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

    expected_display_name = 'OS:{0:s}'.format(test_file_path)
    display_name = parser_mediator.GetDisplayNameForPathSpec(os_path_spec)
    self.assertEqual(display_name, expected_display_name)

  def testGetFileEntry(self):
    """Tests the GetFileEntry function."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    file_entry = parser_mediator.GetFileEntry()
    self.assertIsNone(file_entry)

  def testGetFilename(self):
    """Tests the GetFilename function."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    filename = parser_mediator.GetFilename()
    self.assertIsNone(filename)

  def testGetLanguageTag(self):
    """Tests the GetLanguageTag function."""
    parser_mediator = mediator.ParserMediator()

    language_tag = parser_mediator.GetLanguageTag()
    self.assertEqual(language_tag, 'en-us')

    # TODO: improve test coverage.

  # TODO: add tests for GetParserChain.
  # TODO: add tests for GetRelativePathForPathSpec.
  # TODO: add tests for PopFromParserChain.

  def testProduceEventData(self):
    """Tests the ProduceEventData method."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    storage_writer.Open()

    event_data_stream = events.EventDataStream()
    parser_mediator.ProduceEventDataStream(event_data_stream)

    event_data = events.EventData()
    event_data._parser_chain = 'test_parser'
    event_data.data_type = 'test'

    parser_mediator.ProduceEventData(event_data)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  # TODO: add tests for ProduceEventDataStream.
  # TODO: add tests for ProduceEventSource.

  def testProduceExtractionWarning(self):
    """Tests the ProduceExtractionWarning method."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    storage_writer.Open()

    parser_mediator.ProduceExtractionWarning('test')

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 1)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

  def testProduceRecoveryWarning(self):
    """Tests the ProduceRecoveryWarning method."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    storage_writer.Open()

    parser_mediator.ProduceRecoveryWarning('test')

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 1)

  def testResetFileEntry(self):
    """Tests the ResetFileEntry function."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    parser_mediator.ResetFileEntry()

  def testSetFileEntry(self):
    """Tests the SetFileEntry function."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    parser_mediator.SetFileEntry(None)

  def testSetStorageWriter(self):
    """Tests the SetStorageWriter function."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    parser_mediator.SetStorageWriter(None)

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    parser_mediator = mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    parser_mediator.SignalAbort()


if __name__ == '__main__':
  unittest.main()
