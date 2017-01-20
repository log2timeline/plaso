#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X preprocess plug-ins."""

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.path import fake_path_spec

from plaso.preprocessors import macosx

from tests import test_lib as shared_test_lib
from tests.preprocessors import test_lib


class MacOSXHostnamePreprocessPluginTest(test_lib.PreprocessPluginTestCase):
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

  def testRun(self):
    """Tests the Run function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        u'/Library/Preferences/SystemConfiguration/preferences.plist',
        self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = macosx.MacOSXHostnamePreprocessPlugin()
    knowledge_base = self._RunFileSystemPlugin(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.hostname, u'Plaso\'s Mac mini')


class MacOSXKeyboardLayoutPreprocessPluginTest(
    test_lib.PreprocessPluginTestCase):
  """Tests for the Mac OS X keyboard layout preprocess plug-in object."""

  @shared_test_lib.skipUnlessHasTestFile([u'com.apple.HIToolbox.plist'])
  def testRun(self):
    """Tests the Run function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    test_file_path = self._GetTestFilePath([u'com.apple.HIToolbox.plist'])
    file_system_builder.AddFileReadData(
        u'/Library/Preferences/com.apple.HIToolbox.plist', test_file_path)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = macosx.MacOSXKeyboardLayoutPreprocessPlugin()
    knowledge_base = self._RunFileSystemPlugin(
        file_system_builder.file_system, mount_point, plugin)

    keyboard_layout = knowledge_base.GetValue('keyboard_layout')
    self.assertEqual(keyboard_layout, u'US')


class MacOSXSystemVersionPreprocessPluginTest(
    test_lib.PreprocessPluginTestCase):
  """Tests for the plugin to determine Mac OS X system version information."""

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

  def testRun(self):
    """Tests the Run function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(
        u'/System/Library/CoreServices/SystemVersion.plist',
        self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = macosx.MacOSXSystemVersionPreprocessPlugin()
    knowledge_base = self._RunFileSystemPlugin(
        file_system_builder.file_system, mount_point, plugin)

    build = knowledge_base.GetValue(u'operating_system_version')
    self.assertEqual(build, u'10.9.2')


class MacOSXTimeZonePreprocessPluginTest(test_lib.PreprocessPluginTestCase):
  """Tests for the Mac OS X timezone preprocess plug-in object."""

  def testRun(self):
    """Tests the Run function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddSymbolicLink(
        u'/private/etc/localtime', u'/usr/share/zoneinfo/Europe/Amsterdam')

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = macosx.MacOSXTimeZonePreprocessPlugin()
    knowledge_base = self._RunFileSystemPlugin(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.timezone.zone, u'Europe/Amsterdam')


class MacOSXUserAccountsPreprocessPluginTest(test_lib.PreprocessPluginTestCase):
  """Tests for the Mac OS X usernames preprocess plug-in object."""

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

    plugin = macosx.MacOSXUserAccountsPreprocessPlugin()
    knowledge_base = self._RunFileSystemPlugin(
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
