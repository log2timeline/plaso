#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the single process processing engine."""

import collections
import unittest

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context

from plaso.containers import sessions
from plaso.engine import configurations
from plaso.single_process import extraction_engine
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class SingleProcessEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the single process engine object."""

  # pylint: disable=protected-access

  def testProcessSources(self):
    """Tests the ProcessSources function."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()
    registry.ReadFromDirectory(reader, test_artifacts_path)

    test_engine = extraction_engine.SingleProcessEngine()
    resolver_context = context.Context()

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
        parent=os_path_spec)

    session = sessions.Session()

    configuration = configurations.ProcessingConfiguration()
    configuration.parser_filter_expression = 'filestat'

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      test_engine.PreprocessSources(
          registry, [source_path_spec], session, storage_writer)

      test_engine.ProcessSources(
          session, [source_path_spec], storage_writer, resolver_context,
          configuration)

    finally:
      storage_writer.Close()

    self.assertEqual(storage_writer.number_of_events, 15)
    self.assertEqual(storage_writer.number_of_extraction_warnings, 0)
    self.assertEqual(storage_writer.number_of_recovery_warnings, 0)

    expected_parsers_counter = collections.Counter({
        'filestat': 15,
        'total': 15
    })
    self.assertEqual(session.parsers_counter, expected_parsers_counter)


if __name__ == '__main__':
  unittest.main()
