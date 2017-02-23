#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the multi-processing worker process."""

import unittest

from plaso.multi_processing import worker_process

from tests import test_lib as shared_test_lib


class WorkerProcessTest(shared_test_lib.BaseTestCase):
  """Tests the multi-processing worker process."""

  # pylint: disable=protected-access

  def testInitialization(self):
    """Tests the initialization."""
    test_process = worker_process.WorkerProcess(
        None, None, None, None, None, name=u'TestWorker')
    self.assertIsNotNone(test_process)

  def testGetStatus(self):
    """Tests the _GetStatus function."""
    test_process = worker_process.WorkerProcess(
        None, None, None, None, None, name=u'TestWorker')
    status_attributes = test_process._GetStatus()

    self.assertIsNotNone(status_attributes)
    self.assertEqual(status_attributes[u'identifier'], u'TestWorker')

  # TODO: add test for _Main.
  # TODO: add test for _ProcessPathSpec.
  # TODO: add test for _ProcessTask.
  # TODO: add test for _StartProfiling.
  # TODO: add test for _StopProfiling.

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    test_process = worker_process.WorkerProcess(
        None, None, None, None, None, name=u'TestWorker')
    test_process.SignalAbort()


if __name__ == '__main__':
  unittest.main()
