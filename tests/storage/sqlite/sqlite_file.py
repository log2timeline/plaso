#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SQLite-based storage."""

from __future__ import unicode_literals

import os
import unittest

from plaso.containers import events
from plaso.containers import event_sources
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.containers import warnings
from plaso.lib import definitions
from plaso.storage.sqlite import sqlite_file

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.storage import test_lib


class _TestSQLiteStorageFileV1(sqlite_file.SQLiteStorageFile):
  """Test class for testing format compatibility checks."""

  _FORMAT_VERSION = 1
  _COMPATIBLE_FORMAT_VERSION = 1


class _TestSQLiteStorageFileV2(sqlite_file.SQLiteStorageFile):
  """Test class for testing format compatibility checks."""

  _FORMAT_VERSION = 2
  _COMPATIBLE_FORMAT_VERSION = 1


class SQLiteStorageFileTest(test_lib.StorageTestCase):
  """Tests for the SQLite-based storage file object."""

  # pylint: disable=protected-access

  def testAddAttributeContainer(self):
    """Tests the _AddAttributeContainer function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file._AddAttributeContainer(
          storage_file._CONTAINER_TYPE_EVENT_DATA, event_data)

      storage_file.Close()

  def testAddSerializedEvent(self):
    """Tests the _AddSerializedEvent function."""
    event = events.EventObject()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file._AddSerializedEvent(event)

      storage_file.Close()

  def testCountStoredAttributeContainers(self):
    """Tests the _CountStoredAttributeContainers function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      number_of_containers = storage_file._GetNumberOfAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertEqual(number_of_containers, 0)

      storage_file._AddAttributeContainer(
          storage_file._CONTAINER_TYPE_EVENT_DATA, event_data)
      storage_file._WriteSerializedAttributeContainerList(
          storage_file._CONTAINER_TYPE_EVENT_DATA)

      number_of_containers = storage_file._GetNumberOfAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertEqual(number_of_containers, 1)

      with self.assertRaises(ValueError):
        storage_file._GetNumberOfAttributeContainers('bogus')

      # Test for a supported container type that does not have a table
      # present in the storage file.
      query = 'DROP TABLE {0:s}'.format(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      storage_file._cursor.execute(query)
      number_of_containers = storage_file._GetNumberOfAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertEqual(number_of_containers, 0)

      storage_file.Close()

  def testGetAttributeContainerByIndex(self):
    """Tests the _GetAttributeContainerByIndex function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      container = storage_file._GetAttributeContainerByIndex(
          storage_file._CONTAINER_TYPE_EVENT_DATA, 0)
      self.assertIsNone(container)

      storage_file._AddAttributeContainer(
          storage_file._CONTAINER_TYPE_EVENT_DATA, event_data)
      storage_file._WriteSerializedAttributeContainerList(
          storage_file._CONTAINER_TYPE_EVENT_DATA)

      container = storage_file._GetAttributeContainerByIndex(
          storage_file._CONTAINER_TYPE_EVENT_DATA, 0)
      self.assertIsNotNone(container)

      with self.assertRaises(IOError):
        storage_file._GetAttributeContainerByIndex('bogus', 0)

      storage_file.Close()

  def testGetAttributeContainers(self):
    """Tests the _GetAttributeContainers function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      containers = list(storage_file._GetAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA))
      self.assertEqual(len(containers), 0)

      storage_file._AddAttributeContainer(
          storage_file._CONTAINER_TYPE_EVENT_DATA, event_data)
      storage_file._WriteSerializedAttributeContainerList(
          storage_file._CONTAINER_TYPE_EVENT_DATA)

      containers = list(storage_file._GetAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA))
      self.assertEqual(len(containers), 1)

      with self.assertRaises(IOError):
        list(storage_file._GetAttributeContainers('bogus'))

      storage_file.Close()

  def testHasAttributeContainers(self):
    """Tests the _HasAttributeContainers function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      result = storage_file._HasAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertFalse(result)

      storage_file._AddAttributeContainer(
          storage_file._CONTAINER_TYPE_EVENT_DATA, event_data)
      storage_file._WriteSerializedAttributeContainerList(
          storage_file._CONTAINER_TYPE_EVENT_DATA)

      result = storage_file._HasAttributeContainers(
          storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertTrue(result)

      with self.assertRaises(ValueError):
        storage_file._HasAttributeContainers('bogus')

      storage_file.Close()

  def testHasTable(self):
    """Tests the _HasTable function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      result = storage_file._HasTable(storage_file._CONTAINER_TYPE_EVENT_DATA)
      self.assertTrue(result)

      result = storage_file._HasTable('bogus')
      self.assertFalse(result)

      storage_file.Close()

  # TODO: add tests for _ReadStorageMetadata

  def testWriteAttributeContainer(self):
    """Tests the _WriteAttributeContainer function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file._WriteAttributeContainer(event_data)

      storage_file.Close()

  def testWriteSerializedAttributeContainerList(self):
    """Tests the _WriteSerializedAttributeContainerList function."""
    event_data = events.EventData()
    event = events.EventObject()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file._AddAttributeContainer(
          storage_file._CONTAINER_TYPE_EVENT_DATA, event_data)
      storage_file._WriteSerializedAttributeContainerList(
          storage_file._CONTAINER_TYPE_EVENT_DATA)

      event.timestamp = 0x7fffffffffffffff

      storage_file._AddSerializedEvent(event)
      storage_file._WriteSerializedAttributeContainerList(
          storage_file._CONTAINER_TYPE_EVENT)

      event.timestamp = 0x8000000000000000

      storage_file._AddSerializedEvent(event)
      with self.assertRaises(OverflowError):
        storage_file._WriteSerializedAttributeContainerList(
            storage_file._CONTAINER_TYPE_EVENT)

      storage_file.Close()

  # TODO: add tests for _WriteStorageMetadata

  def testAddAnalysisReport(self):
    """Tests the AddAnalysisReport function."""
    analysis_report = reports.AnalysisReport(
        plugin_name='test', text='test report')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddAnalysisReport(analysis_report)

      storage_file.Close()

  def testAddEvent(self):
    """Tests the AddEvent function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event, event_data in containers_test_lib.CreateEventsFromValues(
          self._TEST_EVENTS):
        storage_file.AddEventData(event_data)

        event.SetEventDataIdentifier(event_data.GetIdentifier())
        storage_file.AddEvent(event)

      storage_file.Close()

  def testAddAddEventData(self):
    """Tests the AddAddEventData function."""
    event_data = events.EventData()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddEventData(event_data)

      storage_file.Close()

  def testAddEventSource(self):
    """Tests the AddEventSource function."""
    event_source = event_sources.EventSource()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddEventSource(event_source)

      storage_file.Close()

  def testAddEventTag(self):
    """Tests the AddEventTag function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      test_events = []
      for event, event_data in containers_test_lib.CreateEventsFromValues(
          self._TEST_EVENTS):
        storage_file.AddEventData(event_data)

        event.SetEventDataIdentifier(event_data.GetIdentifier())
        storage_file.AddEvent(event)

        test_events.append(event)

      test_event_tags = self._CreateTestEventTags(test_events)
      for event_tag in test_event_tags:
        storage_file.AddEventTag(event_tag)

      storage_file.Close()

  def testAddWarning(self):
    """Tests the AddWarning function."""
    extraction_warning = warnings.ExtractionWarning(
        message='Test extraction warning')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddWarning(extraction_warning)

      storage_file.Close()

  # TODO: add tests for CheckSupportedFormat

  def testGetAnalysisReports(self):
    """Tests the GetAnalysisReports function."""
    analysis_report = reports.AnalysisReport(
        plugin_name='test', text='test report')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddAnalysisReport(analysis_report)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_reports = list(storage_file.GetAnalysisReports())
      self.assertEqual(len(test_reports), 1)

      storage_file.Close()

  def testGetWarnings(self):
    """Tests the GetWarnings function."""
    extraction_warning = warnings.ExtractionWarning(
        message='Test extraction warning')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddWarning(extraction_warning)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_warnings = list(storage_file.GetWarnings())
      self.assertEqual(len(test_warnings), 1)

      storage_file.Close()

  def testExtractionErrorCompatibility(self):
    """Tests that extraction errors are converted to warnings."""
    extraction_error = warnings.ExtractionError(
        message='Test extraction error')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      # Directly using the private methods as AddError has been removed.
      storage_file._AddAttributeContainer(
          extraction_error.CONTAINER_TYPE, extraction_error)
      storage_file._WriteSerializedAttributeContainerList(
          extraction_error.CONTAINER_TYPE)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_warnings = list(storage_file.GetWarnings())
      self.assertEqual(len(test_warnings), 1)

      storage_file.Close()

  # TODO: add tests for GetEventData
  # TODO: add tests for GetEventDataByIdentifier

  def testGetEvents(self):
    """Tests the GetEvents function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event, event_data in containers_test_lib.CreateEventsFromValues(
          self._TEST_EVENTS):
        storage_file.AddEventData(event_data)

        event.SetEventDataIdentifier(event_data.GetIdentifier())
        storage_file.AddEvent(event)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_events = list(storage_file.GetEvents())
      self.assertEqual(len(test_events), 4)

      storage_file.Close()

  # TODO: add tests for GetEventSourceByIndex

  def testGetEventSources(self):
    """Tests the GetEventSources function."""
    event_source = event_sources.EventSource()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddEventSource(event_source)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_event_sources = list(storage_file.GetEventSources())
      self.assertEqual(len(test_event_sources), 1)

      storage_file.Close()

  def testGetEventTags(self):
    """Tests the GetEventTags function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      test_events = []
      for event, event_data in containers_test_lib.CreateEventsFromValues(
          self._TEST_EVENTS):
        storage_file.AddEventData(event_data)

        event.SetEventDataIdentifier(event_data.GetIdentifier())
        storage_file.AddEvent(event)

        test_events.append(event)

      test_event_tags = self._CreateTestEventTags(test_events)
      for event_tag in test_event_tags:
        storage_file.AddEventTag(event_tag)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_event_tags = list(storage_file.GetEventTags())
      self.assertEqual(len(test_event_tags), 4)

      storage_file.Close()

  # TODO: add tests for GetNumberOfAnalysisReports
  # TODO: add tests for GetNumberOfEventSources

  # TODO: add tests for GetSessions

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event, event_data in containers_test_lib.CreateEventsFromValues(
          self._TEST_EVENTS):
        storage_file.AddEventData(event_data)

        event.SetEventDataIdentifier(event_data.GetIdentifier())
        storage_file.AddEvent(event)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_events = list(storage_file.GetSortedEvents())
      self.assertEqual(len(test_events), 4)

      storage_file.Close()

    # TODO: add test with time range.

  # TODO: add tests for HasAnalysisReports
  # TODO: add tests for HasWarnings
  # TODO: add tests for HasEventTags

  # TODO: add tests for Open and Close

  # TODO: add tests for ReadPreprocessingInformation
  # TODO: add tests for WritePreprocessingInformation

  def testWriteSessionStartAndCompletion(self):
    """Tests the WriteSessionStart and WriteSessionCompletion functions."""
    session = sessions.Session()
    session_start = sessions.SessionStart(identifier=session.identifier)
    session_completion = sessions.SessionCompletion(
        identifier=session.identifier)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.WriteSessionStart(session_start)
      storage_file.WriteSessionCompletion(session_completion)

      storage_file.Close()

  def testWriteTaskStartAndCompletion(self):
    """Tests the WriteTaskStart and WriteTaskCompletion functions."""
    session = sessions.Session()
    task_start = tasks.TaskStart(session_identifier=session.identifier)
    task_completion = tasks.TaskCompletion(
        identifier=task_start.identifier,
        session_identifier=session.identifier)

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.WriteTaskStart(task_start)
      storage_file.WriteTaskCompletion(task_completion)

      storage_file.Close()

  def testVersionCompatibility(self):
    """Tests the version compatibility methods."""
    with shared_test_lib.TempDirectory() as temp_directory:
      v1_storage_path = os.path.join(temp_directory, 'v1.sqlite')
      v1_storage_file = _TestSQLiteStorageFileV1(
          storage_type=definitions.STORAGE_TYPE_SESSION)
      v1_storage_file.Open(path=v1_storage_path, read_only=False)
      v1_storage_file.Close()

      v2_storage_file_rw = _TestSQLiteStorageFileV2(
          storage_type=definitions.STORAGE_TYPE_SESSION)

      with self.assertRaises((IOError, OSError)):
        v2_storage_file_rw.Open(path=v1_storage_path, read_only=False)

      v2_storage_file_ro = _TestSQLiteStorageFileV2(
          storage_type=definitions.STORAGE_TYPE_SESSION)
      v2_storage_file_ro.Open(path=v1_storage_path, read_only=True)
      v2_storage_file_ro.Close()


# TODO: add tests for SQLiteStorageMergeReader
# TODO: add tests for SQLiteStorageFileReader
# TODO: add tests for SQLiteStorageFileWriter


if __name__ == '__main__':
  unittest.main()
