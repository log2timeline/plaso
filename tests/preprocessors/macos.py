#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the MacOS preprocess plug-ins."""

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.path import fake_path_spec

from plaso.preprocessors import macos

from tests import test_lib as shared_test_lib
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
        u'/Library/Preferences/SystemConfiguration/preferences.plist',
        self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = macos.MacOSHostnamePlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.hostname, u'Plaso\'s Mac mini')


class MacOSKeyboardLayoutPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the MacOS keyboard layout plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'com.apple.HIToolbox.plist'])
  def testParsePlistKeyValue(self):
    """Tests the _ParsePlistKeyValue function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath([u'com.apple.HIToolbox.plist'])
    file_system_builder.AddFileReadData(
        u'/Library/Preferences/com.apple.HIToolbox.plist', test_file_path)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = macos.MacOSKeyboardLayoutPlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    keyboard_layout = knowledge_base.GetValue('keyboard_layout')
    self.assertEqual(keyboard_layout, u'US')


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
        u'/System/Library/CoreServices/SystemVersion.plist',
        self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = macos.MacOSSystemVersionPlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    build = knowledge_base.GetValue(u'operating_system_version')
    self.assertEqual(build, u'10.9.2')


class MacOSTimeZonePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the MacOS time zone plugin."""

  def testParseFileEntry(self):
    """Tests the _ParseFileEntry function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddSymbolicLink(
        u'/private/etc/localtime', u'/usr/share/zoneinfo/Europe/Amsterdam')

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = macos.MacOSTimeZonePlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.timezone.zone, u'Europe/Amsterdam')


class MacOSUserAccountsPluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the MacOS user accounts plugin."""

  # pylint: disable=protected-access

  @shared_test_lib.skipUnlessHasTestFile([u'nobody.plist'])
  def testRun(self):
    """Tests the Run function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath([u'nobody.plist'])
    file_system_builder.AddFileReadData(
        u'/private/var/db/dslocal/nodes/Default/users/nobody.plist',
        test_file_path)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = macos.MacOSUserAccountsPlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    users = sorted(
        knowledge_base.user_accounts,
        key=lambda user_account: user_account.identifier)
    self.assertEqual(len(users), 1)

    user_account = users[0]

    self.assertEqual(user_account.identifier, u'-2')
    self.assertEqual(user_account.full_name, u'Unprivileged User')
    self.assertEqual(user_account.user_directory, u'/var/empty')
    self.assertEqual(user_account.username, u'nobody')


if __name__ == '__main__':
  unittest.main()
