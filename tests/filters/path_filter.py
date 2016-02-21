#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the scan tree-based path filter."""

import unittest

from plaso.filters import path_filter

from tests.filters import test_lib


class PathFilterScanTreeTest(test_lib.FilterTestCase):
  """Tests for the path filter scan tree."""

  def testInitialize(self):
    """Tests the initialize function."""
    scan_tree = path_filter.PathFilterScanTree([])
    self.assertIsNone(scan_tree._root_node)

    paths = [
        u'HKEY_CURRENT_USER\\Software\\WinRAR\\ArcHistory',
        u'HKEY_CURRENT_USER\\Software\\WinRAR\\DialogEditHistory\\ArcName',
        u'HKEY_CURRENT_USER\\Software\\WinRAR\\DialogEditHistory\\ExtrPath',
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{FA99DFC7-6AC2-453A-A5E2-5E2AFF4507BD}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{F4E57C4B-2036-45F0-A9AB-443BCFE33D9F}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{F2A1CB5A-E3CC-4A2E-AF9D-505A7009D442}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{CEBFF5CD-ACE2-4F4F-9178-9926F41749EA}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{CAA59E3C-4792-41A5-9909-6A6A8D32490E}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{B267E3AD-A825-4A09-82B9-EEC22AA3B847}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{A3D53349-6E61-4557-8FC7-0028EDCEEBF6}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{9E04CAB2-CC14-11DF-BB8C-A2F1DED72085}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{75048700-EF1F-11D0-9888-006097DEACF9}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{5E6AB780-7743-11CF-A12B-00AA004AE837}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{0D6D4F41-2994-4BA0-8FEF-620E43CD2812}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\UserAssist\\{BCB48336-4DDD-48FF-BB0B-D3190DACB3E2}'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\'
         u'TypedURLs'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Explorer\\TypedPaths'),
        (u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
         u'Session Manager\\AppCompatibility'),
        (u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
         u'Session Manager\\AppCompatCache'),
        (u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\'
         u'CurrentVersion'),
        u'HKEY_LOCAL_MACHINE\\SAM\\Domains\\Account\\Users',
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Internet Settings\\Lockdown_Zones'),
        (u'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Internet Settings\\Zones'),
        (u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Internet Settings\\Lockdown_Zones'),
        (u'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\'
         u'Internet Settings\\Zones'),
    ]

    scan_tree = path_filter.PathFilterScanTree(
        paths, path_segment_separator=u'\\')
    self.assertIsNotNone(scan_tree._root_node)

    path = u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows'
    self.assertFalse(scan_tree.CheckPath(path))

    path = (
        u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
        u'Session Manager\\AppCompatCache')
    self.assertTrue(scan_tree.CheckPath(path))

    path = (
        u'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\'
        u'Session Manager\\AppCompatCache')
    self.assertFalse(scan_tree.CheckPath(path))

    path = (
        u'HKEY_LOCAL_MACHINE/System/CurrentControlSet/Control/'
        u'Session Manager/AppCompatCache')
    self.assertTrue(scan_tree.CheckPath(path, path_segment_separator=u'/'))

    scan_tree = path_filter.PathFilterScanTree(
        paths, case_sensitive=False, path_segment_separator=u'\\')
    self.assertIsNotNone(scan_tree._root_node)

    path = u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows'
    self.assertFalse(scan_tree.CheckPath(path))

    path = (
        u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\'
        u'Session Manager\\AppCompatCache')
    self.assertTrue(scan_tree.CheckPath(path))

    path = (
        u'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\'
        u'Session Manager\\AppCompatCache')
    self.assertTrue(scan_tree.CheckPath(path))

    path = (
        u'HKEY_LOCAL_MACHINE/System/CurrentControlSet/Control/'
        u'Session Manager/AppCompatCache')
    self.assertTrue(scan_tree.CheckPath(path, path_segment_separator=u'/'))


if __name__ == '__main__':
  unittest.main()
