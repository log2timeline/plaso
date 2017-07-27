#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the single process processing engine."""

import unittest

from artifacts import reader as artifacts_reader
from artifacts import registry as artifacts_registry
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context

from plaso.containers import sessions
from plaso.engine import configurations
from plaso.engine import single_process
from plaso.storage import fake_storage

from tests import test_lib as shared_test_lib


class SingleProcessEngineTest(shared_test_lib.BaseTestCase):
  """Tests for the single process engine object."""

  # pylint: disable=protected-access

  @shared_test_lib.skipUnlessHasTestFile([u'artifacts'])
  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testProcessSources(self):
    """Tests the ProcessSources function."""
    registry = artifacts_registry.ArtifactDefinitionsRegistry()
    reader = artifacts_reader.YamlArtifactsReader()
    path = shared_test_lib.GetTestFilePath([u'artifacts'])
    registry.ReadFromDirectory(reader, path)

    test_engine = single_process.SingleProcessEngine()
    resolver_context = context.Context()
    session = sessions.Session()

    source_path = self._GetTestFilePath([u'ímynd.dd'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    source_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=os_path_spec)

    test_engine.PreprocessSources(registry, [source_path_spec])

    storage_writer = fake_storage.FakeStorageWriter(session)

    configuration = configurations.ProcessingConfiguration()
    configuration.parser_filter_expression = u'filestat'

    test_engine.ProcessSources(
        [source_path_spec], storage_writer, resolver_context, configuration)

    self.assertEqual(storage_writer.number_of_events, 15)


if __name__ == '__main__':
  unittest.main()
