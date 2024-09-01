#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows preprocessor plugins."""

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfwinreg import fake as dfwinreg_fake
from dfwinreg import regf as dfwinreg_regf
from dfwinreg import registry as dfwinreg_registry
from dfwinreg import registry_searcher

from plaso.containers import artifacts
from plaso.preprocessors import manager
from plaso.preprocessors import mediator
from plaso.preprocessors import windows

from tests.preprocessors import test_lib


class WindowsArtifactPreprocessorPluginTestCase(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Windows artifact preprocessor plugin test case."""

  def _GetWinRegistryFromFileEntry(self, file_entry):
    """Retrieves a Windows Registry from a file entry.

    Args:
      file_entry (dfvfs.FileEntry): file entry that references a test file.

    Returns:
      dfwinreg.WinRegistry: Windows Registry or None.
    """
    file_object = file_entry.GetFileObject()
    if not file_object:
      return None

    registry_file = dfwinreg_regf.REGFWinRegistryFile(ascii_codepage='cp1252')
    registry_file.Open(file_object)

    win_registry = dfwinreg_registry.WinRegistry()
    key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
    win_registry.MapFile(key_path_prefix, registry_file)

    return win_registry

  def _RunPreprocessorPluginOnWindowsRegistryValue(
      self, file_system, mount_point, storage_writer, plugin):
    """Runs a preprocessor plugin on a Windows Registry value.

    Args:
      file_system (dfvfs.FileSystem): file system to be preprocessed.
      mount_point (dfvfs.PathSpec): mount point path specification that refers
          to the base location of the file system.
      storage_writer (StorageWriter): storage writer.
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      PreprocessMediator: preprocess mediator.
    """
    artifact_definition = self._artifacts_registry.GetDefinitionByName(
        plugin.ARTIFACT_DEFINITION_NAME)
    self.assertIsNotNone(artifact_definition)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')

    registry_file_reader = manager.FileSystemWinRegistryFileReader(
        file_system, mount_point, environment_variables=[environment_variable])
    win_registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)

    test_mediator = mediator.PreprocessMediator(storage_writer)

    searcher = registry_searcher.WinRegistrySearcher(win_registry)

    plugin.Collect(test_mediator, artifact_definition, searcher)

    return test_mediator

  def _RunPreprocessorPluginOnWindowsRegistryValueSoftware(
      self, storage_writer, plugin):
    """Runs a preprocessor plugin on a Windows Registry value in SOFTWARE.

    Args:
      storage_writer (StorageWriter): storage writer.
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      PreprocessMediator: preprocess mediator.
    """
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    file_system_builder.AddFileReadData(
        '/Windows/System32/config/SOFTWARE', test_file_path)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location='/')

    return self._RunPreprocessorPluginOnWindowsRegistryValue(
        file_system_builder.file_system, mount_point, storage_writer, plugin)

  def _RunPreprocessorPluginOnWindowsRegistryValueSystem(
      self, storage_writer, plugin):
    """Runs a preprocessor plugin on a Windows Registry value in SYSTEM.

    Args:
      storage_writer (StorageWriter): storage writer.
      plugin (ArtifactPreprocessorPlugin): preprocessor plugin.

    Return:
      PreprocessMediator: preprocess mediator.
    """
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    file_system_builder.AddFileReadData(
        '/Windows/System32/config/SYSTEM', test_file_path)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location='/')

    return self._RunPreprocessorPluginOnWindowsRegistryValue(
        file_system_builder.file_system, mount_point, storage_writer, plugin)


class WindowsAllUsersAppDataKnowledgeBasePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the allusersdata knowledge base value plugin."""

  # pylint: disable=protected-access

  def testCollect(self):
    """Tests the Collect function."""
    plugin = windows.WindowsAllUsersAppDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)

    plugin.Collect(test_mediator)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 0)

  def testCollectWithAllUsersProfile(self):
    """Tests the Collect function with the %AllUsersProfile% variable."""
    plugin = windows.WindowsAllUsersAppDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersprofile',
        value='C:\\Documents and Settings\\All Users')

    test_mediator._environment_variables['ALLUSERSPROFILE'] = (
        environment_variable)

    plugin.Collect(test_mediator)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    # The %AllUsersAppData% environment variable is derived from
    # the %AllUsersProfile% environment variable.
    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 1)

    environment_variable = storage_writer.GetAttributeContainerByIndex(
        'environment_variable', 0)
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.name, 'allusersappdata')
    self.assertEqual(
        environment_variable.value,
        'C:\\Documents and Settings\\All Users\\Application Data')

  def testCollectWithProgramData(self):
    """Tests the Collect function with the %ProgramData% variable."""
    plugin = windows.WindowsAllUsersAppDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='programdata',
        value='%SystemDrive%\\ProgramData')

    test_mediator._environment_variables['PROGRAMDATA'] = environment_variable

    plugin.Collect(test_mediator)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    # The %AllUsersAppData% environment variable is derived from
    # the %ProgramData% environment variable.
    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 1)

    environment_variable = storage_writer.GetAttributeContainerByIndex(
        'environment_variable', 0)
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.name, 'allusersappdata')
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsAllUsersProfileEnvironmentVariablePluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the %AllUsersProfile% environment variable plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsAllUsersProfileEnvironmentVariablePlugin()
    self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 0)


class WindowsAllUsersAppProfileKnowledgeBasePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the allusersprofile knowledge base value plugin."""

  # pylint: disable=protected-access

  def testCollect(self):
    """Tests the Collect function."""
    plugin = windows.WindowsAllUsersAppProfileKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)

    plugin.Collect(test_mediator)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 0)

  def testCollectWithAllUsersProfile(self):
    """Tests the Collect function with the %AllUsersProfile% variable."""
    plugin = windows.WindowsAllUsersAppProfileKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersprofile',
        value='C:\\Documents and Settings\\All Users')

    test_mediator._environment_variables['ALLUSERSPROFILE'] = (
        environment_variable)

    plugin.Collect(test_mediator)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    # The %AllUsersProfile% environment variable is already set in
    # the knowledge base and should not be created.
    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 0)

  def testCollectWithProgramData(self):
    """Tests the Collect function with the %ProgramData% variable."""
    plugin = windows.WindowsAllUsersAppProfileKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='programdata',
        value='%SystemDrive%\\ProgramData')

    test_mediator._environment_variables['PROGRAMDATA'] = environment_variable

    plugin.Collect(test_mediator)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    # The %AllUsersProfile% environment variable is derived from
    # the %ProgramData% environment variable.
    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 1)

    environment_variable = storage_writer.GetAttributeContainerByIndex(
        'environment_variable', 0)
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.name, 'allusersprofile')
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsAvailableTimeZonesPluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the Windows available time zones plugin."""

  def testParseKey(self):
    """Tests the _ParseKey function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsAvailableTimeZonesPlugin()
    self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'time_zone')
    self.assertEqual(number_of_artifacts, 101)

    available_time_zone = storage_writer.GetAttributeContainerByIndex(
       'time_zone', 7)

    self.assertEqual(available_time_zone.name, 'AUS Central Standard Time')


class WindowsCodePagePluginTest(WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the Windows code page plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsCodePagePlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    self.assertEqual(test_mediator.code_page, 'cp1252')


class WindowsEventLogPublishersPluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the Windows Event Log publishers plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsEventLogPublishersPlugin()
    self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'windows_eventlog_provider')
    self.assertEqual(number_of_artifacts, 438)


class WindowsEventLogSourcesPluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the Windows Event Log sources plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsEventLogSourcesPlugin()
    self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'windows_eventlog_provider')
    self.assertEqual(number_of_artifacts, 374)


class WindowsHostnamePluginTest(WindowsArtifactPreprocessorPluginTestCase):
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

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    self.assertEqual(test_mediator.hostname.name, 'WKS-WIN732BITA')

    value_data = ['MyHost', '']
    plugin._ParseValueData(test_mediator, value_data)


class WindowsLanguagePlugin(WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the Windows language plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsLanguagePlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    self.assertEqual(test_mediator.language, 'en-US')


class WindowsMountedDevicesPluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the Windows mounted devices plugin."""

  # pylint: disable=protected-access

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsMountedDevicesPlugin()
    self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_windows_mounted_devices = (
        storage_writer._attribute_containers_counter['windows_mounted_device'])
    self.assertEqual(number_of_windows_mounted_devices, 11)

    attribute_containers = list(storage_writer.GetAttributeContainers(
        'windows_mounted_device'))
    self.assertEqual(len(attribute_containers), 11)

    mounted_device_artifact = attribute_containers[0]
    self.assertEqual(mounted_device_artifact.identifier, '\\DosDevices\\C:')
    self.assertEqual(mounted_device_artifact.disk_identity, 0x5cbea03e)
    self.assertEqual(mounted_device_artifact.partition_offset, 1048576)


class WindowsProgramDataEnvironmentVariablePluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramData% environment variable plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsProgramDataEnvironmentVariablePlugin()
    self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 1)

    environment_variable = storage_writer.GetAttributeContainerByIndex(
        'environment_variable', 0)
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.name, 'programdata')
    self.assertEqual(environment_variable.value, '%SystemDrive%\\ProgramData')


class WindowsProgramDataKnowledgeBasePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the programdata knowledge base value plugin."""

  # pylint: disable=protected-access

  def testCollect(self):
    """Tests the Collect function."""
    plugin = windows.WindowsProgramDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)

    plugin.Collect(test_mediator)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 0)

  def testCollectWithAllUsersProfile(self):
    """Tests the Collect function with the %AllUsersProfile% variable."""
    plugin = windows.WindowsProgramDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersprofile',
        value='C:\\Documents and Settings\\All Users')

    test_mediator._environment_variables['ALLUSERSPROFILE'] = (
        environment_variable)

    plugin.Collect(test_mediator)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    # The %ProgramData% environment variable is derived from
    # the %AllUsersProfile% environment variable.
    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 1)

    environment_variable = storage_writer.GetAttributeContainerByIndex(
        'environment_variable', 0)
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.name, 'programdata')
    self.assertEqual(
        environment_variable.value, 'C:\\Documents and Settings\\All Users')

  def testCollectWithProgramData(self):
    """Tests the Collect function with the %ProgramData% variable."""
    plugin = windows.WindowsProgramDataKnowledgeBasePlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='programdata',
        value='%SystemDrive%\\ProgramData')

    test_mediator._environment_variables['PROGRAMDATA'] = environment_variable

    plugin.Collect(test_mediator)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    # The %ProgramData% environment variable is already set in
    # the knowledge base and should not be created.
    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 0)


class WindowsProgramFilesEnvironmentVariablePluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramFiles% environment variable plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsProgramFilesEnvironmentVariablePlugin()
    self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 1)

    environment_variable = storage_writer.GetAttributeContainerByIndex(
        'environment_variable', 0)
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.name, 'programfiles')
    self.assertEqual(environment_variable.value, 'C:\\Program Files')


class WindowsProgramFilesX86EnvironmentVariablePluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the %ProgramFilesX86% environment variable plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsProgramFilesX86EnvironmentVariablePlugin()
    self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    # The test SOFTWARE Registry file does not contain a value for
    # the Program Files X86 path.
    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 0)


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

    storage_writer = self._CreateTestStorageWriter()
    plugin = windows.WindowsSystemRootEnvironmentVariablePlugin()
    self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 1)

    environment_variable = storage_writer.GetAttributeContainerByIndex(
        'environment_variable', 0)
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.name, 'systemroot')
    self.assertEqual(environment_variable.value, '\\Windows')


class WindowsServicesAndDriversPluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the Windows service (and driver) configurations plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsServicesAndDriversPlugin()
    self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'windows_service_configuration')
    self.assertEqual(number_of_artifacts, 416)


class WindowsSystemProductPluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the system product information plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsSystemProductPlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    system_product = test_mediator.GetValue('operating_system_product')
    self.assertEqual(system_product, 'Windows 7 Ultimate')


class WindowsSystemVersionPluginTest(
    WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the system version information plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SOFTWARE'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsSystemVersionPlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSoftware(
        storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    system_version = test_mediator.GetValue('operating_system_version')
    self.assertEqual(system_version, '6.1')


class WindowsTimeZonePluginTest(WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the time zone plugin."""

  def testParseValueData(self):
    """Tests the _ParseValueData function."""
    test_file_path = self._GetTestFilePath(['SYSTEM'])
    self._SkipIfPathNotExists(test_file_path)

    storage_writer = self._CreateTestStorageWriter()

    plugin = windows.WindowsTimeZonePlugin()
    test_mediator = self._RunPreprocessorPluginOnWindowsRegistryValueSystem(
        storage_writer, plugin)

    # Unable to map: "@tzres.dll,-112" to time zone with error: Unsupported
    # time zone: @tzres.dll,-112
    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 1)

    self.assertEqual(test_mediator.time_zone.zone, 'America/New_York')


class WindowsUserAccountsPluginTest(WindowsArtifactPreprocessorPluginTestCase):
  """Tests for the Windows user accounts artifacts mapping."""

  # pylint: disable=protected-access

  def _CreateTestKey(self):
    """Creates Registry keys and values for testing.

    Returns:
      dfwinreg.WinRegistryKey: a Windows Registry key.
    """
    key_path_prefix = (
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
        'CurrentVersion')
    relative_key_path = 'Microsoft\\Windows NT\\CurrentVersion'
    registry_key = dfwinreg_fake.FakeWinRegistryKey(
        'ProfileList', key_path_prefix=key_path_prefix,
        relative_key_path=relative_key_path)

    # Setup user profile sub key.

    profile_key_name = 'S-1-5-21-2036804247-3058324640-2116585241-1114'
    profile_key = dfwinreg_fake.FakeWinRegistryKey(profile_key_name)
    registry_key.AddSubkey(profile_key_name, profile_key)

    return profile_key

  def testParseKey(self):
    """Tests the _ParseKey function."""
    test_file_entry = self._GetTestFileEntry(['SOFTWARE'])
    win_registry = self._GetWinRegistryFromFileEntry(test_file_entry)

    registry_key = win_registry.GetKeyByPath((
        'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion\\'
        'ProfileList\\S-1-5-21-2036804247-3058324640-2116585241-1114'))

    plugin = windows.WindowsUserAccountsPlugin()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)
    plugin._ParseKey(test_mediator, registry_key, 'ProfileImagePath')

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'user_account')
    self.assertEqual(number_of_artifacts, 1)

    user_account = storage_writer.GetAttributeContainerByIndex(
       'user_account', 0)

    self.assertEqual(
        user_account.identifier,
        'S-1-5-21-2036804247-3058324640-2116585241-1114')
    self.assertEqual(user_account.username, 'rsydow')
    self.assertEqual(user_account.user_directory, 'C:\\Users\\rsydow')

    # Test key with empty ProfileImagePath value.
    registry_key = self._CreateTestKey()

    storage_writer = self._CreateTestStorageWriter()
    test_mediator = mediator.PreprocessMediator(storage_writer)
    plugin._ParseKey(test_mediator, registry_key, 'ProfileImagePath')

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'user_account')
    self.assertEqual(number_of_artifacts, 1)

    user_account = storage_writer.GetAttributeContainerByIndex(
       'user_account', 0)

    self.assertEqual(
        user_account.identifier,
        'S-1-5-21-2036804247-3058324640-2116585241-1114')
    self.assertIsNone(user_account.username)
    self.assertIsNone(user_account.user_directory)


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

    storage_writer = self._CreateTestStorageWriter()
    plugin = windows.WindowsWinDirEnvironmentVariablePlugin()
    self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, storage_writer, plugin)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'preprocessing_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_artifacts = storage_writer.GetNumberOfAttributeContainers(
        'environment_variable')
    self.assertEqual(number_of_artifacts, 1)

    environment_variable = storage_writer.GetAttributeContainerByIndex(
        'environment_variable', 0)
    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.name, 'windir')
    self.assertEqual(environment_variable.value, '\\Windows')


if __name__ == '__main__':
  unittest.main()
