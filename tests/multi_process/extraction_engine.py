#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the multi-process processing engine."""

import os
import unittest

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import sessions
from plaso.lib import definitions
from plaso.engine import configurations
from plaso.multi_process import extraction_engine
from plaso.storage.sqlite import writer as sqlite_writer

from tests import test_lib as shared_test_lib


class ExtractionMultiProcessEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the task-based multi-process extraction engine."""

  def testProcessSources(self):
    """Tests the PreprocessSources and ProcessSources function."""
    artifacts_path = shared_test_lib.GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(artifacts_path)

    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()
    registry.ReadFromDirectory(reader, artifacts_path)

    test_engine = extraction_engine.ExtractionMultiProcessEngine(
        maximum_number_of_tasks=100)

    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
        parent=os_path_spec)

    session = sessions.Session()

    configuration = configurations.ProcessingConfiguration()
    configuration.parser_filter_expression = 'filestat'
    configuration.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

    with shared_test_lib.TempDirectory() as temp_directory:
      temp_file = os.path.join(temp_directory, 'storage.plaso')
      storage_writer = sqlite_writer.SQLiteStorageFileWriter()
      storage_writer.Open(path=temp_file)

      try:
        test_engine.PreprocessSources(
            registry, [source_path_spec], session, storage_writer)

        test_engine.ProcessSources(
            session, [source_path_spec], storage_writer, configuration,
            storage_file_path=temp_directory)

      finally:
        storage_writer.Close()

    self.assertEqual(storage_writer.number_of_events, 15)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)


if __name__ == '__main__':
  unittest.main()
