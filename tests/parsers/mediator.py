#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the parsers mediator."""

import unittest

from dfdatetime import fake_time

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import events
from plaso.containers import sessions
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.engine import knowledge_base
from plaso.parsers import mediator
from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class ParsersMediatorTest(test_lib.ParserTestCase):
  """Tests for the parsers mediator."""

  # pylint: disable=protected-access

  def testGetEarliestYearFromFileEntry(self):
    """Tests the _GetEarliestYearFromFileEntry function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    earliest_year = parser_mediator._GetEarliestYearFromFileEntry()
    self.assertIsNone(earliest_year)

    # TODO: improve test coverage.

  def testGetLatestYearFromFileEntry(self):
    """Tests the _GetLatestYearFromFileEntry function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    latest_year = parser_mediator._GetLatestYearFromFileEntry()
    self.assertIsNone(latest_year)

    # TODO: improve test coverage.

  # TODO: add tests for AddEventAttribute.
  # TODO: add tests for AppendToParserChain.
  # TODO: add tests for ClearEventAttributes.
  # TODO: add tests for ClearParserChain.

  def testGetDisplayName(self):
    """Tests the GetDisplayName function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

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

    expected_display_name = 'VSS2:TSK:/syslog.gz'
    self.assertEqual(display_name, expected_display_name)

    knowledge_base_object.SetTextPrepend('C:')

    display_name = parser_mediator.GetDisplayName(file_entry=file_entry)
    expected_display_name = 'VSS2:TSK:C:/syslog.gz'
    self.assertEqual(display_name, expected_display_name)

    # TODO: add test with relative path.

  def testGetDisplayNameForPathSpec(self):
    """Tests the GetDisplayNameForPathSpec function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    test_file_path = self._GetTestFilePath(['syslog.gz'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

    expected_display_name = 'OS:{0:s}'.format(test_file_path)
    display_name = parser_mediator.GetDisplayNameForPathSpec(os_path_spec)
    self.assertEqual(display_name, expected_display_name)

  def testGetEstimatedYear(self):
    """Tests the GetEstimatedYear function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    expected_estimated_year = parser_mediator.GetCurrentYear()
    estimated_year = parser_mediator.GetEstimatedYear()
    self.assertEqual(estimated_year, expected_estimated_year)

    # TODO: improve test coverage.

  def testGetFileEntry(self):
    """Tests the GetFileEntry function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    file_entry = parser_mediator.GetFileEntry()
    self.assertIsNone(file_entry)

  def testGetFilename(self):
    """Tests the GetFilename function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    filename = parser_mediator.GetFilename()
    self.assertIsNone(filename)

  def testGetLatestYear(self):
    """Tests the GetLatestYear function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    expected_latest_year = parser_mediator.GetCurrentYear()
    latest_year = parser_mediator.GetLatestYear()
    self.assertEqual(latest_year, expected_latest_year)

  # TODO: add tests for GetParserChain.
  # TODO: add tests for GetRelativePathForPathSpec.
  # TODO: add tests for PopFromParserChain.
  # TODO: add tests for ProcessEvent.
  # TODO: add tests for ProduceEventSource.

  def testProduceEventWithEventData(self):
    """Tests the ProduceEventWithEventData method."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    storage_writer.Open()

    event_data_stream = events.EventDataStream()
    parser_mediator.ProduceEventDataStream(event_data_stream)

    date_time = fake_time.FakeTime()
    event_with_timestamp = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
    event_with_timestamp.parser = 'test_parser'
    event_data = events.EventData()
    event_data.parser = 'test_parser'

    parser_mediator.ProduceEventWithEventData(event_with_timestamp, event_data)
    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    event_without_timestamp = events.EventObject()
    event_without_timestamp.parser = 'test_parser'
    with self.assertRaises(errors.InvalidEvent):
      parser_mediator.ProduceEventWithEventData(
          event_without_timestamp, event_data)

  # TODO: add tests for ProduceExtractionWarning.
  # TODO: add tests for RemoveEventAttribute.

  def testResetFileEntry(self):
    """Tests the ResetFileEntry function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    parser_mediator.ResetFileEntry()

  def testSetFileEntry(self):
    """Tests the SetFileEntry function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    parser_mediator.SetFileEntry(None)

  def testSetStorageWriter(self):
    """Tests the SetStorageWriter function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    parser_mediator.SetStorageWriter(None)

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    parser_mediator.SignalAbort()


if __name__ == '__main__':
  unittest.main()
