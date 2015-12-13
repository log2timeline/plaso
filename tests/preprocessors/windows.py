#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows preprocess plug-ins."""

import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.dfwinreg import registry as dfwinreg_registry
from plaso.engine import knowledge_base
from plaso.preprocessors import manager
from plaso.preprocessors import windows

from tests import test_lib as shared_test_lib
from tests.preprocessors import test_lib


class WindowsSoftwareRegistryTest(test_lib.PreprocessPluginTest):
  """Base class for tests that use the SOFTWARE Registry file."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    path_attributes = {u'systemroot': u'\\Windows'}

    file_system_builder = shared_test_lib.FakeFileSystemBuilder()
    file_system_builder.AddTestFile(
        u'/Windows/System32/config/SOFTWARE', [u'SOFTWARE'])

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')
    registry_file_reader = manager.FileSystemWinRegistryFileReader(
        file_system_builder.file_system, mount_point,
        path_attributes=path_attributes)
    self._win_registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)


class WindowsSystemRegistryTest(test_lib.PreprocessPluginTest):
  """Base class for tests that use the SYSTEM Registry file."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    path_attributes = {u'systemroot': u'\\Windows'}

    file_system_builder = shared_test_lib.FakeFileSystemBuilder()
    file_system_builder.AddTestFile(
        u'/Windows/System32/config/SYSTEM', [u'SYSTEM'])

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')
    registry_file_reader = manager.FileSystemWinRegistryFileReader(
        file_system_builder.file_system, mount_point,
        path_attributes=path_attributes)
    self._win_registry = dfwinreg_registry.WinRegistry(
        registry_file_reader=registry_file_reader)


class WindowsCodepageTest(WindowsSystemRegistryTest):
  """Tests for the Windows codepage preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsCodepage()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    self.assertEqual(knowledge_base_object.codepage, u'cp1252')


class WindowsHostnameTest(WindowsSystemRegistryTest):
  """Tests for the Windows hostname preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsHostname()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    self.assertEqual(knowledge_base_object.hostname, u'WKS-WIN732BITA')


class WindowsProgramFilesPath(WindowsSoftwareRegistryTest):
  """Tests for the Windows Program Files path preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsProgramFilesPath()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    path = knowledge_base_object.GetValue(u'programfiles')
    self.assertEqual(path, u'\\Program Files')


class WindowsProgramFilesX86Path(WindowsSoftwareRegistryTest):
  """Tests for the Windows Program Files X86 path preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsProgramFilesX86Path()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    path = knowledge_base_object.GetValue(u'programfilesx86')
    # The test SOFTWARE Registry file does not contain a value for
    # the Program Files X86 path.
    self.assertIsNone(path)


class WindowsSystemRegistryPathTest(test_lib.PreprocessPluginTest):
  """Tests for the Windows system Registry path preprocess plug-in object."""

  _FILE_DATA = b'regf'

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    file_system_builder = shared_test_lib.FakeFileSystemBuilder()
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
    self.assertEqual(path, u'/Windows/System32/config')


class WindowsSystemRootPathTest(test_lib.PreprocessPluginTest):
  """Tests for the Windows system Root path preprocess plug-in object."""

  _FILE_DATA = b'regf'

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    file_system_builder = shared_test_lib.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        u'/Windows/System32/config/SYSTEM', self._FILE_DATA)

    mount_point = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_FAKE, location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        file_system_builder.file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = windows.WindowsSystemRootPath()
    plugin.Run(self._searcher, knowledge_base_object)

    path = knowledge_base_object.GetValue(u'systemroot')
    self.assertEqual(path, u'/Windows')


class WindowsTimeZoneTest(WindowsSystemRegistryTest):
  """Tests for the Windows timezone preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsTimeZone()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    time_zone_str = knowledge_base_object.GetValue(u'time_zone_str')
    self.assertEqual(time_zone_str, u'EST5EDT')


class WindowsUsersTest(WindowsSoftwareRegistryTest):
  """Tests for the Windows username preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsUsers()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    users = knowledge_base_object.GetValue(u'users')
    self.assertIsNotNone(users)
    self.assertEqual(len(users), 11)

    expected_sid = u'S-1-5-21-2036804247-3058324640-2116585241-1114'
    self.assertEqual(users[9].get(u'sid', None), expected_sid)
    self.assertEqual(users[9].get(u'name', None), u'rsydow')
    self.assertEqual(users[9].get(u'path', None), u'C:\\Users\\rsydow')


class WindowsVersionTest(WindowsSoftwareRegistryTest):
  """Tests for the Windows version preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    plugin = windows.WindowsVersion()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    plugin.Run(self._win_registry, knowledge_base_object)

    osversion = knowledge_base_object.GetValue(u'osversion')
    self.assertEqual(osversion, u'Windows 7 Ultimate')


if __name__ == '__main__':
  unittest.main()
