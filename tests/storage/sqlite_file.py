#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SQLite-based storage."""

import os
import unittest

from plaso.containers import errors
from plaso.containers import event_sources
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage import sqlite_file

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


class SQLiteStorageFileTest(test_lib.StorageTestCase):
  """Tests for the SQLite-based storage file object."""

  # pylint: disable=protected-access

  # TODO: add tests for _AddAttributeContainer
  # TODO: add tests for _GetAttributeContainer
  # TODO: add tests for _HasTable
  # TODO: add tests for _WriteAttributeContainer
  # TODO: add tests for _WriteStorageMetadata

  def testAddAnalysisReport(self):
    """Tests the AddAnalysisReport function."""
    analysis_report = reports.AnalysisReport(
        plugin_name=u'test', text=u'test report')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddAnalysisReport(analysis_report)

      storage_file.Close()

  def testAddError(self):
    """Tests the AddError function."""
    extraction_error = errors.ExtractionError(
        message=u'Test extraction error')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddError(extraction_error)

      storage_file.Close()

  def testAddEvent(self):
    """Tests the AddEvent function."""
    test_events = self._CreateTestEvents()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event in test_events:
        storage_file.AddEvent(event)

      storage_file.Close()

  def testAddEventSource(self):
    """Tests the AddEventSource function."""
    event_source = event_sources.EventSource()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddEventSource(event_source)

      storage_file.Close()

  def testAddEventTag(self):
    """Tests the AddEventTag function."""
    test_events = self._CreateTestEvents()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event in test_events:
        storage_file.AddEvent(event)

      test_event_tags = self._CreateTestEventTags(test_events)
      for event_tag in test_event_tags:
        storage_file.AddEventTag(event_tag)

      storage_file.Close()

  # TODO: add tests for CheckSupportedFormat

  def testGetAnalysisReports(self):
    """Tests the GetAnalysisReports function."""
    analysis_report = reports.AnalysisReport(
        plugin_name=u'test', text=u'test report')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddAnalysisReport(analysis_report)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_reports = list(storage_file.GetAnalysisReports())
      self.assertEqual(len(test_reports), 1)

      storage_file.Close()

  def testGetErrors(self):
    """Tests the GetErrors function."""
    extraction_error = errors.ExtractionError(
        message=u'Test extraction error')

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.AddError(extraction_error)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_errors = list(storage_file.GetErrors())
      self.assertEqual(len(test_errors), 1)

      storage_file.Close()

  def testGetEvents(self):
    """Tests the GetEvents function."""
    test_events = self._CreateTestEvents()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event in test_events:
        storage_file.AddEvent(event)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_events = list(storage_file.GetEvents())
      self.assertEqual(len(test_events), 4)

      storage_file.Close()

  def testGetEventSources(self):
    """Tests the GetEventSources function."""
    event_source = event_sources.EventSource()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
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
    test_events = self._CreateTestEvents()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event in test_events:
        storage_file.AddEvent(event)

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
    test_events = self._CreateTestEvents()

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file, read_only=False)

      for event in test_events:
        storage_file.AddEvent(event)

      storage_file.Close()

      storage_file = sqlite_file.SQLiteStorageFile()
      storage_file.Open(path=temp_file)

      test_events = list(storage_file.GetSortedEvents())
      self.assertEqual(len(test_events), 4)

      storage_file.Close()

    # TODO: add test with time range.

  # TODO: add tests for HasAnalysisReports
  # TODO: add tests for HasErrors
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
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
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
      temp_file = os.path.join(temp_directory, u'plaso.sqlite')
      storage_file = sqlite_file.SQLiteStorageFile(
          storage_type=definitions.STORAGE_TYPE_TASK)
      storage_file.Open(path=temp_file, read_only=False)

      storage_file.WriteTaskStart(task_start)
      storage_file.WriteTaskCompletion(task_completion)

      storage_file.Close()


# TODO: add tests for SQLiteStorageMergeReader
# TODO: add tests for SQLiteStorageFileReader
# TODO: add tests for SQLiteStorageFileWriter


if __name__ == '__main__':
  unittest.main()
