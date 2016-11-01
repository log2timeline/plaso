#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the preprocess plugins manager."""

import unittest

from plaso.preprocessors import interface
from plaso.preprocessors import manager


class TestFileSystemPreprocessPlugin(interface.FileSystemPreprocessPlugin):
  """Test file system preprocess plugin."""

  def Run(self, unused_searcher, unused_knowledge_base):
    """Runs the plugin to determine the value of the preprocessing attribute.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
    """
    return


class TestWindowsRegistryKeyPreprocessPlugin(
    interface.WindowsRegistryKeyPreprocessPlugin):
  """Test Windows Registry key preprocess plugin."""

  def _ParseKey(self, unused_knowledge_base, unused_registry_key):
    """Parses a Windows Registry key for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      registry_key (WinRegistryKey): Windows Registry key.
    """
    return


class PreprocessPluginsManagerTest(unittest.TestCase):
  """Tests for the preprocess plugins manager."""

  # pylint: disable=protected-access

  def testRegistrationFileSystemPreprocessPlugin(self):
    """Tests the RegisterPlugin and DeregisterPlugin functions."""
    number_of_plugins = len(
        manager.PreprocessPluginsManager._file_system_plugin_classes)

    manager.PreprocessPluginsManager.RegisterPlugin(
        TestFileSystemPreprocessPlugin)
    self.assertEqual(
        len(manager.PreprocessPluginsManager._file_system_plugin_classes),
        number_of_plugins + 1)

    with self.assertRaises(KeyError):
      manager.PreprocessPluginsManager.RegisterPlugin(
          TestFileSystemPreprocessPlugin)

    manager.PreprocessPluginsManager.DeregisterPlugin(
        TestFileSystemPreprocessPlugin)
    self.assertEqual(
        len(manager.PreprocessPluginsManager._file_system_plugin_classes),
        number_of_plugins)

  def testRegistrationWindowsRegistryKeyPreprocessPlugin(self):
    """Tests the RegisterPlugin and DeregisterPlugin functions."""
    number_of_plugins = len(
        manager.PreprocessPluginsManager._registry_plugin_classes)

    manager.PreprocessPluginsManager.RegisterPlugin(
        TestWindowsRegistryKeyPreprocessPlugin)
    self.assertEqual(
        len(manager.PreprocessPluginsManager._registry_plugin_classes),
        number_of_plugins + 1)

    with self.assertRaises(KeyError):
      manager.PreprocessPluginsManager.RegisterPlugin(
          TestWindowsRegistryKeyPreprocessPlugin)

    manager.PreprocessPluginsManager.DeregisterPlugin(
        TestWindowsRegistryKeyPreprocessPlugin)
    self.assertEqual(
        len(manager.PreprocessPluginsManager._registry_plugin_classes),
        number_of_plugins)


if __name__ == '__main__':
  unittest.main()
