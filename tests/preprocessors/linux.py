#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Linux preprocess plug-ins."""

import unittest

from dfvfs.helpers import file_system_searcher
from dfvfs.path import fake_path_spec

from plaso.engine import knowledge_base
from plaso.preprocessors import linux

from tests import test_lib as shared_test_lib
from tests.preprocessors import test_lib


class LinuxHostnameTest(test_lib.PreprocessPluginTest):
  """Tests for the Linux hostname preprocess plug-in object."""

  _FILE_DATA = (
      'plaso.kiddaland.net\n')

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    file_system_builder = shared_test_lib.FakeFileSystemBuilder()
    file_system_builder.AddFile(u'/etc/hostname', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        file_system_builder.file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = linux.LinuxHostname()
    plugin.Run(self._searcher, knowledge_base_object)

    self.assertEqual(knowledge_base_object.hostname, u'plaso.kiddaland.net')


class LinuxUsernamesTest(test_lib.PreprocessPluginTest):
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

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    file_system_builder = shared_test_lib.FakeFileSystemBuilder()
    file_system_builder.AddFile(u'/etc/passwd', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location=u'/')
    self._searcher = file_system_searcher.FileSystemSearcher(
        file_system_builder.file_system, mount_point)

  def testGetValue(self):
    """Tests the GetValue function."""
    knowledge_base_object = knowledge_base.KnowledgeBase()

    plugin = linux.LinuxUsernames()
    plugin.Run(self._searcher, knowledge_base_object)

    users = knowledge_base_object.GetValue('users')
    self.assertEqual(len(users), 13)

    self.assertEqual(users[11].get('uid', None), u'14')
    self.assertEqual(users[11].get('gid', None), u'50')
    self.assertEqual(users[11].get('name', None), u'ftp')
    self.assertEqual(users[11].get('path', None), u'/var/ftp')
    self.assertEqual(users[11].get('shell', None), u'/sbin/nologin')


if __name__ == '__main__':
  unittest.main()
