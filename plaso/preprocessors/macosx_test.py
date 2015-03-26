#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X preprocess plug-ins."""

import os
import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.path import fake_path_spec

from plaso.artifacts import knowledge_base
from plaso.preprocessors import macosx
from plaso.preprocessors import test_lib


class MacOSXBuildTest(test_lib.PreprocessPluginTest):
  """Tests for the Mac OS X build information preprocess plug-in object."""

  _FILE_DATA = (
      '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
      '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
      '<plist version="1.0">\n'
      '<dict>\n'
      '\t<key>ProductBuildVersion</key>\n'
      '\t<string>13C64</string>\n'
      '\t<key>ProductCopyright</key>\n'
      '\t<string>1983-2014 Apple Inc.</string>\n'
      '\t<key>ProductName</key>\n'
      '\t<string>Mac OS X</string>\n'
      '\t<key>ProductUserVisibleVersion</key>\n'
      '\t<string>10.9.2</string>\n'
      '\t<key>ProductVersion</key>\n'
      '\t<string>10.9.2</string>\n'
      '</dict>\n'
      '</plist>\n')

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._fake_file_system = self._BuildSingleFileFakeFileSystem(
        u'/System/Library/CoreServices/SystemVersion.plist',
        self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        self._fake_file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = macosx.MacOSXBuild()
    plugin.Run(self._searcher, knowledge_base_object)

    build = knowledge_base_object.GetValue('build')
    self.assertEqual(build, u'10.9.2')


class MacOSXHostname(test_lib.PreprocessPluginTest):
  """Tests for the Mac OS X hostname preprocess plug-in object."""

  # Note that is only part of the normal preferences.plist file data.
  _FILE_DATA = (
      '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
      '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
      '<plist version="1.0">\n'
      '<dict>\n'
      '\t<key>System</key>\n'
      '\t<dict>\n'
      '\t\t<key>Network</key>\n'
      '\t\t<dict>\n'
      '\t\t\t<key>HostNames</key>\n'
      '\t\t\t<dict>\n'
      '\t\t\t\t<key>LocalHostName</key>\n'
      '\t\t\t\t<string>Plaso\'s Mac mini</string>\n'
      '\t\t\t</dict>\n'
      '\t\t</dict>\n'
      '\t\t<key>System</key>\n'
      '\t\t<dict>\n'
      '\t\t\t<key>ComputerName</key>\n'
      '\t\t\t<string>Plaso\'s Mac mini</string>\n'
      '\t\t\t<key>ComputerNameEncoding</key>\n'
      '\t\t\t<integer>0</integer>\n'
      '\t\t</dict>\n'
      '\t</dict>\n'
      '</dict>\n'
      '</plist>\n')

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._fake_file_system = self._BuildSingleFileFakeFileSystem(
        u'/Library/Preferences/SystemConfiguration/preferences.plist',
        self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        self._fake_file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = macosx.MacOSXHostname()
    plugin.Run(self._searcher, knowledge_base_object)

    self.assertEqual(knowledge_base_object.hostname, u'Plaso\'s Mac mini')


class MacOSXKeyboard(test_lib.PreprocessPluginTest):
  """Tests for the Mac OS X keyboard layout preprocess plug-in object."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    file_object = open(os.path.join(
        self._TEST_DATA_PATH, u'com.apple.HIToolbox.plist'))
    file_data = file_object.read()
    file_object.close()

    self._fake_file_system = self._BuildSingleFileFakeFileSystem(
        u'/Library/Preferences/com.apple.HIToolbox.plist',
        file_data)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        self._fake_file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = macosx.MacOSXKeyboard()
    plugin.Run(self._searcher, knowledge_base_object)

    keyboard_layout = knowledge_base_object.GetValue('keyboard_layout')
    self.assertEqual(keyboard_layout, u'US')


class MacOSXTimezone(test_lib.PreprocessPluginTest):
  """Tests for the Mac OS X timezone preprocess plug-in object."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._fake_file_system = self._BuildSingleLinkFakeFileSystem(
        u'/private/etc/localtime', u'/usr/share/zoneinfo/Europe/Amsterdam')

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        self._fake_file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = macosx.MacOSXTimeZone()
    plugin.Run(self._searcher, knowledge_base_object)

    time_zone_str = knowledge_base_object.GetValue('time_zone_str')
    self.assertEqual(time_zone_str, u'Europe/Amsterdam')


class MacOSXUsersTest(test_lib.PreprocessPluginTest):
  """Tests for the Mac OS X usernames preprocess plug-in object."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    file_object = open(os.path.join(
        self._TEST_DATA_PATH, u'com.apple.HIToolbox.plist'))
    file_data = file_object.read()
    file_object.close()

    self._fake_file_system = self._BuildSingleFileFakeFileSystem(
        u'/private/var/db/dslocal/nodes/Default/users/nobody.plist',
        file_data)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        self._fake_file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = macosx.MacOSXUsers()
    plugin.Run(self._searcher, knowledge_base_object)

    users = knowledge_base_object.GetValue('users')
    self.assertEqual(len(users), 1)

    # TODO: fix the parsing of the following values to match the behavior on
    # Mac OS X.

    # The string -2 is converted into the integer -1.
    self.assertEqual(users[0].get('uid', None), -1)
    # 'home' is 0 which represents: /var/empty but we convert it
    # into u'<not set>'.
    self.assertEqual(users[0].get('path', None), u'<not set>')
    # 'name' is 0 which represents: nobody but we convert it into u'<not set>'.
    self.assertEqual(users[0].get('name', None), u'<not set>')
    # 'realname' is 0 which represents: 'Unprivileged User' but we convert it
    # into u'N/A'.
    self.assertEqual(users[0].get('realname', None), u'N/A')


if __name__ == '__main__':
  unittest.main()
