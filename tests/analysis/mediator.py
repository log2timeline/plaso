#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the analysis mediator."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.analysis import mediator
from plaso.containers import artifacts

from tests.analysis import test_lib


class AnalysisMediatorTest(test_lib.AnalysisPluginTestCase):
  """Tests for the analysis mediator."""

  def testGetDisplayNameForPathSpec(self):
    """Tests the GetDisplayNameForPathSpec function."""
    analysis_mediator = mediator.AnalysisMediator()

    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    expected_display_name = 'OS:{0:s}'.format(test_path)
    display_name = analysis_mediator.GetDisplayNameForPathSpec(os_path_spec)
    self.assertEqual(display_name, expected_display_name)

  def testGetUsernameForPath(self):
    """Tests the GetUsernameForPath function."""
    test_user1 = artifacts.UserAccountArtifact(
        identifier='1000', path_separator='\\',
        user_directory='C:\\Users\\testuser1',
        username='testuser1')

    analysis_mediator = mediator.AnalysisMediator(user_accounts=[test_user1])

    username = analysis_mediator.GetUsernameForPath(
        'C:\\Users\\testuser1\\Downloads')
    self.assertEqual(username, 'testuser1')

    username = analysis_mediator.GetUsernameForPath(
        'C:\\Users\\testuser2\\Downloads')
    self.assertIsNone(username)

  # TODO: add test for ProduceAnalysisReport.
  # TODO: add test for ProduceEventTag.

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    analysis_mediator = mediator.AnalysisMediator()

    analysis_mediator.SignalAbort()


if __name__ == '__main__':
  unittest.main()
