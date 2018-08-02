#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the preprocess plugins manager."""

from __future__ import unicode_literals

import unittest

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry

from plaso.engine import knowledge_base as knowledge_base_library
from plaso.preprocessors import interface
from plaso.preprocessors import manager

from tests import test_lib as shared_test_lib


class TestArtifactPreprocessorPlugin(interface.ArtifactPreprocessorPlugin):
  """Test artifact preprocessor plugin."""

  ARTIFACT_DEFINITION_NAME = 'TestArtifactDefinition'


  # pylint: disable=unused-argument
  def ParseValueData(self, knowledge_base, value_data):
    """Parses artifact value data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      value_data (object): artifact value data.
    """
    return


class PreprocessPluginsManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the preprocess plugins manager."""

  # pylint: disable=protected-access

  @shared_test_lib.skipUnlessHasTestFile(['artifacts'])
  def testCollectFromFileSystem(self):
    """Tests the CollectFromFileSystem function."""
    path = self._GetTestFilePath(['artifacts'])
    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()
    registry.ReadFromDirectory(reader, path)

    knowledge_base_object = knowledge_base_library.KnowledgeBase()

    _ = knowledge_base_object

    # TODO: implement.
    # manager.PreprocessPluginsManager.CollectFromFileSystem(
    #     registry, knowledge_base_object, None, None)

  # TODO: add tests for CollectFromWindowsRegistry
  # TODO: add tests for GetNames

  def testRegistrationPlugin(self):
    """Tests RegisterPlugin and DeregisterPlugin functions."""
    number_of_plugins = len(manager.PreprocessPluginsManager._plugins)

    manager.PreprocessPluginsManager.RegisterPlugin(
        TestArtifactPreprocessorPlugin)
    self.assertEqual(
        len(manager.PreprocessPluginsManager._plugins), number_of_plugins + 1)

    with self.assertRaises(KeyError):
      manager.PreprocessPluginsManager.RegisterPlugin(
          TestArtifactPreprocessorPlugin)

    manager.PreprocessPluginsManager.DeregisterPlugin(
        TestArtifactPreprocessorPlugin)
    self.assertEqual(
        len(manager.PreprocessPluginsManager._plugins), number_of_plugins)

  # TODO: add tests for RegisterPlugins

  # TODO: add tests for RunPlugins


if __name__ == '__main__':
  unittest.main()
