#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the analysis mediator."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.analysis import mediator
from plaso.containers import artifacts
from plaso.containers import sessions
from plaso.storage.fake import writer as fake_writer

from tests.analysis import test_lib


class AnalysisMediatorTest(test_lib.AnalysisPluginTestCase):
  """Tests for the analysis mediator."""

  def testGetDisplayNameForPathSpec(self):
    """Tests the GetDisplayNameForPathSpec function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base = self._SetUpKnowledgeBase()

    analysis_mediator = mediator.AnalysisMediator(session, knowledge_base)
    analysis_mediator.SetStorageWriter(storage_writer)

    storage_writer.Open()

    try:
      test_path = self._GetTestFilePath(['syslog.gz'])
      os_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

      expected_display_name = 'OS:{0:s}'.format(test_path)
      display_name = analysis_mediator.GetDisplayNameForPathSpec(os_path_spec)
      self.assertEqual(display_name, expected_display_name)

    finally:
      storage_writer.Close()

  def testGetUsernameForPath(self):
    """Tests the GetUsernameForPath function."""
    test_user1 = artifacts.UserAccountArtifact(
        identifier='1000', path_separator='\\',
        user_directory='C:\\Users\\testuser1',
        username='testuser1')

    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base = self._SetUpKnowledgeBase()

    analysis_mediator = mediator.AnalysisMediator(session, knowledge_base)
    analysis_mediator.SetStorageWriter(storage_writer)

    storage_writer.Open()

    try:
      storage_writer.AddAttributeContainer(test_user1)

      username = analysis_mediator.GetUsernameForPath(
          'C:\\Users\\testuser1\\Downloads')
      self.assertEqual(username, 'testuser1')

      username = analysis_mediator.GetUsernameForPath(
          'C:\\Users\\testuser2\\Downloads')
      self.assertIsNone(username)

    finally:
      storage_writer.Close()

  # TODO: add test for ProduceAnalysisReport.
  # TODO: add test for ProduceEventTag.

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base = self._SetUpKnowledgeBase()

    analysis_mediator = mediator.AnalysisMediator(session, knowledge_base)
    analysis_mediator.SetStorageWriter(storage_writer)

    storage_writer.Open()

    try:
      analysis_mediator.SignalAbort()

    finally:
      storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
