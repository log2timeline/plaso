#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the scan tree-based path filter."""

import unittest

from plaso.filters import path_filter

from tests.filters import test_lib


class PathFilterScanTreeTest(test_lib.FilterTestCase):
  """Tests for the path filter scan tree."""

  # pylint: disable=protected-access

  def testInitialize(self):
    """Tests the initialize function."""
    scan_tree = path_filter.PathFilterScanTree([])
    self.assertIsNone(scan_tree._root_node)

    paths = [
        'HKEY_CURRENT_USER\\Software\\WinRAR\\ArcHistory',
        'HKEY_CURRENT_USER\\Software\\WinRAR\\DialogEditHistory\\ArcName',
        'HKEY_CURRENT_USER\\Software\\WinRAR\\DialogEditHistory\\ExtrPath',
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{FA99DFC7-6AC2-453A-A5E2-5E2AFF4507BD}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{F4E57C4B-2036-45F0-A9AB-443BCFE33D9F}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{F2A1CB5A-E3CC-4A2E-AF9D-505A7009D442}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{CAA59E3C-4792-41A5-9909-6A6A8D32490E}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{B267E3AD-A825-4A09-82B9-EEC22AA3B847}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{A3D53349-6E61-4557-8FC7-0028EDCEEBF6}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{9E04CAB2-CC14-11DF-BB8C-A2F1DED72085}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{75048700-EF1F-11D0-9888-006097DEACF9}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{5E6AB780-7743-11CF-A12B-00AA004AE837}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{0D6D4F41-2994-4BA0-8FEF-620E43CD2812}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\UserAssist\\{BCB48336-4DDD-48FF-BB0B-D3190DACB3E2}'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\'
         'TypedURLs'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Explorer\\TypedPaths'),
        ('HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
         'Session Manager\\AppCompatibility'),
        ('HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
         'Session Manager\\AppCompatCache'),
        ('HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
         'CurrentVersion'),
        'HKEY_LOCAL_MACHINE\\SAM\\Domains\\Account\\Users',
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Internet Settings\\Lockdown_Zones'),
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Internet Settings\\Zones'),
        ('HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Internet Settings\\Lockdown_Zones'),
        ('HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         'Internet Settings\\Zones'),
    ]

    scan_tree = path_filter.PathFilterScanTree(
        paths, path_segment_separator='\\')
    self.assertIsNotNone(scan_tree._root_node)

    path = 'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows'
    self.assertFalse(scan_tree.CheckPath(path))

    path = (
        'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
        'Session Manager\\AppCompatCache')
    self.assertTrue(scan_tree.CheckPath(path))

    path = (
        'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\'
        'Session Manager\\AppCompatCache')
    self.assertFalse(scan_tree.CheckPath(path))

    path = (
        'HKEY_LOCAL_MACHINE/System/CurrentControlSet/Control/'
        'Session Manager/AppCompatCache')
    self.assertTrue(scan_tree.CheckPath(path, path_segment_separator='/'))

    scan_tree = path_filter.PathFilterScanTree(
        paths, case_sensitive=False, path_segment_separator='\\')
    self.assertIsNotNone(scan_tree._root_node)

    path = 'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows'
    self.assertFalse(scan_tree.CheckPath(path))

    path = (
        'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
        'Session Manager\\AppCompatCache')
    self.assertTrue(scan_tree.CheckPath(path))

    path = (
        'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\'
        'Session Manager\\AppCompatCache')
    self.assertTrue(scan_tree.CheckPath(path))

    path = (
        'HKEY_LOCAL_MACHINE/System/CurrentControlSet/Control/'
        'Session Manager/AppCompatCache')
    self.assertTrue(scan_tree.CheckPath(path, path_segment_separator='/'))


if __name__ == '__main__':
  unittest.main()
