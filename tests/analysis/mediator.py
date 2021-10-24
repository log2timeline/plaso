#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the analysis mediator."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.analysis import mediator
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

    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    expected_display_name = 'OS:{0:s}'.format(test_path)
    display_name = analysis_mediator.GetDisplayNameForPathSpec(os_path_spec)
    self.assertEqual(display_name, expected_display_name)

  # TODO: add test for GetUsernameForPath.
  # TODO: add test for ProduceAnalysisReport.
  # TODO: add test for ProduceEventTag.

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter()
    knowledge_base = self._SetUpKnowledgeBase()

    analysis_mediator = mediator.AnalysisMediator(session, knowledge_base)
    analysis_mediator.SetStorageWriter(storage_writer)

    analysis_mediator.SignalAbort()


if __name__ == '__main__':
  unittest.main()
