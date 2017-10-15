#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the path helper."""

from __future__ import unicode_literals

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import artifacts
from plaso.engine import path_helper

from tests import test_lib as shared_test_lib


class PathHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the path helper."""

  def testExpandWindowsPath(self):
    """Tests the ExpandWindowsPath function."""
    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value='C:\\Windows')

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        '%SystemRoot%\\System32', [environment_variable])
    self.assertEqual(expanded_path, 'C:\\Windows\\System32')

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        'C:\\Windows\\System32', [environment_variable])
    self.assertEqual(expanded_path, 'C:\\Windows\\System32')

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        '%SystemRoot%\\System32', None)
    self.assertEqual(expanded_path, '%SystemRoot%\\System32')

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        '%Bogus%\\System32', [environment_variable])
    self.assertEqual(expanded_path, '%Bogus%\\System32')

    # Test non-string environment variable.
    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name='SystemRoot', value=('bogus', 0))

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        '%SystemRoot%\\System32', [environment_variable])
    self.assertEqual(expanded_path, '%SystemRoot%\\System32')

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

    expected_display_name = 'VSS2:TSK:C:/syslog.gz'
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        tsk_path_spec, text_prepend='C:')
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

    # Test path specification with mount point.
    mount_path = self._GetTestFilePath([])
    relative_path = path_helper.PathHelper.GetRelativePathForPathSpec(
        os_path_spec, mount_path=mount_path)
    expected_relative_path = '{0:s}syslog.gz'.format(os.path.sep)
    self.assertEqual(relative_path, expected_relative_path)

    # Test path specification with incorrect mount point.
    relative_path = path_helper.PathHelper.GetRelativePathForPathSpec(
        os_path_spec, mount_path='/bogus')
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
