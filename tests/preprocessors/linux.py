#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Linux preprocess plug-ins."""

from __future__ import unicode_literals

import unittest

from dfvfs.helpers import fake_file_system_builder
from dfvfs.path import fake_path_spec

from plaso.preprocessors import linux

from tests.preprocessors import test_lib


class LinuxHostnamePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Linux hostname plugin."""

  _FILE_DATA = b'plaso.kiddaland.net\n'

  def testParseFileData(self):
    """Tests the _ParseFileData function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/etc/hostname', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = linux.LinuxHostnamePlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.hostname, 'plaso.kiddaland.net')


class LinuxDistributionPluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Linux distribution plugin."""

  _FILE_DATA = b'Fedora release 26 (Twenty Six)\n'

  def testParseFileData(self):
    """Tests the _ParseFileData function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/etc/system-release', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = linux.LinuxDistributionPlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    system_product = knowledge_base.GetValue('operating_system_product')
    self.assertEqual(system_product, 'Fedora release 26 (Twenty Six)')


class LinuxIssueFilePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Linux issue file plugin."""

  _FILE_DATA = b"""\
Debian GNU/Linux 5.0 \\n \\l

"""

  def testParseFileData(self):
    """Tests the _ParseFileData function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/etc/issue', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = linux.LinuxIssueFilePlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    system_product = knowledge_base.GetValue('operating_system_product')
    self.assertEqual(system_product, 'Debian GNU/Linux 5.0')


class LinuxStandardBaseReleasePluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Linux standard base (LSB) release plugin."""

  _FILE_DATA = b"""\
DISTRIB_CODENAME=trusty
DISTRIB_DESCRIPTION="Ubuntu 14.04 LTS"
DISTRIB_ID=Ubuntu
DISTRIB_RELEASE=14.04"""

  def testParseFileData(self):
    """Tests the _ParseFileData function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/etc/lsb-release', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = linux.LinuxStandardBaseReleasePlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    system_product = knowledge_base.GetValue('operating_system_product')
    self.assertEqual(system_product, 'Ubuntu 14.04 LTS')


class LinuxSystemdOperatingSystemPluginTest(
    test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Linux operating system release plugin."""

  _FILE_DATA = b"""\
NAME=Fedora
VERSION="26 (Workstation Edition)"
ID=fedora
VERSION_ID=26
PRETTY_NAME="Fedora 26 (Workstation Edition)"
ANSI_COLOR="0;34"
CPE_NAME="cpe:/o:fedoraproject:fedora:26"
HOME_URL="https://fedoraproject.org/"
BUG_REPORT_URL="https://bugzilla.redhat.com/"
REDHAT_BUGZILLA_PRODUCT="Fedora"
REDHAT_BUGZILLA_PRODUCT_VERSION=26
REDHAT_SUPPORT_PRODUCT="Fedora"
REDHAT_SUPPORT_PRODUCT_VERSION=26
PRIVACY_POLICY_URL=https://fedoraproject.org/wiki/Legal:PrivacyPolicy
VARIANT="Workstation Edition"
VARIANT_ID=workstation"""

  def testParseFileData(self):
    """Tests the _ParseFileData function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/etc/os-release', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = linux.LinuxSystemdOperatingSystemPlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    system_product = knowledge_base.GetValue('operating_system_product')
    self.assertEqual(system_product, 'Fedora 26 (Workstation Edition)')


class LinuxTimeZonePluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Linux time zone plugin."""

  def testParseFileEntryWithLink(self):
    """Tests the _ParseFileEntry function on a symbolic link."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddSymbolicLink(
        '/etc/localtime', '/usr/share/zoneinfo/Europe/Zurich')

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = linux.LinuxTimeZonePlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.timezone.zone, 'Europe/Zurich')

  def testParseFileEntryWithTZif(self):
    """Tests the _ParseFileEntry function on a timezone information file."""
    test_file_path = self._GetTestFilePath(['localtime.tzif'])
    self._SkipIfPathNotExists(test_file_path)

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFileReadData('/etc/localtime', test_file_path)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = linux.LinuxTimeZonePlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.timezone.zone, 'CET')

  def testParseFileEntryWithBogusTZif(self):
    """Tests the _ParseFileEntry function on a bogus TZif file."""
    test_file_path = self._GetTestFilePath(['syslog'])
    self._SkipIfPathNotExists(test_file_path)

    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFileReadData('/etc/localtime', test_file_path)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = linux.LinuxTimeZonePlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    self.assertEqual(knowledge_base.timezone.zone, 'UTC')


class LinuxUserAccountsPluginTest(test_lib.ArtifactPreprocessorPluginTestCase):
  """Tests for the Linux user accounts plugin."""

  _FILE_DATA = (
      b'root:x:0:0:root:/root:/bin/bash\n'
      b'bin:x:1:1:bin:/bin:/sbin/nologin\n'
      b'daemon:x:2:2:daemon:/sbin:/sbin/nologin\n'
      b'adm:x:3:4:adm:/var/adm:/sbin/nologin\n'
      b'lp:x:4:7:lp:/var/spool/lpd:/sbin/nologin\n'
      b'sync:x:5:0:sync:/sbin:/bin/sync\n'
      b'shutdown:x:6:0:shutdown:/sbin:/sbin/shutdown\n'
      b'halt:x:7:0:halt:/sbin:/sbin/halt\n'
      b'mail:x:8:12:mail:/var/spool/mail:/sbin/nologin\n'
      b'operator:x:11:0:operator:/root:/sbin/nologin\n'
      b'games:x:12:100:games:/usr/games:/sbin/nologin\n'
      b'ftp:x:14:50:FTP User:/var/ftp:/sbin/nologin\n'
      b'nobody:x:99:99:Nobody:/:/sbin/nologin\n')

  def testParseFileData(self):
    """Tests the _ParseFileData function."""
    file_system_builder = fake_file_system_builder.FakeFileSystemBuilder()
    file_system_builder.AddFile('/etc/passwd', self._FILE_DATA)

    mount_point = fake_path_spec.FakePathSpec(location='/')

    plugin = linux.LinuxUserAccountsPlugin()
    knowledge_base = self._RunPreprocessorPluginOnFileSystem(
        file_system_builder.file_system, mount_point, plugin)

    users = sorted(
        knowledge_base.user_accounts,
        key=lambda user_account: user_account.identifier)
    self.assertEqual(len(users), 13)

    user_account = users[4]

    self.assertEqual(user_account.identifier, '14')
    self.assertEqual(user_account.group_identifier, '50')
    self.assertEqual(user_account.user_directory, '/var/ftp')
    self.assertEqual(user_account.username, 'ftp')
    self.assertEqual(user_account.shell, '/sbin/nologin')


if __name__ == '__main__':
  unittest.main()
