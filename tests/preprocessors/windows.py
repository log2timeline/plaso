#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows preprocess plug-ins."""

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import artifacts
from plaso.engine import knowledge_base
from plaso.preprocessors import mediator
from plaso.preprocessors import windows

from tests.preprocessors import test_lib


class WindowsAllUsersAppDataKnowledgeBasePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the allusersdata knowledge base value plugin."""

  def testCollect(self):
    """Tests the Collect function."""
    plugin = windows.WindowsAllUsersAppDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_knowledge_base = knowledge_base.KnowledgeBase()
    test_mediator = mediator.PreprocessMediator(
        storage_writer, test_knowledge_base)

    plugin.Collect(test_mediator)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'allusersappdata')
    self.assertIsNone(environment_variable)

  def testCollectWithAllUsersProfile(self):
    """Tests the Collect function with the %AllUsersProfile% variable."""
    plugin = windows.WindowsAllUsersAppDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_knowledge_base = knowledge_base.KnowledgeBase()
    test_mediator = mediator.PreprocessMediator(
        storage_writer, test_knowledge_base)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersprofile',
        value='C:\\Documents and Settings\\All Users')

    test_mediator.knowledge_base.AddEnvironmentVariable(environment_variable)

    plugin.Collect(test_mediator)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'allusersappdata')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(
        environment_variable.value,
        'C:\\Documents and Settings\\All Users\\Application Data')

  def testCollectWithProgramData(self):
    """Tests the Collect function with the %ProgramData% variable."""
    plugin = windows.WindowsAllUsersAppDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_knowledge_base = knowledge_base.KnowledgeBase()
    test_mediator = mediator.PreprocessMediator(
        storage_writer, test_knowledge_base)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='programdata',
        value='%SystemDrive%\\ProgramData')

    test_mediator.knowledge_base.AddEnvironmentVariable(environment_variable)

    plugin.Collect(test_mediator)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'allusersappdata')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsAllUsersProfileEnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %AllUsersProfile% environment variable plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsAllUsersProfileEnvironmentVariablePlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'AllUsersProfile')
    self.assertIsNone(environment_variable)


class WindowsAllUsersAppProfileKnowledgeBasePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the allusersprofile knowledge base value plugin."""

  def testCollect(self):
    """Tests the Collect function."""
    plugin = windows.WindowsAllUsersAppProfileKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_knowledge_base = knowledge_base.KnowledgeBase()
    test_mediator = mediator.PreprocessMediator(
        storage_writer, test_knowledge_base)

    plugin.Collect(test_mediator)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'allusersprofile')
    self.assertIsNone(environment_variable)

  def testCollectWithAllUsersProfile(self):
    """Tests the Collect function with the %AllUsersProfile% variable."""
    plugin = windows.WindowsAllUsersAppProfileKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_knowledge_base = knowledge_base.KnowledgeBase()
    test_mediator = mediator.PreprocessMediator(
        storage_writer, test_knowledge_base)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersprofile',
        value='C:\\Documents and Settings\\All Users')

    test_mediator.knowledge_base.AddEnvironmentVariable(environment_variable)

    plugin.Collect(test_mediator)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'allusersprofile')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(
        environment_variable.value, 'C:\\Documents and Settings\\All Users')

  def testCollectWithProgramData(self):
    """Tests the Collect function with the %ProgramData% variable."""
    plugin = windows.WindowsAllUsersAppProfileKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_knowledge_base = knowledge_base.KnowledgeBase()
    test_mediator = mediator.PreprocessMediator(
        storage_writer, test_knowledge_base)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='programdata',
        value='%SystemDrive%\\ProgramData')

    test_mediator.knowledge_base.AddEnvironmentVariable(environment_variable)

    plugin.Collect(test_mediator)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'allusersprofile')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsAvailableTimeZonesPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Windows available time zones plugin."""

  def testParseKey(self):
    """Tests the _ParseKey function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsAvailableTimeZonesPlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    available_time_zones = sorted(
        test_mediator.knowledge_base.available_time_zones,
        key=lambda time_zone: time_zone.name)
    self.assertIsNotNone(available_time_zones)
    self.assertEqual(len(available_time_zones), 101)

    self.assertEqual(available_time_zones[0].name, 'AUS Central Standard Time')


class WindowsCodepagePlugin(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Windows codepage plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsCodepagePlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    self.assertEqual(test_mediator.knowledge_base.codepage, 'cp1252')


class WindowsHostnamePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Windows hostname plugin."""

  # pylint: disable=protected-access

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsHostnamePlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    self.assertEqual(test_mediator.knowledge_base.hostname, 'WKS-WIN732BITA')

    value_data = ['MyHost', '']
    plugin._ParseValueData(test_mediator, value_data)


class WindowsProgramDataEnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramData% environment variable plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsProgramDataEnvironmentVariablePlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'ProgramData')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsProgramDataKnowledgeBasePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the programdata knowledge base value plugin."""

  def testCollect(self):
    """Tests the Collect function."""
    plugin = windows.WindowsProgramDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_knowledge_base = knowledge_base.KnowledgeBase()
    test_mediator = mediator.PreprocessMediator(
        storage_writer, test_knowledge_base)

    plugin.Collect(test_mediator)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'programdata')
    self.assertIsNone(environment_variable)

  def testCollectWithAllUsersProfile(self):
    """Tests the Collect function with the %AllUsersProfile% variable."""
    plugin = windows.WindowsProgramDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_knowledge_base = knowledge_base.KnowledgeBase()
    test_mediator = mediator.PreprocessMediator(
        storage_writer, test_knowledge_base)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersprofile',
        value='C:\\Documents and Settings\\All Users')

    test_mediator.knowledge_base.AddEnvironmentVariable(environment_variable)

    plugin.Collect(test_mediator)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'programdata')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(
        environment_variable.value, 'C:\\Documents and Settings\\All Users')

  def testCollectWithProgramData(self):
    """Tests the Collect function with the %ProgramData% variable."""
    plugin = windows.WindowsProgramDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_knowledge_base = knowledge_base.KnowledgeBase()
    test_mediator = mediator.PreprocessMediator(
        storage_writer, test_knowledge_base)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='programdata',
        value='%SystemDrive%\\ProgramData')

    test_mediator.knowledge_base.AddEnvironmentVariable(environment_variable)

    plugin.Collect(test_mediator)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'programdata')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsProgramFilesEnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramFiles% environment variable plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsProgramFilesEnvironmentVariablePlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'ProgramFiles')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, 'C:\\Program Files')


class WindowsProgramFilesX86EnvironmentVariablePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramFilesX86% environment variable plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsProgramFilesX86EnvironmentVariablePlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
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

    plugin = windows.WindowsSystemRootEnvironmentVariablePlugin()
    test_mediator = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, None, plugin)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'SystemRoot')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '\\Windows')


class WindowsSystemProductPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the system product information plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsSystemProductPlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    system_product = test_mediator.knowledge_base.GetValue(
        'operating_system_product')
    self.assertEqual(system_product, 'Windows 7 Ultimate')


class WindowsSystemVersionPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the system version information plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsSystemVersionPlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    system_version = test_mediator.knowledge_base.GetValue(
        'operating_system_version')
    self.assertEqual(system_version, '6.1')


class WindowsTimeZonePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the time zone plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsTimeZonePlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    self.assertEqual(test_mediator.knowledge_base.timezone.zone, 'EST5EDT')


class WindowsUserAccountsPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Windows user accounts artifacts mapping."""

  # pylint: disable=protected-access

  def testParseKey(self):
    """Tests the _ParseKey function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsUserAccountsPlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    self.assertEqual(storage_writer.number_of_preprocessing_warnings, 0)

    user_accounts = sorted(
        test_mediator.knowledge_base.user_accounts,
        key=lambda user_account: user_account.identifier)
    self.assertIsNotNone(user_accounts)
    self.assertEqual(len(user_accounts), 11)

    user_account = user_accounts[9]

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

    plugin = windows.WindowsWinDirEnvironmentVariablePlugin()
    test_mediator = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, None, plugin)

    environment_variable = test_mediator.knowledge_base.GetEnvironmentVariable(
        'WinDir')
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, '\\Windows')


if __name__ == '__main__':
  unittest.main()
