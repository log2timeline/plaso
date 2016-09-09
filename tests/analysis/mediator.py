#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the analysis mediator."""

import unittest

from plaso.analysis import mediator
from plaso.containers import sessions
from plaso.storage import fake_storage

from tests.analysis import test_lib


class AnalysisMediatorTest(test_lib.AnalysisPluginTestCase):
  """Tests for the analysis mediator."""

  def testInitialize(self):
    """Tests the __init__ function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    knowledge_base = self._SetUpKnowledgeBase()

    mediator.AnalysisMediator(storage_writer, knowledge_base)

  # TODO: add test for GetDisplayName.
  # TODO: add test for GetRelativePath.
  # TODO: add test for GetUsernameForPath.
  # TODO: add test for ProduceAnalysisReport.
  # TODO: add test for ReportingComplete.


if __name__ == '__main__':
  unittest.main()
