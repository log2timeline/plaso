#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Linux preprocess plug-ins."""

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.path import fake_path_spec

from plaso.preprocessors import linux

from tests.preprocessors import test_lib


class LinuxHostnamePreprocessPluginTest(test_lib.PreprocessPluginTestCase):
  """Tests for the Linux hostname preprocess plug-in object."""

  _FILE_DATA = 'plaso.kiddaland.net\n'

  def testRun(self):
    """Tests the Run function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(u'/etc/hostname', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = linux.LinuxHostnamePreprocessPlugin()
    knowledge_base = self._RunFileSystemPlugin(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.hostname, u'plaso.kiddaland.net')


class LinuxTimeZonePreprocessPluginTest(test_lib.PreprocessPluginTestCase):
  """Test for the Linux timezone preprocess plug-in object."""

  _FILE_DATA = 'Europe/Zurich\n'

  def testRun(self):
    """Test the Run function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(u'/etc/timezone', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = linux.LinuxTimeZonePreprocessPlugin()
    knowledge_base = self._RunFileSystemPlugin(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.timezone.zone, u'Europe/Zurich')


class LinuxUserAccountsPreprocessPluginTest(test_lib.PreprocessPluginTestCase):
  """Tests for the Linux usernames preprocess plug-in object."""

  _FILE_DATA = (
      'root:x:0:0:root:/root:/bin/bash\n'
      'bin:x:1:1:bin:/bin:/sbin/nologin\n'
      'daemon:x:2:2:daemon:/sbin:/sbin/nologin\n'
      'adm:x:3:4:adm:/var/adm:/sbin/nologin\n'
      'lp:x:4:7:lp:/var/spool/lpd:/sbin/nologin\n'
      'sync:x:5:0:sync:/sbin:/bin/sync\n'
      'shutdown:x:6:0:shutdown:/sbin:/sbin/shutdown\n'
      'halt:x:7:0:halt:/sbin:/sbin/halt\n'
      'mail:x:8:12:mail:/var/spool/mail:/sbin/nologin\n'
      'operator:x:11:0:operator:/root:/sbin/nologin\n'
      'games:x:12:100:games:/usr/games:/sbin/nologin\n'
      'ftp:x:14:50:FTP User:/var/ftp:/sbin/nologin\n'
      'nobody:x:99:99:Nobody:/:/sbin/nologin\n')

  def testRun(self):
    """Tests the Run function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile(u'/etc/passwd', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')

    plugin = linux.LinuxUserAccountsPreprocessPlugin()
    knowledge_base = self._RunFileSystemPlugin(
        file_system_builder.file_system, mount_point, plugin)

    users = sorted(
        knowledge_base.user_accounts,
        key=lambda user_account: user_account.identifier)
    self.assertEqual(len(users), 13)

    user_account = users[4]

    self.assertEqual(user_account.identifier, u'14')
    self.assertEqual(user_account.group_identifier, u'50')
    self.assertEqual(user_account.user_directory, u'/var/ftp')
    self.assertEqual(user_account.username, u'ftp')
    self.assertEqual(user_account.shell, u'/sbin/nologin')


if __name__ == '__main__':
  unittest.main()
