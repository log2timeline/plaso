#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the multi-processing analysis process."""

import unittest

from plaso.analysis import interface as analysis_interface
from plaso.containers import sessions
from plaso.multi_processing import analysis_process
from plaso.multi_processing import multi_process_queue

from tests.multi_processing import test_lib


class TestAnalysisPlugin(analysis_interface.AnalysisPlugin):
  """Analysis plugin for testing."""

  NAME = 'test_plugin'

  def CompileReport(self, unused_mediator):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to
    analyze this function will be called so that the report
    can be assembled.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: analysis report.
    """
    return

  def ExamineEvent(self, unused_mediator, unused_event, **unused_kwargs):
    """Analyzes an event.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
    """
    return


class AnalysisProcessTest(test_lib.MultiProcessingTestCase):
  """Tests the multi-processing analysis process."""

  # pylint: disable=protected-access

  def testInitialization(self):
    """Tests the initialization."""
    test_process = analysis_process.AnalysisProcess(
        None, None, None, None, name=u'TestAnalysis')
    self.assertIsNotNone(test_process)

  def testGetStatus(self):
    """Tests the _GetStatus function."""
    test_process = analysis_process.AnalysisProcess(
        None, None, None, None, name=u'TestAnalysis')
    status_attributes = test_process._GetStatus()

    self.assertIsNotNone(status_attributes)
    self.assertEqual(status_attributes[u'identifier'], u'TestAnalysis')
    self.assertIsNone(status_attributes['number_of_produced_reports'])

    # TODO: add test with analysis mediator.

  def testMain(self):
    """Tests the _Main function."""
    event_queue = multi_process_queue.MultiProcessingQueue(timeout=1)

    session = sessions.Session()
    storage_writer = self._CreateStorageWriter(session)
    analysis_plugin = TestAnalysisPlugin()

    test_process = analysis_process.AnalysisProcess(
        event_queue, storage_writer, None, analysis_plugin,
        name=u'TestAnalysis')
    test_process._abort = True
    test_process._FOREMAN_STATUS_WAIT = 1
    test_process._pid = 0

    test_process._Main()

  # TODO: add test for _ProcessEvent.

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    test_process = analysis_process.AnalysisProcess(
        None, None, None, None, name=u'TestAnalysis')
    test_process.SignalAbort()


if __name__ == '__main__':
  unittest.main()
