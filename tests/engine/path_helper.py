#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the path helper."""

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
        case_sensitive=False, name=u'SystemRoot', value=u'C:\\Windows')

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        u'%SystemRoot%\\System32', [environment_variable])
    self.assertEqual(expanded_path, u'C:\\Windows\\System32')

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        u'C:\\Windows\\System32', [environment_variable])
    self.assertEqual(expanded_path, u'C:\\Windows\\System32')

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        u'%SystemRoot%\\System32', None)
    self.assertEqual(expanded_path, u'%SystemRoot%\\System32')

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        u'%Bogus%\\System32', [environment_variable])
    self.assertEqual(expanded_path, u'%Bogus%\\System32')

    # Test non-string environment variable.
    environment_variable = artifacts.EnvironmentVariableArtifact(
        case_sensitive=False, name=u'SystemRoot', value=(u'bogus', 0))

    expanded_path = path_helper.PathHelper.ExpandWindowsPath(
        u'%SystemRoot%\\System32', [environment_variable])
    self.assertEqual(expanded_path, u'%SystemRoot%\\System32')

  def testGetDisplayNameForPathSpec(self):
    """Tests the GetDisplayNameForPathSpec function."""
    test_path = self._GetTestFilePath([u'syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    expected_display_name = u'OS:{0:s}'.format(test_path)
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        os_path_spec)
    self.assertEqual(display_name, expected_display_name)

    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)

    expected_display_name = u'GZIP:{0:s}'.format(test_path)
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        gzip_path_spec)
    self.assertEqual(display_name, expected_display_name)

    test_path = self._GetTestFilePath([u'vsstest.qcow2'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    qcow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_QCOW, parent=os_path_spec)
    vshadow_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/vss2',
        store_index=1, parent=qcow_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=35, location=u'/syslog.gz',
        parent=vshadow_path_spec)

    expected_display_name = u'VSS2:TSK:/syslog.gz'
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        tsk_path_spec)
    self.assertEqual(display_name, expected_display_name)

    expected_display_name = u'VSS2:TSK:C:/syslog.gz'
    display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
        tsk_path_spec, text_prepend=u'C:')
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
    test_path = self._GetTestFilePath([u'syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)

    relative_path = path_helper.PathHelper.GetRelativePathForPathSpec(
        os_path_spec)
    self.assertEqual(relative_path, test_path)

    # Test path specification with mount point.
    mount_path = self._GetTestFilePath([])
    relative_path = path_helper.PathHelper.GetRelativePathForPathSpec(
        os_path_spec, mount_path=mount_path)
    expected_relative_path = u'{0:s}syslog.gz'.format(os.path.sep)
    self.assertEqual(relative_path, expected_relative_path)

    # Test path specification with incorrect mount point.
    relative_path = path_helper.PathHelper.GetRelativePathForPathSpec(
        os_path_spec, mount_path=u'/bogus')
    self.assertEqual(relative_path, test_path)

    # Test path specification with data stream.
    os_path_spec.data_stream = u'MYDATA'

    expected_relative_path = u'{0:s}:MYDATA'.format(test_path)
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
