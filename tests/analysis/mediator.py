#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the analysis mediator."""

import unittest

from plaso.analysis import mediator
from plaso.engine import plaso_queue
from plaso.engine import single_process

from tests.analysis import test_lib


class AnalysisMediatorTest(test_lib.AnalysisPluginTestCase):
  """Tests for the analysis mediator."""

  def testInitialize(self):
    """Tests the __init__ function."""
    knowledge_base = self._SetUpKnowledgeBase()

    analysis_report_queue = single_process.SingleProcessQueue()
    analysis_report_queue_producer = plaso_queue.ItemQueueProducer(
        analysis_report_queue)

    mediator.AnalysisMediator(analysis_report_queue_producer, knowledge_base)

  # TODO: add test for GetDisplayName.
  # TODO: add test for GetRelativePath.
  # TODO: add test for GetUsernameForPath.
  # TODO: add test for ProcessAnalysisReport.
  # TODO: add test for ProduceAnalysisReport.
  # TODO: add test for ReportingComplete.


if __name__ == '__main__':
  unittest.main()
