#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows preprocess plug-ins."""

from __future__ import unicode_literals

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import artifacts
from plaso.engine import knowledge_base
from plaso.preprocessors import windows

from tests import test_lib as shared_test_lib
from tests.preprocessors import test_lib


class WindowsAllUsersAppDataKnowledgeBasePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the allusersdata knowledge base value plugin."""

  def testCollect(self):
    """Tests the Collect function."""
    plugin = windows.WindowsAllUsersAppDataKnowledgeBasePlugin()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin.Collect(knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'allusersappdata')
    self.assertIsNone(environment_variable)

  def testCollectWithAllUsersProfile(self):
    """Tests the Collect function with the %AllUsersProfile% variable."""
    plugin = windows.WindowsAllUsersAppDataKnowledgeBasePlugin()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersprofile',
        value='C:\\Documents and Settings\\All Users')

    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    plugin.Collect(knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'allusersappdata')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(
        environment_variable.value,
        'C:\\Documents and Settings\\All Users\\Application Data')

  def testCollectWithProgramData(self):
    """Tests the Collect function with the %ProgramData% variable."""
    plugin = windows.WindowsAllUsersAppDataKnowledgeBasePlugin()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='programdata',
        value='%SystemDrive%\\ProgramData')

    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    plugin.Collect(knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'allusersappdata')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsAllUsersProfileEnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %AllUsersProfile% environment variable plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['SOFTWARE'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = (
        windows.WindowsAllUsersProfileEnvironmentVariablePlugin())
    knowledge_base_object = (
        self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(plugin))

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'AllUsersProfile')
    self.assertIsNone(environment_variable)


class WindowsAllUsersAppProfileKnowledgeBasePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the allusersprofile knowledge base value plugin."""

  def testCollect(self):
    """Tests the Collect function."""
    plugin = windows.WindowsAllUsersAppProfileKnowledgeBasePlugin()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin.Collect(knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'allusersprofile')
    self.assertIsNone(environment_variable)

  def testCollectWithAllUsersProfile(self):
    """Tests the Collect function with the %AllUsersProfile% variable."""
    plugin = windows.WindowsAllUsersAppProfileKnowledgeBasePlugin()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersprofile',
        value='C:\\Documents and Settings\\All Users')

    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    plugin.Collect(knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'allusersprofile')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(
        environment_variable.value, 'C:\\Documents and Settings\\All Users')

  def testCollectWithProgramData(self):
    """Tests the Collect function with the %ProgramData% variable."""
    plugin = windows.WindowsAllUsersAppProfileKnowledgeBasePlugin()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='programdata',
        value='%SystemDrive%\\ProgramData')

    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    plugin.Collect(knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'allusersprofile')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsCodepagePlugin(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Windows codepage plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = windows.WindowsCodepagePlugin()
    knowledge_base_object = (
        self._RunPreprocessorPluginOnWindowsRegistryValueSystem(plugin))

    self.assertEqual(knowledge_base_object.codepage, 'cp1252')


class WindowsHostnamePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Windows hostname plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = windows.WindowsHostnamePlugin()
    knowledge_base_object = (
        self._RunPreprocessorPluginOnWindowsRegistryValueSystem(plugin))

    self.assertEqual(knowledge_base_object.hostname, 'WKS-WIN732BITA')


class WindowsProgramDataEnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramData% environment variable plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['SOFTWARE'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = (
        windows.WindowsProgramDataEnvironmentVariablePlugin())
    knowledge_base_object = (
        self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(plugin))

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'ProgramData')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsProgramDataKnowledgeBasePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the programdata knowledge base value plugin."""

  def testCollect(self):
    """Tests the Collect function."""
    plugin = windows.WindowsProgramDataKnowledgeBasePlugin()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin.Collect(knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'programdata')
    self.assertIsNone(environment_variable)

  def testCollectWithAllUsersProfile(self):
    """Tests the Collect function with the %AllUsersProfile% variable."""
    plugin = windows.WindowsProgramDataKnowledgeBasePlugin()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersprofile',
        value='C:\\Documents and Settings\\All Users')

    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    plugin.Collect(knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'programdata')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(
        environment_variable.value, 'C:\\Documents and Settings\\All Users')

  def testCollectWithProgramData(self):
    """Tests the Collect function with the %ProgramData% variable."""
    plugin = windows.WindowsProgramDataKnowledgeBasePlugin()
    knowledge_base_object = knowledge_base.KnowledgeBase()

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='programdata',
        value='%SystemDrive%\\ProgramData')

    knowledge_base_object.AddEnvironmentVariable(environment_variable)

    plugin.Collect(knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'programdata')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsProgramFilesEnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramFiles% environment variable plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['SOFTWARE'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = (
        windows.WindowsProgramFilesEnvironmentVariablePlugin())
    knowledge_base_object = (
        self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(plugin))

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'ProgramFiles')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, 'C:\\Program Files')


class WindowsProgramFilesX86EnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramFilesX86% environment variable plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['SOFTWARE'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = (
        windows.WindowsProgramFilesX86EnvironmentVariablePlugin())
    knowledge_base_object = (
        self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(plugin))

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'ProgramFilesX86')
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
        '/Windows/System32/config/SYSTEM', self._FILE_DATA)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location='/')

    plugin = (
        windows.WindowsSystemRootEnvironmentVariablePlugin())
    knowledge_base_object = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'SystemRoot')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '\\Windows')


class WindowsSystemProductPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the system product information plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['SOFTWARE'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = windows.WindowsSystemProductPlugin()
    knowledge_base_object = (
        self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(plugin))

    system_product = knowledge_base_object.GetValue('operating_system_product')
    self.assertEqual(system_product, 'Windows 7 Ultimate')


class WindowsSystemVersionPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the system version information plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['SOFTWARE'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = windows.WindowsSystemVersionPlugin()
    knowledge_base_object = (
        self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(plugin))

    system_version = knowledge_base_object.GetValue('operating_system_version')
    self.assertEqual(system_version, '6.1')


class WindowsTimeZonePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the time zone plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['SYSTEM'])
  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    plugin = windows.WindowsTimeZonePlugin()
    knowledge_base_object = (
        self._RunPreprocessorPluginOnWindowsRegistryValueSystem(plugin))

    self.assertEqual(knowledge_base_object.timezone.zone, 'EST5EDT')


class WindowsUserAccountsPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Windows user accounts artifacts mapping."""

  # pylint: disable=protected-access

  @shared_test_lib.skipUnlessHasTestFile(['SOFTWARE'])
  def testParseKey(self):
    """Tests the _ParseKey function."""
    plugin = windows.WindowsUserAccountsPlugin()
    knowledge_base_object = (
        self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(plugin))

    users = sorted(
        knowledge_base_object.user_accounts,
        key=lambda user_account: user_account.identifier)
    self.assertIsNotNone(users)
    self.assertEqual(len(users), 11)

    user_account = users[9]

    expected_sid = 'S-1-5-21-2036804247-3058324640-2116585241-1114'
    self.assertEqual(user_account.identifier, expected_sid)
    self.assertEqual(user_account.username, 'rsydow')
    self.assertEqual(user_account.user_directory, 'C:\\Users\\rsydow')


class WindowsWinDirEnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %WinDir% environment variable plugin."""

  _FILE_DATA = b'regf'

  def testParsePathSpecification(self):
    """Tests the _ParsePathSpecification function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        '/Windows/System32/config/SYSTEM', self._FILE_DATA)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location='/')

    plugin = (
        windows.WindowsWinDirEnvironmentVariablePlugin())
    knowledge_base_object = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        'WinDir')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '\\Windows')


if __name__ == '__main__':
  unittest.main()
