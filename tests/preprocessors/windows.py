#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows preprocess plug-ins."""

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.preprocessors import windows

from tests import test_lib as shared_test_lib
from tests.preprocessors import test_lib


class WindowsCodepagePreprocessPluginTest(test_lib.PreprocessPluginTestCase):
  """Tests for the Windows codepage preprocess plug-in object."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testRun(self):
    """Tests the Run function."""
    plugin = windows.WindowsCodepagePreprocessPlugin()
    knowledge_base = self._RunWindowsRegistryPluginOnSystem(plugin)

    self.assertEqual(knowledge_base.codepage, u'cp1252')


class WindowsHostnamePreprocessPluginTest(test_lib.PreprocessPluginTestCase):
  """Tests for the Windows hostname preprocess plug-in object."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testRun(self):
    """Tests the Run function."""
    plugin = windows.WindowsHostnamePreprocessPlugin()
    knowledge_base = self._RunWindowsRegistryPluginOnSystem(plugin)

    self.assertEqual(knowledge_base.hostname, u'WKS-WIN732BITA')


class WindowsProgramFilesEnvironmentVariableTest(
    test_lib.PreprocessPluginTestCase):
  """Tests for the %ProgramFiles% environment variable plug-in."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testRun(self):
    """Tests the Run function."""
    plugin = windows.WindowsProgramFilesEnvironmentVariable()
    knowledge_base = self._RunWindowsRegistryPluginOnSoftware(plugin)

    environment_variable = knowledge_base.GetEnvironmentVariable(
        u'ProgramFiles')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, u'C:\\Program Files')


class WindowsProgramFilesX86EnvironmentVariableTest(
    test_lib.PreprocessPluginTestCase):
  """Tests for the %ProgramFilesX86% environment variable plug-in."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testRun(self):
    """Tests the Run function."""
    plugin = windows.WindowsProgramFilesX86EnvironmentVariable()
    knowledge_base = self._RunWindowsRegistryPluginOnSoftware(plugin)

    environment_variable = knowledge_base.GetEnvironmentVariable(
        u'ProgramFilesX86')
    # The test SOFTWARE Registry file does not contain a value for
    # the Program Files X86 path.
    self.assertIsNone(environment_variable)


class WindowsSystemRootEnvironmentVariableTest(
    test_lib.PreprocessPluginTestCase):
  """Tests for the %SystemRoot% environment variable plug-in."""

  _FILE_DATA = b'regf'

  def testRun(self):
    """Tests the Run function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        u'/Windows/System32/config/SYSTEM', self._FILE_DATA)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

    plugin = windows.WindowsSystemRootEnvironmentVariable()
    knowledge_base = self._RunFileSystemPlugin(
        file_system_builder.file_system, mount_point, plugin)

    environment_variable = knowledge_base.GetEnvironmentVariable(u'SystemRoot')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, u'\\Windows')


class WindowsSystemProductPluginTest(test_lib.PreprocessPluginTestCase):
  """Tests for the plugin to determine Windows system version information."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testRun(self):
    """Tests the Run function."""
    plugin = windows.WindowsSystemProductPlugin()
    knowledge_base = self._RunWindowsRegistryPluginOnSoftware(plugin)

    osversion = knowledge_base.GetValue(u'operating_system_product')
    self.assertEqual(osversion, u'Windows 7 Ultimate')


class WindowsSystemVersionPluginTest(test_lib.PreprocessPluginTestCase):
  """Tests for the plugin to determine Windows system version information."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testRun(self):
    """Tests the Run function."""
    plugin = windows.WindowsSystemVersionPlugin()
    knowledge_base = self._RunWindowsRegistryPluginOnSoftware(plugin)

    osversion = knowledge_base.GetValue(u'operating_system_version')
    self.assertEqual(osversion, u'6.1')


class WindowsTimeZonePreprocessPluginTest(test_lib.PreprocessPluginTestCase):
  """Tests for the Windows timezone preprocess plug-in object."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testRun(self):
    """Tests the Run function."""
    plugin = windows.WindowsTimeZonePreprocessPlugin()
    knowledge_base = self._RunWindowsRegistryPluginOnSystem(plugin)

    time_zone_str = knowledge_base.GetValue(u'time_zone_str')
    self.assertEqual(time_zone_str, u'EST5EDT')


class WindowsUserAccountsPreprocessPluginTest(
    test_lib.PreprocessPluginTestCase):
  """Tests for the Windows username preprocess plug-in object."""

  # pylint: disable=protected-access

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testRun(self):
    """Tests the Run function."""
    plugin = windows.WindowsUserAccountsPreprocessPlugin()
    knowledge_base = self._RunWindowsRegistryPluginOnSoftware(plugin)

    users = sorted(
        knowledge_base._user_accounts[0].values(),
        key=lambda user_account: user_account.identifier)
    self.assertIsNotNone(users)
    self.assertEqual(len(users), 11)

    user_account = users[9]

    expected_sid = u'S-1-5-21-2036804247-3058324640-2116585241-1114'
    self.assertEqual(user_account.identifier, expected_sid)
    self.assertEqual(user_account.username, u'rsydow')
    self.assertEqual(user_account.user_directory, u'C:\\Users\\rsydow')


if __name__ == '__main__':
  unittest.main()
