#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the fake storage."""

import unittest

from plaso.containers import errors
from plaso.containers import event_sources
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.lib import definitions
from plaso.storage import fake_storage
from plaso.storage import zip_file

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


# TODO: add tests for _EventsHeap


class FakeStorageWriterTest(test_lib.StorageTestCase):
  """Tests for the fake storage writer object."""

  def testAddAnalysisReport(self):
    """Tests the AddAnalysisReport function."""
    session = sessions.Session()
    analysis_report = reports.AnalysisReport(
        plugin_name=u'test', text=u'test report')

    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    storage_writer.AddAnalysisReport(analysis_report)

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.AddAnalysisReport(analysis_report)

  def testAddError(self):
    """Tests the AddError function."""
    session = sessions.Session()
    extraction_error = errors.ExtractionError(
        message=u'Test extraction error')

    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    storage_writer.AddError(extraction_error)

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.AddError(extraction_error)

  def testAddEvent(self):
    """Tests the AddEvent function."""
    session = sessions.Session()
    test_events = self._CreateTestEvents()

    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    event = None
    for event in test_events:
      storage_writer.AddEvent(event)

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.AddEvent(event)

  def testAddEventSource(self):
    """Tests the AddEventSource function."""
    session = sessions.Session()
    event_source = event_sources.EventSource()

    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    storage_writer.AddEventSource(event_source)

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.AddEventSource(event_source)

  def testAddEventTag(self):
    """Tests the AddEventTag function."""
    session = sessions.Session()

    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    test_events = self._CreateTestEvents()
    for event in test_events:
      storage_writer.AddEvent(event)

    event_tag = None
    test_event_tags = self._CreateTestEventTags(test_events)
    for event_tag in test_event_tags:
      storage_writer.AddEventTag(event_tag)

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.AddEventTag(event_tag)

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()
    storage_writer.Close()

    storage_writer.Open()
    storage_writer.Close()

    storage_writer = fake_storage.FakeStorageWriter(
        session, storage_type=definitions.STORAGE_TYPE_TASK)
    storage_writer.Open()
    storage_writer.Close()

    storage_writer.Open()

    with self.assertRaises(IOError):
      storage_writer.Open()

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.Close()

  def testGetEvents(self):
    """Tests the GetEvents function."""
    session = sessions.Session()
    test_events = self._CreateTestEvents()

    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    event = None
    for event in test_events:
      storage_writer.AddEvent(event)

    events = list(storage_writer.GetEvents())
    self.assertEqual(len(events), len(test_events))

    storage_writer.Close()

  # TODO: add tests for GetEventSources.
  # TODO: add tests for GetEventTags.
  # TODO: add tests for GetFirstWrittenEventSource and
  # GetNextWrittenEventSource.

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents function."""
    session = sessions.Session()
    test_events = self._CreateTestEvents()

    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    event = None
    for event in test_events:
      storage_writer.AddEvent(event)

    events = list(storage_writer.GetSortedEvents())
    self.assertEqual(len(events), len(test_events))

    storage_writer.Close()

    # TODO: add test with time range.

  @shared_test_lib.skipUnlessHasTestFile([u'psort_test.json.plaso'])
  @shared_test_lib.skipUnlessHasTestFile([u'pinfo_test.json.plaso'])
  def testMergeFromStorage(self):
    """Tests the MergeFromStorage function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
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
    session = sessions.Session()

    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    storage_writer.WriteSessionStart()
    storage_writer.WriteSessionCompletion()

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.WriteSessionStart()

    with self.assertRaises(IOError):
      storage_writer.WriteSessionCompletion()

    storage_writer = fake_storage.FakeStorageWriter(
        session, storage_type=definitions.STORAGE_TYPE_TASK)
    storage_writer.Open()

    with self.assertRaises(IOError):
      storage_writer.WriteSessionStart()

    with self.assertRaises(IOError):
      storage_writer.WriteSessionCompletion()

    storage_writer.Close()

  def testWriteTaskStartAndCompletion(self):
    """Tests the WriteTaskStart and WriteTaskCompletion functions."""
    session = sessions.Session()
    task = tasks.Task(session_identifier=session.identifier)

    storage_writer = fake_storage.FakeStorageWriter(
        session, storage_type=definitions.STORAGE_TYPE_TASK, task=task)
    storage_writer.Open()

    storage_writer.WriteTaskStart()
    storage_writer.WriteTaskCompletion()

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.WriteTaskStart()

    with self.assertRaises(IOError):
      storage_writer.WriteTaskCompletion()

    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    with self.assertRaises(IOError):
      storage_writer.WriteTaskStart()

    with self.assertRaises(IOError):
      storage_writer.WriteTaskCompletion()

    storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
