#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
    self.assertEquals(
        len(manager.PreprocessPluginsManager._plugin_classes),
        number_of_plugins + 1)

    with self.assertRaises(KeyError):
      manager.PreprocessPluginsManager.RegisterPlugin(TestPreprocessPlugin)

    manager.PreprocessPluginsManager.DeregisterPlugin(TestPreprocessPlugin)
    self.assertEquals(
        len(manager.PreprocessPluginsManager._plugin_classes),
        number_of_plugins)


if __name__ == '__main__':
  unittest.main()
