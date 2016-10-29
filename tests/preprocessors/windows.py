#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows preprocess plug-ins."""

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfwinreg import registry as dfwinreg_registry

from plaso.engine import knowledge_base
from plaso.preprocessors import manager
from plaso.preprocessors import windows

from tests import test_lib as shared_test_lib


class WindowsSoftwareRegistryTest(shared_test_lib.BaseTestCase):
  """Base class for tests that use the SOFTWARE Registry file."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    path_attributes = {u'systemroot': u'\\Windows'}

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath([u'SOFTWARE'])
    file_system_builder.AddFileReadData(
        u'/Windows/System32/config/SOFTWARE', test_file_path)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')
    registry_file_reader = manager.FileSystemWinRegistryFileReader(
        file_system_builder.file_system, mount_point,
        path_attributes=path_attributes)
    self._win_registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)


class WindowsSystemRegistryTest(shared_test_lib.BaseTestCase):
  """Base class for tests that use the SYSTEM Registry file."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    path_attributes = {u'systemroot': u'\\Windows'}

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath([u'SYSTEM'])
    file_system_builder.AddFileReadData(
        u'/Windows/System32/config/SYSTEM', test_file_path)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')
    registry_file_reader = manager.FileSystemWinRegistryFileReader(
        file_system_builder.file_system, mount_point,
        path_attributes=path_attributes)
    self._win_registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)


class WindowsCodepageTest(WindowsSystemRegistryTest):
  """Tests for the Windows codepage preprocess plug-in object."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsCodepage()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    self.assertEqual(knowledge_base_object.codepage, u'cp1252')


class WindowsHostnameTest(WindowsSystemRegistryTest):
  """Tests for the Windows hostname preprocess plug-in object."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsHostname()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    self.assertEqual(knowledge_base_object.hostname, u'WKS-WIN732BITA')


class WindowsProgramFilesEnvironmentVariableTest(WindowsSoftwareRegistryTest):
  """Tests for the %ProgramFiles% environment variable plug-in."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsProgramFilesEnvironmentVariable()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        u'ProgramFiles')

    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, u'\\Program Files')


class WindowsProgramFilesX86EnvironmentVariableTest(
    WindowsSoftwareRegistryTest):
  """Tests for the %ProgramFilesX86% environment variable plug-in."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsProgramFilesX86EnvironmentVariable()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        u'ProgramFilesX86')

    # The test SOFTWARE Registry file does not contain a value for
    # the Program Files X86 path.
    self.assertIsNone(environment_variable)


class WindowsSystemRegistryPathTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows system Registry path preprocess plug-in object."""

  _FILE_DATA = b'regf'

  def setUp(self):
    """Makes preparations before running an individual test."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        u'/Windows/System32/config/SYSTEM', self._FILE_DATA)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        file_system_builder.file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = windows.WindowsSystemRegistryPath()
    plugin.Run(self._searcher, knowledge_base_object)

    path = knowledge_base_object.GetValue(u'sysregistry')
    self.assertEqual(path, u'\\Windows\\System32\\config')


class WindowsSystemRootEnvironmentVariableTest(shared_test_lib.BaseTestCase):
  """Tests for the %SystemRoot% environment variable plug-in."""

  _FILE_DATA = b'regf'

  def testGetValue(self):
    """Tests the GetValue function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        u'/Windows/System32/config/SYSTEM', self._FILE_DATA)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')
    searcher = file_system_searcher.FileSystemSearcher(
        file_system_builder.file_system, mount_point)

    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = windows.WindowsSystemRootEnvironmentVariable()
    plugin.Run(searcher, knowledge_base_object)

    environment_variable = knowledge_base_object.GetEnvironmentVariable(
        u'SystemRoot')

    self.assertIsNotNone(environment_variable)
    self.assertEqual(environment_variable.value, u'\\Windows')


class WindowsTimeZoneTest(WindowsSystemRegistryTest):
  """Tests for the Windows timezone preprocess plug-in object."""

  @shared_test_lib.skipUnlessHasTestFile([u'SYSTEM'])
  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsTimeZone()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    time_zone_str = knowledge_base_object.GetValue(u'time_zone_str')
    self.assertEqual(time_zone_str, u'EST5EDT')


class WindowsUsersTest(WindowsSoftwareRegistryTest):
  """Tests for the Windows username preprocess plug-in object."""

  # pylint: disable=protected-access

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsUsers()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    users = sorted(
        knowledge_base_object._user_accounts[0].values(),
        key=lambda user_account: user_account.identifier)
    self.assertIsNotNone(users)
    self.assertEqual(len(users), 11)

    user_account = users[9]

    expected_sid = u'S-1-5-21-2036804247-3058324640-2116585241-1114'
    self.assertEqual(user_account.identifier, expected_sid)
    self.assertEqual(user_account.username, u'rsydow')
    self.assertEqual(user_account.user_directory, u'C:\\Users\\rsydow')


class WindowsSystemProductPluginTest(WindowsSoftwareRegistryTest):
  """Tests for the plugin to determine Windows system version information."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsSystemProductPlugin()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    osversion = knowledge_base_object.GetValue(u'operating_system_product')
    self.assertEqual(osversion, u'Windows 7 Ultimate')


class WindowsSystemVersionPluginTest(WindowsSoftwareRegistryTest):
  """Tests for the plugin to determine Windows system version information."""

  @shared_test_lib.skipUnlessHasTestFile([u'SOFTWARE'])
  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsSystemVersionPlugin()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    osversion = knowledge_base_object.GetValue(u'operating_system_version')
    self.assertEqual(osversion, u'6.1')


if __name__ == '__main__':
  unittest.main()
