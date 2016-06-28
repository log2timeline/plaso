#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the fake storage."""

import unittest
import uuid

from plaso.containers import errors
from plaso.containers import event_sources
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage import fake_storage
from plaso.storage import zip_file

from tests.storage import test_lib


class FakeStorageWriterTest(test_lib.StorageTestCase):
  """Tests for the fake storage writer object."""

  def testAddAnalysisReport(self):
    """Tests the AddAnalysisReport function."""
    analysis_report = reports.AnalysisReport(
        plugin_name=u'test', text=u'test report')

    storage_writer = fake_storage.FakeStorageWriter()
    storage_writer.Open()

    storage_writer.AddAnalysisReport(analysis_report)

    storage_writer.Close()

  def testAddError(self):
    """Tests the AddError function."""
    extraction_error = errors.ExtractionError(u'Test extraction error')

    storage_writer = fake_storage.FakeStorageWriter()
    storage_writer.Open()

    storage_writer.AddError(extraction_error)

    storage_writer.Close()

  def testAddEvent(self):
    """Tests the AddEvent function."""
    event_objects = self._CreateTestEventObjects()

    storage_writer = fake_storage.FakeStorageWriter()
    storage_writer.Open()

    for event_object in event_objects:
      storage_writer.AddEvent(event_object)

    storage_writer.Close()

  def testAddEventSource(self):
    """Tests the AddEventSource function."""
    event_source = event_sources.EventSource()

    storage_writer = fake_storage.FakeStorageWriter()
    storage_writer.Open()

    storage_writer.AddEventSource(event_source)

    storage_writer.Close()

  def testAddEventTag(self):
    """Tests the AddEventTag function."""
    event_objects = self._CreateTestEventObjects()
    event_tags = self._CreateTestEventTags()

    storage_writer = fake_storage.FakeStorageWriter()
    storage_writer.Open()

    for event_object in event_objects:
      storage_writer.AddEvent(event_object)

    for event_tag in event_tags:
      storage_writer.AddEventTag(event_tag)

    storage_writer.Close()

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    storage_writer = fake_storage.FakeStorageWriter()
    storage_writer.Open()
    storage_writer.Close()

    storage_writer.Open()
    storage_writer.Close()

    storage_writer = fake_storage.FakeStorageWriter(
        storage_type=definitions.STORAGE_TYPE_TASK)
    storage_writer.Open()
    storage_writer.Close()

    storage_writer.Open()
    storage_writer.Close()

  # TODO: add test for GetEventSources.

  def testMergeFromStorage(self):
    """Tests the MergeFromStorage function."""
    storage_writer = fake_storage.FakeStorageWriter()
    storage_writer.Open()

    test_file = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_reader = zip_file.ZIPStorageFileReader(test_file)
    storage_writer.MergeFromStorage(storage_reader)

    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])
    storage_reader = zip_file.ZIPStorageFileReader(test_file)
    storage_writer.MergeFromStorage(storage_reader)

    storage_writer.Close()

  def testWriteSessionStartAndCompletion(self):
    """Tests the WriteSessionStart and WriteSessionCompletion functions."""
    session_start = sessions.SessionStart()

    storage_writer = fake_storage.FakeStorageWriter()
    storage_writer.Open()

    storage_writer.WriteSessionStart(session_start)
    storage_writer.WriteSessionCompletion()

    storage_writer.Close()

    storage_writer = fake_storage.FakeStorageWriter(
        storage_type=definitions.STORAGE_TYPE_TASK)
    storage_writer.Open()

    with self.assertRaises(IOError):
      storage_writer.WriteSessionStart(session_start)

    with self.assertRaises(IOError):
      storage_writer.WriteSessionCompletion()

    storage_writer.Close()

  def testWriteTaskStartAndCompletion(self):
    """Tests the WriteTaskStart and WriteTaskCompletion functions."""
    session_identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    task_start = tasks.TaskStart(session_identifier=session_identifier)

    storage_writer = fake_storage.FakeStorageWriter(
        storage_type=definitions.STORAGE_TYPE_TASK)
    storage_writer.Open()

    storage_writer.WriteTaskStart(task_start)
    storage_writer.WriteTaskCompletion()

    storage_writer.Close()

    storage_writer = fake_storage.FakeStorageWriter()
    storage_writer.Open()

    with self.assertRaises(IOError):
      storage_writer.WriteTaskStart(task_start)

    with self.assertRaises(IOError):
      storage_writer.WriteTaskCompletion()

    storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
