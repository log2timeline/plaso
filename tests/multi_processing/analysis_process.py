#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the multi-processing analysis process."""

import unittest

from plaso.multi_processing import analysis_process

from tests import test_lib as shared_test_lib


class AnalysisProcessTest(shared_test_lib.BaseTestCase):
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

  # TODO: add test for _Main.
  # TODO: add test for _ProcessEvent.

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    test_process = analysis_process.AnalysisProcess(
        None, None, None, None, name=u'TestAnalysis')
    test_process.SignalAbort()


if __name__ == '__main__':
  unittest.main()
