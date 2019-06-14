#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the fake storage."""

from __future__ import unicode_literals

import unittest

from plaso.containers import event_sources
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.containers import warnings
from plaso.lib import definitions
from plaso.storage.fake import writer as fake_writer

from tests.storage import test_lib
from tests.containers import test_lib as containers_test_lib


class FakeStorageWriterTest(test_lib.StorageTestCase):
  """Tests for the fake storage writer object."""

  def testAddAnalysisReport(self):
    """Tests the AddAnalysisReport function."""
    session = sessions.Session()
    analysis_report = reports.AnalysisReport(
        plugin_name='test', text='test report')

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    storage_writer.AddAnalysisReport(analysis_report)

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.AddAnalysisReport(analysis_report)

  def testAddEvent(self):
    """Tests the AddEvent function."""
    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    event = None
    for event, event_data in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      storage_writer.AddEventData(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_writer.AddEvent(event)

    storage_writer.Close()

    # Test writing an event twice.
    with self.assertRaises(IOError):
      storage_writer.AddEvent(event)

  def testAddEventSource(self):
    """Tests the AddEventSource function."""
    session = sessions.Session()
    event_source = event_sources.EventSource()

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    storage_writer.AddEventSource(event_source)

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.AddEventSource(event_source)

  def testAddEventTag(self):
    """Tests the AddEventTag function."""
    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    test_events = []
    for event, event_data in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      storage_writer.AddEventData(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_writer.AddEvent(event)

      test_events.append(event)

    event_tag = None
    test_event_tags = self._CreateTestEventTags(test_events)
    for event_tag in test_event_tags:
      storage_writer.AddEventTag(event_tag)

    storage_writer.Close()

    # Test writing an event tag twice.
    with self.assertRaises(IOError):
      storage_writer.AddEventTag(event_tag)

  def testAddWarning(self):
    """Tests the AddWarning function."""
    session = sessions.Session()
    warning = warnings.ExtractionWarning(
        message='Test extraction error')

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    storage_writer.AddWarning(warning)

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.AddWarning(warning)

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()
    storage_writer.Close()

    storage_writer.Open()
    storage_writer.Close()

    storage_writer = fake_writer.FakeStorageWriter(
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

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    for event, event_data in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      storage_writer.AddEventData(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_writer.AddEvent(event)

    test_events = list(storage_writer.GetEvents())
    self.assertEqual(len(test_events), 4)

    storage_writer.Close()

  # TODO: add tests for GetEventSources.
  # TODO: add tests for GetEventTags.
  # TODO: add tests for GetFirstWrittenEventSource and
  # GetNextWrittenEventSource.

  def testGetSortedEvents(self):
    """Tests the GetSortedEvents function."""
    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    for event, event_data in containers_test_lib.CreateEventsFromValues(
        self._TEST_EVENTS):
      storage_writer.AddEventData(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_writer.AddEvent(event)

    test_events = list(storage_writer.GetSortedEvents())
    self.assertEqual(len(test_events), 4)

    storage_writer.Close()

    # TODO: add test with time range.

  def testWriteSessionStartAndCompletion(self):
    """Tests the WriteSessionStart and WriteSessionCompletion functions."""
    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    storage_writer.WriteSessionStart()
    storage_writer.WriteSessionCompletion()

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.WriteSessionStart()

    with self.assertRaises(IOError):
      storage_writer.WriteSessionCompletion()

    storage_writer = fake_writer.FakeStorageWriter(
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

    storage_writer = fake_writer.FakeStorageWriter(
        session, storage_type=definitions.STORAGE_TYPE_TASK, task=task)
    storage_writer.Open()

    storage_writer.WriteTaskStart()
    storage_writer.WriteTaskCompletion()

    storage_writer.Close()

    with self.assertRaises(IOError):
      storage_writer.WriteTaskStart()

    with self.assertRaises(IOError):
      storage_writer.WriteTaskCompletion()

    storage_writer = fake_writer.FakeStorageWriter(session)
    storage_writer.Open()

    with self.assertRaises(IOError):
      storage_writer.WriteTaskStart()

    with self.assertRaises(IOError):
      storage_writer.WriteTaskCompletion()

    storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
