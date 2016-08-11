#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the multi-processing base process."""

import unittest

from plaso.multi_processing import base_process

from tests import test_lib as shared_test_lib


class TestProcess(base_process.MultiProcessBaseProcess):
  """Implementation of the multi-processing base process for testing."""


class MultiProcessBaseProcessTest(shared_test_lib.BaseTestCase):
  """Tests the multi-processing base process."""

  # pylint: disable=protected-access

  def testInitialization(self):
    """Tests the initialization."""
    test_process = TestProcess(name=u'TestBase')
    self.assertIsNotNone(test_process)

  # TODO: add test for name property.
  # TODO: add test for _OnCriticalError.
  # TODO: add test for _SigSegvHandler.
  # TODO: add test for _SigTermHandler.
  # TODO: add test for _StartProcessStatusRPCServer.
  # TODO: add test for _StopProcessStatusRPCServer.
  # TODO: add test for _WaitForStatusNotRunning.
  # TODO: add test for run.


if __name__ == '__main__':
  unittest.main()
