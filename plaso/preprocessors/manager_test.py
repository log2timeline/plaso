#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the preprocess plugins manager."""

import unittest

from plaso.preprocessors import interface
from plaso.preprocessors import manager


class TestPreprocessPlugin(interface.PreprocessPlugin):
  """Preprocess test plugin."""

  def GetValue(self, searcher, unused_knowledge_base):
    """Returns the path as found by the searcher.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.

    Returns:
      The first path location string.

    Raises:
      PreProcessFail: if the path could not be found.
    """
    return


class PreprocessPluginsManagerTest(unittest.TestCase):
  """Tests for the preprocess plugins manager."""

  def testRegistration(self):
    """Tests the RegisterPlugin and DeregisterPlugin functions."""
    # pylint: disable=protected-access
    number_of_plugins = len(manager.PreprocessPluginsManager._plugin_classes)

    manager.PreprocessPluginsManager.RegisterPlugin(TestPreprocessPlugin)
    self.assertEqual(
        len(manager.PreprocessPluginsManager._plugin_classes),
        number_of_plugins + 1)

    with self.assertRaises(KeyError):
      manager.PreprocessPluginsManager.RegisterPlugin(TestPreprocessPlugin)

    manager.PreprocessPluginsManager.DeregisterPlugin(TestPreprocessPlugin)
    self.assertEqual(
        len(manager.PreprocessPluginsManager._plugin_classes),
        number_of_plugins)


if __name__ == '__main__':
  unittest.main()
