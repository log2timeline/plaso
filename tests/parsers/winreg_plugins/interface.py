#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Registry plugin interface."""

from __future__ import unicode_literals

import unittest

from plaso.parsers.winreg_plugins import interface

from tests.parsers.winreg_plugins import test_lib


class BaseWindowsRegistryKeyFilterTest(test_lib.RegistryPluginTestCase):
  """Tests for the Windows Registry key filter interface."""

  # TODO: add tests for key_paths


class WindowsRegistryKeyPathFilterTest(test_lib.RegistryPluginTestCase):
  """Tests for the Windows Registry key path filter."""

  def testInitialize(self):
    """Tests the __init__ function."""
    path_filter = interface.WindowsRegistryKeyPathFilter('')
    self.assertIsNotNone(path_filter)

  # TODO: add tests for key_paths
  # TODO: add tests for Match


class WindowsRegistryKeyPathPrefixFilterTest(test_lib.RegistryPluginTestCase):
  """Tests for Windows Registry key path prefix filter."""

  def testInitialize(self):
    """Tests the __init__ function."""
    path_filter = interface.WindowsRegistryKeyPathPrefixFilter('')
    self.assertIsNotNone(path_filter)

  # TODO: add tests for key_paths
  # TODO: add tests for Match


class WindowsRegistryKeyPathSuffixFilterTest(test_lib.RegistryPluginTestCase):
  """Tests for Windows Registry key path suffix filter."""

  def testInitialize(self):
    """Tests the __init__ function."""
    path_filter = interface.WindowsRegistryKeyPathSuffixFilter('')
    self.assertIsNotNone(path_filter)

  # TODO: add tests for key_paths
  # TODO: add tests for Match


class WindowsRegistryKeyWithValuesFilterTest(test_lib.RegistryPluginTestCase):
  """Tests for Windows Registry key with values filter."""

  def testInitialize(self):
    """Tests the __init__ function."""
    path_filter = interface.WindowsRegistryKeyWithValuesFilter([])
    self.assertIsNotNone(path_filter)

  # TODO: add tests for key_paths
  # TODO: add tests for Match


class WindowsRegistryPluginTest(test_lib.RegistryPluginTestCase):
  """Tests for the Windows Registry plugin interface."""

  # TODO: add tests for _GetValuesFromKey


if __name__ == '__main__':
  unittest.main()
