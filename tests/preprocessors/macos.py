#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MacOS preprocess plug-ins."""

from __future__ import unicode_literals

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.path import fake_path_spec

from plaso.preprocessors import macos

from tests.preprocessors import test_lib


class MacOSHostnamePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the MacOS hostname plugin."""

  # Note that is only part of the normal preferences.plist file data.
  _FILE_DATA = (
      b'<?xml version="1.0" encoding="UTF-8"?>\n'
      b'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
      b'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
      b'<plist version="1.0">\n'
      b'<dict>\n'
      b'\t<key>System</key>\n'
      b'\t<dict>\n'
      b'\t\t<key>Network</key>\n'
      b'\t\t<dict>\n'
      b'\t\t\t<key>HostNames</key>\n'
      b'\t\t\t<dict>\n'
      b'\t\t\t\t<key>LocalHostName</key>\n'
      b'\t\t\t\t<string>Plaso\'s Mac mini</string>\n'
      b'\t\t\t</dict>\n'
      b'\t\t</dict>\n'
      b'\t\t<key>System</key>\n'
      b'\t\t<dict>\n'
      b'\t\t\t<key>ComputerName</key>\n'
      b'\t\t\t<string>Plaso\'s Mac mini</string>\n'
      b'\t\t\t<key>ComputerNameEncoding</key>\n'
      b'\t\t\t<integer>0</integer>\n'
      b'\t\t</dict>\n'
      b'\t</dict>\n'
      b'</dict>\n'
      b'</plist>\n')

  def testParsePlistKeyValue(self):
    """Tests the _ParsePlistKeyValue function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        '/Library/Preferences/SystemConfiguration/preferences.plist',
        self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = macos.MacOSHostnamePlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.hostname, 'Plaso\'s Mac mini')


class MacOSKeyboardLayoutPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the MacOS keyboard layout plugin."""

  def testParsePlistKeyValue(self):
    """Tests the _ParsePlistKeyValue function."""
    test_file_path = self._GetTestFilePath(['com.apple.HIToolbox.plist'])
    self._SkipIfPathNotExists(test_file_path)

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFileReadData(
        '/Library/Preferences/com.apple.HIToolbox.plist', test_file_path)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = macos.MacOSKeyboardLayoutPlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    keyboard_layout = knowledge_base.GetValue('keyboard_layout')
    self.assertEqual(keyboard_layout, 'US')


class MacOSSystemVersionPluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the MacOS system version information plugin."""

  _FILE_DATA = (
      b'<?xml version="1.0" encoding="UTF-8"?>\n'
      b'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
      b'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
      b'<plist version="1.0">\n'
      b'<dict>\n'
      b'\t<key>ProductBuildVersion</key>\n'
      b'\t<string>13C64</string>\n'
      b'\t<key>ProductCopyright</key>\n'
      b'\t<string>1983-2014 Apple Inc.</string>\n'
      b'\t<key>ProductName</key>\n'
      b'\t<string>Mac OS X</string>\n'
      b'\t<key>ProductUserVisibleVersion</key>\n'
      b'\t<string>10.9.2</string>\n'
      b'\t<key>ProductVersion</key>\n'
      b'\t<string>10.9.2</string>\n'
      b'</dict>\n'
      b'</plist>\n')

  def testParsePlistKeyValue(self):
    """Tests the _ParsePlistKeyValue function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        '/System/Library/CoreServices/SystemVersion.plist',
        self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = macos.MacOSSystemVersionPlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    build = knowledge_base.GetValue('operating_system_version')
    self.assertEqual(build, '10.9.2')


class MacOSTimeZonePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the MacOS time zone plugin."""

  def testParseFileEntry(self):
    """Tests the _ParseFileEntry function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddSymbolicLink(
        '/private/etc/localtime', '/usr/share/zoneinfo/Europe/Amsterdam')

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = macos.MacOSTimeZonePlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.timezone.zone, 'Europe/Amsterdam')


class MacOSUserAccountsPluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the MacOS user accounts plugin."""

  # pylint: disable=protected-access

  def testRun(self):
    """Tests the Run function."""
    test_file_path = self._GetTestFilePath(['nobody.plist'])
    self._SkipIfPathNotExists(test_file_path)

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFileReadData(
        '/private/var/db/dslocal/nodes/Default/users/nobody.plist',
        test_file_path)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = macos.MacOSUserAccountsPlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    users = sorted(
        knowledge_base.user_accounts,
        key=lambda user_account: user_account.identifier)
    self.assertEqual(len(users), 1)

    user_account = users[0]

    self.assertEqual(user_account.identifier, '-2')
    self.assertEqual(user_account.full_name, 'Unprivileged User')
    self.assertEqual(user_account.user_directory, '/var/empty')
    self.assertEqual(user_account.username, 'nobody')


if __name__ == '__main__':
  unittest.main()
