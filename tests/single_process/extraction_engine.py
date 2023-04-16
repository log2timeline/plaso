#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the single process processing engine."""

import collections
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context

from plaso.engine import configurations
from plaso.single_process import extraction_engine
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class SingleProcessEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the single process engine object."""

  # pylint: disable=protected-access

  def testProcessSource(self):
    """Tests the PreprocessSource and ProcessSource functions."""
    test_artifacts_path = self._GetTestFilePath(['artifacts'])
    self._SkipIfPathNotExists(test_artifacts_path)

    test_file_path = self._GetTestFilePath(['ímynd.dd'])
    self._SkipIfPathNotExists(test_file_path)

    test_engine = extraction_engine.SingleProcessEngine()
    test_engine.BuildArtifactsRegistry(test_artifacts_path, None)
    resolver_context = context.Context()

    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
        parent=os_path_spec)

    processing_configuration = configurations.ProcessingConfiguration()
    processing_configuration.data_location = shared_test_lib.DATA_PATH
    processing_configuration.parser_filter_expression = 'filestat'

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    try:
      system_configurations = test_engine.PreprocessSource(
          [source_path_spec], storage_writer)

      processing_status = test_engine.ProcessSource(
          storage_writer, resolver_context, processing_configuration,
          system_configurations, [source_path_spec])

      number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
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
