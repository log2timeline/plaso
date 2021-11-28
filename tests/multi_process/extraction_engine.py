#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the multi-process processing engine."""

import collections
import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import artifacts
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

    test_engine = extraction_engine.ExtractionMultiProcessEngine(
        maximum_number_of_tasks=100)

    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
        parent=os_path_spec)

    source_configuration = artifacts.SourceConfigurationArtifact(
        path_spec=source_path_spec)

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
            artifacts_path, None, [source_path_spec], session, storage_writer)

        processing_status = test_engine.ProcessSources(
            [source_configuration], storage_writer, session.identifier,
            configuration, storage_file_path=temp_directory)

        number_of_events = storage_writer.GetNumberOfAttributeContainers(
            'event')
        number_of_extraction_warnings = (
            storage_writer.GetNumberOfAttributeContainers(
                'extraction_warning'))
        number_of_recovery_warnings = (
            storage_writer.GetNumberOfAttributeContainers(
                'recovery_warning'))

        parsers_counter = collections.Counter({
            parser_count.name: parser_count.number_of_events
            for parser_count in storage_writer.GetAttributeContainers(
                'parser_count')})

      finally:
        storage_writer.Close()

    self.assertFalse(processing_status.aborted)

    self.assertEqual(number_of_events, 15)
    self.assertEqual(number_of_extraction_warnings, 0)
    self.assertEqual(number_of_recovery_warnings, 0)

    expected_parsers_counter = collections.Counter({
        'filestat': 15,
        'total': 15})
    self.assertEqual(parsers_counter, expected_parsers_counter)


if __name__ == '__main__':
  unittest.main()
