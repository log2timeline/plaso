#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the path helper."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import artifacts
from plaso.engine import path_helper

from tests import test_lib as shared_test_lib


class PathHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the path helper."""

  # pylint: disable=protected-access

  def testExpandUsersHomeDirectoryPathSegments(self):
    """Tests the _ExpandUsersHomeDirectoryPathSegments function."""
    user_account_artifact1 = artifacts.UserAccountArtifact(
        user_directory='/home/Test1', username='Test1')
    user_account_artifact2 = artifacts.UserAccountArtifact(
        user_directory='/Users/Test2', username='Test2')
    user_account_artifact3 = artifacts.UserAccountArtifact(username='Test3')

    user_accounts = [
        user_account_artifact1, user_account_artifact2, user_account_artifact3]

    path_segments = ['%%users.homedir%%', '.bashrc']
    expanded_paths = (
        path_helper.PathHelper._ExpandUsersHomeDirectoryPathSegments(
            path_segments, '/', user_accounts))

    expected_expanded_paths = [
        '/home/Test1/.bashrc',
        '/Users/Test2/.bashrc']
    self.assertEqual(expanded_paths, expected_expanded_paths)

    user_account_artifact1 = artifacts.UserAccountArtifact(
        path_separator='\\', user_directory='C:\\Users\\Test1',
        username='Test1')
    user_account_artifact2 = artifacts.UserAccountArtifact(
        path_separator='\\', user_directory='%SystemDrive%\\Users\\Test2',
        username='Test2')

    user_accounts = [user_account_artifact1, user_account_artifact2]

    path_segments = ['%%users.userprofile%%', 'Profile']
    expanded_paths = (
        path_helper.PathHelper._ExpandUsersHomeDirectoryPathSegments(
            path_segments, '\\', user_accounts))

    expected_expanded_paths = [
        '\\Users\\Test1\\Profile',
        '\\Users\\Test2\\Profile']
    self.assertEqual(expanded_paths, expected_expanded_paths)

    path_segments = ['C:', 'Temp']
    expanded_paths = (
        path_helper.PathHelper._ExpandUsersHomeDirectoryPathSegments(
            path_segments, '\\', user_accounts))

    expected_expanded_paths = ['\\Temp']
    self.assertEqual(expanded_paths, expected_expanded_paths)

    path_segments = ['C:', 'Temp', '%%users.userprofile%%']
    expanded_paths = (
        path_helper.PathHelper._ExpandUsersHomeDirectoryPathSegments(
            path_segments, '\\', user_accounts))

    expected_expanded_paths = ['\\Temp\\%%users.userprofile%%']
    self.assertEqual(expanded_paths, expected_expanded_paths)

  def testExpandUsersVariablePathSegments(self):
    """Tests the _ExpandUsersVariablePathSegments function."""
    user_account_artifact1 = artifacts.UserAccountArtifact(
        identifier='1000', path_separator='\\',
        user_directory='C:\\Users\\Test1', username='Test1')
    user_account_artifact2 = artifacts.UserAccountArtifact(
        identifier='1001', path_separator='\\',
        user_directory='%SystemDrive%\\Users\\Test2', username='Test2')

    user_accounts = [user_account_artifact1, user_account_artifact2]

    path_segments = ['%%users.appdata%%', 'Microsoft', 'Windows', 'Recent']
    expanded_paths = path_helper.PathHelper._ExpandUsersVariablePathSegments(
        path_segments, '\\', user_accounts)

    expected_expanded_paths = [
        '\\Users\\Test1\\AppData\\Roaming\\Microsoft\\Windows\\Recent',
        '\\Users\\Test1\\Application Data\\Microsoft\\Windows\\Recent',
        '\\Users\\Test2\\AppData\\Roaming\\Microsoft\\Windows\\Recent',
        '\\Users\\Test2\\Application Data\\Microsoft\\Windows\\Recent']
    self.assertEqual(sorted(expanded_paths), expected_expanded_paths)

    path_segments = ['C:', 'Windows']
    expanded_paths = path_helper.PathHelper._ExpandUsersVariablePathSegments(
        path_segments, '\\', user_accounts)

    expected_expanded_paths = ['\\Windows']
    self.assertEqual(sorted(expanded_paths), expected_expanded_paths)

  def testIsWindowsDrivePathSegment(self):
    """Tests the _IsWindowsDrivePathSegment function."""
    result = path_helper.PathHelper._IsWindowsDrivePathSegment('C:')
    self.assertTrue(result)

    result = path_helper.PathHelper._IsWindowsDrivePathSegment('%SystemDrive%')
    self.assertTrue(result)

    result = path_helper.PathHelper._IsWindowsDrivePathSegment(
        '%%environ_systemdrive%%')
    self.assertTrue(result)

    result = path_helper.PathHelper._IsWindowsDrivePathSegment('Windows')
    self.assertFalse(result)

  def testExpandGlobStars(self):
    """Tests the ExpandGlobStars function."""
    paths = path_helper.PathHelper.ExpandGlobStars('/etc/sysconfig/**', '/')

    self.assertEqual(len(paths), 10)

    expected_paths = sorted([
        '/etc/sysconfig/*',
        '/etc/sysconfig/*/*',
        '/etc/sysconfig/*/*/*',
        '/etc/sysconfig/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*/*/*/*/*/*'])
    self.assertEqual(sorted(paths), expected_paths)

    # Test globstar with recursion depth of 4.
    paths = path_helper.PathHelper.ExpandGlobStars('/etc/sysconfig/**4', '/')

    self.assertEqual(len(paths), 4)

    expected_paths = sorted([
        '/etc/sysconfig/*',
        '/etc/sysconfig/*/*',
        '/etc/sysconfig/*/*/*',
        '/etc/sysconfig/*/*/*/*'])
    self.assertEqual(sorted(paths), expected_paths)

    # Test globstar with unsupported recursion depth of 99.
    paths = path_helper.PathHelper.ExpandGlobStars('/etc/sysconfig/**99', '/')

    self.assertEqual(len(paths), 10)

    expected_paths = sorted([
        '/etc/sysconfig/*',
        '/etc/sysconfig/*/*',
        '/etc/sysconfig/*/*/*',
        '/etc/sysconfig/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*/*/*/*/*',
        '/etc/sysconfig/*/*/*/*/*/*/*/*/*/*'])
    self.assertEqual(sorted(paths), expected_paths)

    # Test globstar with prefix.
    paths = path_helper.PathHelper.ExpandGlobStars('/etc/sysconfig/my**', '/')

    self.assertEqual(len(paths), 1)

    self.assertEqual(paths, ['/etc/sysconfig/my**'])

    # Test globstar with suffix.
    paths = path_helper.PathHelper.ExpandGlobStars('/etc/sysconfig/**.exe', '/')

    self.assertEqual(len(paths), 1)

    self.assertEqual(paths, ['/etc/sysconfig/**.exe'])

  def testExpandUsersVariablePath(self):
    """Tests the ExpandUsersVariablePath function."""
    user_account_artifact1 = artifacts.UserAccountArtifact(
        path_separator='\\', user_directory='C:\\Users\\Test1',
        username='Test1')
    user_account_artifact2 = artifacts.UserAccountArtifact(
        path_separator='\\', user_directory='%SystemDrive%\\Users\\Test2',
        username='Test2')

    user_accounts = [user_account_artifact1, user_account_artifact2]

    path = '%%users.appdata%%\\Microsoft\\Windows\\Recent'
    expanded_paths = path_helper.PathHelper.ExpandUsersVariablePath(
        path, '\\', user_accounts)

    expected_expanded_paths = [
        '\\Users\\Test1\\AppData\\Roaming\\Microsoft\\Windows\\Recent',
        '\\Users\\Test1\\Application Data\\Microsoft\\Windows\\Recent',
        '\\Users\\Test2\\AppData\\Roaming\\Microsoft\\Windows\\Recent',
        '\\Users\\Test2\\Application Data\\Microsoft\\Windows\\Recent']
    self.assertEqual(sorted(expanded_paths), expected_expanded_paths)

  def testExpandWindowsPath(self):
    """Tests the ExpandWindowsPath function."""
    environment_variables = []

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')
    environment_variables.append(environment_variable)

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        '%SystemRoot%\\System32', environment_variables)
    self.assertEqual(expanded_path, '\\Windows\\System32')

  def testExpandWindowsPathSegments(self):
    """Tests the ExpandWindowsPathSegments function."""
    environment_variables = []

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersappdata',
        value='C:\\Documents and Settings\\All Users\\Application Data')
    environment_variables.append(environment_variable)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='allusersprofile',
        value='C:\\Documents and Settings\\All Users')
    environment_variables.append(environment_variable)

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')
    environment_variables.append(environment_variable)

    expected_expanded_path_segment = [
        '', 'Documents and Settings', 'All Users', 'Application Data',
        'Apache Software Foundation']

    expanded_path_segment = path_helper.PathHelper.ExpandWindowsPathSegments(
        ['%AllUsersAppData%', 'Apache Software Foundation'],
        environment_variables)
    self.assertEqual(expanded_path_segment, expected_expanded_path_segment)

    expected_expanded_path_segment = [
        '', 'Documents and Settings', 'All Users', 'Start Menu', 'Programs',
        'Startup']

    expanded_path_segment = path_helper.PathHelper.ExpandWindowsPathSegments(
        ['%AllUsersProfile%', 'Start Menu', 'Programs', 'Startup'],
        environment_variables)
    self.assertEqual(expanded_path_segment, expected_expanded_path_segment)

    expanded_path_segment = path_helper.PathHelper.ExpandWindowsPathSegments(
        ['%SystemRoot%', 'System32'], environment_variables)
    self.assertEqual(expanded_path_segment, ['', 'Windows', 'System32'])

    expanded_path_segment = path_helper.PathHelper.ExpandWindowsPathSegments(
        ['C:', 'Windows', 'System32'], environment_variables)
    self.assertEqual(expanded_path_segment, ['', 'Windows', 'System32'])

    expanded_path_segment = path_helper.PathHelper.ExpandWindowsPathSegments(
        ['%SystemRoot%', 'System32'], None)
    self.assertEqual(expanded_path_segment, ['%SystemRoot%', 'System32'])

    expanded_path_segment = path_helper.PathHelper.ExpandWindowsPathSegments(
        ['%Bogus%', 'System32'], environment_variables)
    self.assertEqual(expanded_path_segment, ['%Bogus%', 'System32'])

    expanded_path_segment = path_helper.PathHelper.ExpandWindowsPathSegments(
        ['%%environ_systemroot%%', 'System32'], environment_variables)
    self.assertEqual(expanded_path_segment, ['', 'Windows', 'System32'])

    # Test non-string environment variable.
    environment_variables = []

    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value=('bogus', 0))
    environment_variables.append(environment_variable)

    expanded_path_segment = path_helper.PathHelper.ExpandWindowsPathSegments(
        ['%SystemRoot%', 'System32'], environment_variables)
    self.assertEqual(expanded_path_segment, ['%SystemRoot%', 'System32'])

  def testGetDisplayNameForPathSpec(self):
    """Tests the GetDisplayNameForPathSpec function."""
    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    expected_display_name = 'OS:{0:s}'.format(test_path)
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        os_path_spec)
    self.assertEqual(display_name, expected_display_name)

    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    expected_display_name = 'GZIP:{0:s}'.format(test_path)
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        gzip_path_spec)
    self.assertEqual(display_name, expected_display_name)

    test_path = self._GetTestFilePath(['syslog.bz2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
        compression_method=dfvfs_definitions.COMPRESSION_METHOD_BZIP2,
        parent=os_path_spec)

    expected_display_name = 'BZIP2:{0:s}'.format(test_path)
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        compressed_stream_path_spec)
    self.assertEqual(display_name, expected_display_name)

    test_path = self._GetTestFilePath(['syslog.xz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    compressed_stream_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM,
        compression_method=dfvfs_definitions.COMPRESSION_METHOD_XZ,
        parent=os_path_spec)

    expected_display_name = 'XZ:{0:s}'.format(test_path)
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        compressed_stream_path_spec)
    self.assertEqual(display_name, expected_display_name)

    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    vshadow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location='/vss2',
        store_index=1, parent=qcow_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=35, location='/syslog.gz',
        parent=vshadow_path_spec)

    expected_display_name = 'VSS2:TSK:/syslog.gz'
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        tsk_path_spec)
    self.assertEqual(display_name, expected_display_name)

    test_path = self._GetTestFilePath(['vsstest.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    vshadow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location='/vss2',
        store_index=1, parent=qcow_path_spec)
    ntfs_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_NTFS, mft_entry=35,
        location='\\syslog.gz', parent=vshadow_path_spec)

    expected_display_name = 'VSS2:NTFS:\\syslog.gz'
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        ntfs_path_spec)
    self.assertEqual(display_name, expected_display_name)

    # Test a path specification with a location with Unicode surrogates.
    tar_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR,
        location='/ustar/umlauts-\udcc4\udcd6\udcdc\udce4\udcf6\udcfc\udcdf',
        parent=os_path_spec)

    expected_display_name = (
        'TAR:/ustar/umlauts-\\xc4\\xd6\\xdc\\xe4\\xf6\\xfc\\xdf')
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        tar_path_spec)
    self.assertEqual(display_name, expected_display_name)

    # Test without path specification.
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(None)
    self.assertIsNone(display_name)

    # Test path specification without location
    os_path_spec.location = None
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    self.assertIsNone(display_name)

  def testGetRelativePathForPathSpec(self):
    """Tests the GetRelativePathForPathSpec function."""
    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    relative_path = path_helper.PathHelper.GetRelativePathForPathSpec(
        os_path_spec)
    self.assertEqual(relative_path, test_path)

    # Test path specification with data stream.
    os_path_spec.data_stream = 'MYDATA'

    expected_relative_path = '{0:s}:MYDATA'.format(test_path)
    relative_path = path_helper.PathHelper.GetRelativePathForPathSpec(
        os_path_spec)
    self.assertEqual(relative_path, expected_relative_path)

    # Test without path specification.
    display_name = path_helper.PathHelper.GetRelativePathForPathSpec(None)
    self.assertIsNone(display_name)

    # Test path specification without location.
    os_path_spec.location = None
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)

    display_name = path_helper.PathHelper.GetRelativePathForPathSpec(
        qcow_path_spec)
    self.assertIsNone(display_name)


if __name__ == '__main__':
  unittest.main()
