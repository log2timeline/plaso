#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows EventLog providers helper."""

import unittest

from plaso.helpers.windows import eventlog_providers

from tests import test_lib as shared_test_lib


class WindowsEventLogProvidersHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows EventLog providers helper."""

  # pylint: disable=protected-access

  def testGetNormalizedPath(self):
    """Tests the _GetNormalizedPath function."""
    test_helper = eventlog_providers.WindowsEventLogProvidersHelper()

    normalized_path = test_helper._GetNormalizedPath(
        '%SystemRoot%\\System32\\IoLogMsg.dll')
    self.assertEqual(normalized_path, '%SystemRoot%\\System32\\IoLogMsg.dll')

    normalized_path = test_helper._GetNormalizedPath(
        '%windir%\\System32\\lsasrv.dll')
    self.assertEqual(normalized_path, '%SystemRoot%\\System32\\lsasrv.dll')

    normalized_path = test_helper._GetNormalizedPath(
        'C:\\Windows\\System32\\mscoree.dll')
    self.assertEqual(normalized_path, '%SystemRoot%\\System32\\mscoree.dll')

    normalized_path = test_helper._GetNormalizedPath(
        'werfault.exe')
    self.assertEqual(normalized_path, '%SystemRoot%\\System32\\werfault.exe')

    normalized_path = test_helper._GetNormalizedPath(
        'system32\\drivers\\WdFilter.sys')
    self.assertEqual(normalized_path, (
        '%SystemRoot%\\System32\\drivers\\WdFilter.sys'))

    normalized_path = test_helper._GetNormalizedPath(
        'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\84.0.522.52\\'
        'eventlog_provider.dll')
    self.assertEqual(normalized_path, (
        '\\Program Files (x86)\\Microsoft\\Edge\\Application\\84.0.522.52\\'
        'eventlog_provider.dll'))

    normalized_path = test_helper._GetNormalizedPath(
        '%ProgramFiles%\\Windows Defender\\MpClient.dll')
    self.assertEqual(normalized_path, (
        '%ProgramFiles%\\Windows Defender\\MpClient.dll'))

    normalized_path = test_helper._GetNormalizedPath(
        '%programdata%\\Microsoft\\Windows Defender\\Definition Updates\\'
        'Default\\MpEngine.dll')
    self.assertEqual(normalized_path, (
        '%programdata%\\Microsoft\\Windows Defender\\Definition Updates\\'
        'Default\\MpEngine.dll'))

    normalized_path = test_helper._GetNormalizedPath(
        '$(runtime.system32)\\WinML.dll')
    self.assertEqual(normalized_path, '%SystemRoot%\\System32\\WinML.dll')

    normalized_path = test_helper._GetNormalizedPath(
        '$(runtime.windows)\\immersivecontrolpanel\\systemsettings.exe')
    self.assertEqual(normalized_path, (
        '%SystemRoot%\\immersivecontrolpanel\\systemsettings.exe'))

    normalized_path = test_helper._GetNormalizedPath('\\eventlogmessages.dll')
    self.assertEqual(normalized_path, '\\eventlogmessages.dll')

    # TODO: add tests for Merge
    # TODO: add tests for NormalizeMessageFiles


if __name__ == '__main__':
  unittest.main()
