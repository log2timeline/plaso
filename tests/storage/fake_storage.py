#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the fake storage."""

import unittest

from plaso.containers import sessions
from plaso.storage import fake_storage

from tests import test_lib as shared_test_lib
from tests.storage import test_lib


class FakeStorageWriterTest(shared_test_lib.BaseTestCase):
  """Tests for the fake storage writer object."""

  # TODO: add test for AddAnalysisReport.
  # TODO: add test for AddEvent.
  # TODO: add test for AddEventSource.
  # TODO: add test for AddEventTag.
  # TODO: add test for Open/Close.
  # TODO: add test for GetEventSources.
  # TODO: add test for WriteSessionCompletion.
  # TODO: add test for WriteSessionStart.

  def testStorageWriter(self):
    """Test the storage writer."""
    event_objects = test_lib.CreateTestEventObjects()
    session_start = sessions.SessionStart()

    storage_writer = fake_storage.FakeStorageWriter()

    storage_writer.Open()
    storage_writer.WriteSessionStart(session_start)

    for event_object in event_objects:
      storage_writer.AddEvent(event_object)

    storage_writer.WriteSessionCompletion()
    storage_writer.Close()

    self.assertEqual(len(storage_writer.analysis_reports), 0)
    self.assertEqual(len(storage_writer.event_sources), 0)
    self.assertEqual(len(storage_writer.event_tags), 0)
    self.assertEqual(len(storage_writer.events), 4)

    self.assertIsNotNone(storage_writer.session_start)
    self.assertEqual(
        session_start.identifier, storage_writer.session_start.identifier)

    self.assertIsNotNone(storage_writer.session_completion)
    self.assertEqual(
        session_start.identifier, storage_writer.session_completion.identifier)


if __name__ == '__main__':
  unittest.main()
