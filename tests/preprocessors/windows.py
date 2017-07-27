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


class WindowsCodepagePlugin(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Windows codepage plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = windows.WindowsCodepagePlugin()
    knowledge_base = self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        plugin)

    self.assertEqual(knowledge_base.codepage, u'cp1252')


class WindowsHostnamePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Windows hostname plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = windows.WindowsHostnamePlugin()
    knowledge_base = self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        plugin)

    self.assertEqual(knowledge_base.hostname, u'WKS-WIN732BITA')


class WindowsProgramFilesEnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramFiles% environment variable plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = (
        windows.WindowsProgramFilesEnvironmentVariablePlugin())
    knowledge_base = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        plugin)

    environment_variable = knowledge_base.GetEnvironmentVariable(
        u'ProgramFiles')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, u'C:\\Program Files')


class WindowsProgramFilesX86EnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramFilesX86% environment variable plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = (
        windows.WindowsProgramFilesX86EnvironmentVariablePlugin())
    knowledge_base = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        plugin)

    environment_variable = knowledge_base.GetEnvironmentVariable(
        u'ProgramFilesX86')
    # The test SOFTWARE Registry file does not contain a value for
    # the Program Files X86 path.
    self.assertIsNone(environment_variable)


class WindowsSystemRootEnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %SystemRoot% environment variable plugin."""

  _FILE_DATA = b'regf'

  def testParsePathSpecification(self):
    """Tests the _ParsePathSpecification function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        u'/Windows/System32/config/SYSTEM', self._FILE_DATA)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

    plugin = (
        windows.WindowsSystemRootEnvironmentVariablePlugin())
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    environment_variable = knowledge_base.GetEnvironmentVariable(u'SystemRoot')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, u'\\Windows')


class WindowsSystemProductPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the system product information plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = windows.WindowsSystemProductPlugin()
    knowledge_base = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        plugin)

    osversion = knowledge_base.GetValue(u'operating_system_product')
    self.assertEqual(osversion, u'Windows 7 Ultimate')


class WindowsSystemVersionPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the system version information plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = windows.WindowsSystemVersionPlugin()
    knowledge_base = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        plugin)

    osversion = knowledge_base.GetValue(u'operating_system_version')
    self.assertEqual(osversion, u'6.1')


class WindowsTimeZonePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the time zone plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = windows.WindowsTimeZonePlugin()
    knowledge_base = self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        plugin)

    self.assertEqual(knowledge_base.timezone.zone, u'EST5EDT')


class WindowsUserAccountsPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Windows user accounts artifacts mapping."""

  # pylint: disable=protected-access

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testParseKey(self):
    """Tests the _ParseKey function."""
    plugin = windows.WindowsUserAccountsPlugin()
    knowledge_base = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        plugin)

    users = sorted(
        knowledge_base.user_accounts,
        key=lambda user_account: user_account.identifier)
    self.assertIsNotNone(users)
    self.assertEqual(len(users), 11)

    user_account = users[9]

    expected_sid = u'S-1-5-21-2036804247-3058324640-2116585241-1114'
    self.assertEqual(user_account.identifier, expected_sid)
    self.assertEqual(user_account.username, u'rsydow')
    self.assertEqual(user_account.user_directory, u'C:\\Users\\rsydow')


class WindowsWinDirEnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %WinDir% environment variable plugin."""

  _FILE_DATA = b'regf'

  def testParsePathSpecification(self):
    """Tests the _ParsePathSpecification function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        u'/Windows/System32/config/SYSTEM', self._FILE_DATA)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')

    plugin = (
        windows.WindowsWinDirEnvironmentVariablePlugin())
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    environment_variable = knowledge_base.GetEnvironmentVariable(u'WinDir')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, u'\\Windows')


if __name__ == '__main__':
  unittest.main()
