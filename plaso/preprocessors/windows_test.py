#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows preprocess plug-ins."""

import os
import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.path import fake_path_spec

from plaso.artifacts import knowledge_base
from plaso.preprocessors import windows
from plaso.preprocessors import test_lib


class WindowsSoftwareRegistryTest(test_lib.PreprocessPluginTest):
  """Base class for tests that use the SOFTWARE Registry file."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    file_object = open(os.path.join(
        self._TEST_DATA_PATH, u'SYSTEM'), 'rb')
    file_data = file_object.read()
    file_object.close()

    self._fake_file_system = self._BuildSingleFileFakeFileSystem(
        u'/Windows/System32/config/SYSTEM', file_data)

    file_object = open(os.path.join(
        self._TEST_DATA_PATH, u'SOFTWARE'), 'rb')
    file_data = file_object.read()
    file_object.close()

    self._fake_file_system.AddFileEntry(
        u'/Windows/System32/config/SOFTWARE', file_data=file_data)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        self._fake_file_system, mount_point)


class WindowsSystemRegistryTest(test_lib.PreprocessPluginTest):
  """Base class for tests that use the SYSTEM Registry file."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    file_object = open(os.path.join(
        self._TEST_DATA_PATH, u'SYSTEM'), 'rb')
    file_data = file_object.read()
    file_object.close()

    self._fake_file_system = self._BuildSingleFileFakeFileSystem(
        u'/Windows/System32/config/SYSTEM', file_data)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        self._fake_file_system, mount_point)


class WindowsCodepageTest(WindowsSystemRegistryTest):
  """Tests for the Windows codepage preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath()
    plugin.Run(self._searcher, knowledge_base_object)

    plugin = windows.WindowsCodepage()
    plugin.Run(self._searcher, knowledge_base_object)

    self.assertEquals(knowledge_base_object.codepage, u'cp1252')


class WindowsHostnameTest(WindowsSystemRegistryTest):
  """Tests for the Windows hostname preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath()
    plugin.Run(self._searcher, knowledge_base_object)

    plugin = windows.WindowsHostname()
    plugin.Run(self._searcher, knowledge_base_object)

    self.assertEquals(knowledge_base_object.hostname, u'WKS-WIN732BITA')


class WindowsProgramFilesPath(WindowsSoftwareRegistryTest):
  """Tests for the Windows Program Files path preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath()
    plugin.Run(self._searcher, knowledge_base_object)

    plugin = windows.WindowsProgramFilesPath()
    plugin.Run(self._searcher, knowledge_base_object)

    path = knowledge_base_object.GetValue('programfiles')
    self.assertEquals(path, u'Program Files')


class WindowsProgramFilesX86Path(WindowsSoftwareRegistryTest):
  """Tests for the Windows Program Files X86 path preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath()
    plugin.Run(self._searcher, knowledge_base_object)

    plugin = windows.WindowsProgramFilesX86Path()

    plugin.Run(self._searcher, knowledge_base_object)

    path = knowledge_base_object.GetValue('programfilesx86')
    # The test SOFTWARE Registry file does not contain a value for
    # the Program Files X86 path.
    self.assertEquals(path, None)


class WindowsSystemRegistryPathTest(test_lib.PreprocessPluginTest):
  """Tests for the Windows system Registry path preprocess plug-in object."""

  _FILE_DATA = 'regf'

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._fake_file_system = self._BuildSingleFileFakeFileSystem(
        u'/Windows/System32/config/SYSTEM', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        self._fake_file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = windows.WindowsSystemRegistryPath()
    plugin.Run(self._searcher, knowledge_base_object)

    path = knowledge_base_object.GetValue('sysregistry')
    self.assertEquals(path, u'/Windows/System32/config')


class WindowsSystemRootPathTest(test_lib.PreprocessPluginTest):
  """Tests for the Windows system Root path preprocess plug-in object."""

  _FILE_DATA = 'regf'

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._fake_file_system = self._BuildSingleFileFakeFileSystem(
        u'/Windows/System32/config/SYSTEM', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        self._fake_file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = windows.WindowsSystemRootPath()
    plugin.Run(self._searcher, knowledge_base_object)

    path = knowledge_base_object.GetValue('systemroot')
    self.assertEquals(path, u'/Windows')


class WindowsTimeZoneTest(WindowsSystemRegistryTest):
  """Tests for the Windows timezone preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath()
    plugin.Run(self._searcher, knowledge_base_object)

    plugin = windows.WindowsTimeZone()
    plugin.Run(self._searcher, knowledge_base_object)

    time_zone_str = knowledge_base_object.GetValue('time_zone_str')
    self.assertEquals(time_zone_str, u'EST5EDT')


class WindowsUsersTest(WindowsSoftwareRegistryTest):
  """Tests for the Windows username preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath()
    plugin.Run(self._searcher, knowledge_base_object)

    plugin = windows.WindowsUsers()
    plugin.Run(self._searcher, knowledge_base_object)

    users = knowledge_base_object.GetValue('users')
    self.assertEquals(len(users), 11)

    expected_sid = u'S-1-5-21-2036804247-3058324640-2116585241-1114'
    self.assertEquals(users[9].get('sid', None), expected_sid)
    self.assertEquals(users[9].get('name', None), u'rsydow')
    self.assertEquals(users[9].get('path', None), u'C:\\Users\\rsydow')


class WindowsVersionTest(WindowsSoftwareRegistryTest):
  """Tests for the Windows version preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath()
    plugin.Run(self._searcher, knowledge_base_object)

    plugin = windows.WindowsVersion()
    plugin.Run(self._searcher, knowledge_base_object)

    osversion = knowledge_base_object.GetValue('osversion')
    self.assertEquals(osversion, u'Windows 7 Ultimate')


if __name__ == '__main__':
  unittest.main()
