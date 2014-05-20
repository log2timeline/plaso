#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the Windows preprocess plug-ins."""

import os
import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.path import fake_path_spec

from plaso.lib import event
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
    pre_obj = event.PreprocessObject()
    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath(pre_obj)
    plugin.Run(self._searcher)

    plugin = windows.WindowsCodepage(pre_obj)

    plugin.Run(self._searcher)

    codepage = getattr(pre_obj, 'code_page', None)
    self.assertEquals(codepage, u'cp1252')


class WindowsHostnameTest(WindowsSystemRegistryTest):
  """Tests for the Windows hostname preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    pre_obj = event.PreprocessObject()
    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath(pre_obj)
    plugin.Run(self._searcher)

    plugin = windows.WindowsHostname(pre_obj)

    plugin.Run(self._searcher)

    hostname = getattr(pre_obj, 'hostname', None)
    self.assertEquals(hostname, u'WKS-WIN732BITA')


class WindowsProgramFilesPath(WindowsSoftwareRegistryTest):
  """Tests for the Windows Program Files path preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    pre_obj = event.PreprocessObject()
    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath(pre_obj)
    plugin.Run(self._searcher)

    plugin = windows.WindowsProgramFilesPath(pre_obj)

    plugin.Run(self._searcher)

    path = getattr(pre_obj, 'programfiles', None)
    self.assertEquals(path, u'Program Files')


class WindowsProgramFilesX86Path(WindowsSoftwareRegistryTest):
  """Tests for the Windows Program Files X86 path preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    pre_obj = event.PreprocessObject()
    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath(pre_obj)
    plugin.Run(self._searcher)

    plugin = windows.WindowsProgramFilesX86Path(pre_obj)

    plugin.Run(self._searcher)

    path = getattr(pre_obj, 'programfilesx86', None)
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
    pre_obj = event.PreprocessObject()
    plugin = windows.WindowsSystemRegistryPath(pre_obj)

    plugin.Run(self._searcher)

    path = getattr(pre_obj, 'sysregistry', None)
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
    pre_obj = event.PreprocessObject()
    plugin = windows.WindowsSystemRootPath(pre_obj)

    plugin.Run(self._searcher)

    path = getattr(pre_obj, 'systemroot', None)
    self.assertEquals(path, u'/Windows/System32')


class WindowsTimeZoneTest(WindowsSystemRegistryTest):
  """Tests for the Windows timezone preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    pre_obj = event.PreprocessObject()
    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath(pre_obj)
    plugin.Run(self._searcher)

    plugin = windows.WindowsTimeZone(pre_obj)

    plugin.Run(self._searcher)

    timezone = getattr(pre_obj, 'time_zone_str', None)
    self.assertEquals(timezone, u'EST5EDT')


class WindowsUsersTest(WindowsSoftwareRegistryTest):
  """Tests for the Windows username preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    pre_obj = event.PreprocessObject()
    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath(pre_obj)
    plugin.Run(self._searcher)

    plugin = windows.WindowsUsers(pre_obj)

    plugin.Run(self._searcher)

    users = getattr(pre_obj, 'users', None)
    self.assertEquals(len(users), 11)

    expected_sid = u'S-1-5-21-2036804247-3058324640-2116585241-1114'
    self.assertEquals(users[9].get('sid', None), expected_sid)
    self.assertEquals(users[9].get('name', None), u'rsydow')
    self.assertEquals(users[9].get('path', None), u'C:\\Users\\rsydow')


class WindowsVersionTest(WindowsSoftwareRegistryTest):
  """Tests for the Windows version preprocess plug-in object."""

  def testGetValue(self):
    """Tests the GetValue function."""
    pre_obj = event.PreprocessObject()
    # The plug-in needs to expand {sysregistry} so we need to run
    # the WindowsSystemRegistryPath plug-in first.
    plugin = windows.WindowsSystemRegistryPath(pre_obj)
    plugin.Run(self._searcher)

    plugin = windows.WindowsVersion(pre_obj)

    plugin.Run(self._searcher)

    version = getattr(pre_obj, 'osversion', None)
    self.assertEquals(version, u'Windows 7 Ultimate')


if __name__ == '__main__':
  unittest.main()
