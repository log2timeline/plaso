#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the multi-process processing engine."""

import os
import unittest

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import sessions
from plaso.engine import configurations
from plaso.multi_processing import task_engine
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib


class TaskMultiProcessEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the task multi-process engine."""

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testProcessSources(self):
    """Tests the PreprocessSources and ProcessSources function."""
    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()
    path = shared_test_lib.GetTestFilePath([u'artifacts'])
    registry.ReadFromDirectory(reader, path)

    test_engine = task_engine.TaskMultiProcessEngine(
        maximum_number_of_tasks=100)

    source_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    test_engine.PreprocessSources(registry, [source_path_spec])

    session = sessions.Session()

    configuration = configurations.ProcessingConfiguration()
    configuration.parser_filter_expression = u'filestat'

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, u'storage.plaso')
      storage_writer = storage_zip_file.ZIPStorageFileWriter(
          session, temp_file)

      test_engine.ProcessSources(
          session.identifier, [source_path_spec], storage_writer, configuration)

    # TODO: implement a way to obtain the results without relying
    # on multi-process primitives e.g. by writing to a file.
    # self.assertEqual(storage_writer.number_of_events, 15)


if __name__ == '__main__':
  unittest.main()
