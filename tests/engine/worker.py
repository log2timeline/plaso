#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the worker."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.engine import worker
from plaso.parsers import mediator as parsers_mediator
from plaso.storage import fake_storage

from tests.analyzers import manager as analyzers_manager_test
from tests import test_lib as shared_test_lib


class EventExtractionWorkerTest(shared_test_lib.BaseTestCase):
  """Tests for the worker object."""

  # pylint: disable=protected-access

  def _GetTestFileEntry(self, path_segments):
    """Creates a file entry that references a file in the test data directory.

    Args:
      path_segments (list[str]): components of a path to a test file, relative
          to the test_data directory.

    Returns:
      dfvfs.FileEntry: file entry.
    """
    path = self._GetTestFilePath(path_segments)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=path)
    return path_spec_resolver.Resolver.OpenFileEntry(path_spec)

  def _GetTestFilePathSpec(self, path_segments):
    """Retrieves a path specification of a test file in the test data directory.

    Args:
      path_segments (list[str]): components of a path to a test file, relative
          to the test_data directory.

    Returns:
      A path specification (instance of dfvfs.PathSpec).
    """
    source_path = self._GetTestFilePath(path_segments)
    return path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)

  def _TestProcessPathSpec(
      self, storage_writer, path_spec, extraction_worker=None,
      process_archive_files=False):
    """Tests processing a path specification.

    Args:
      storage_writer (StorageWriter): storage writer.
      path_spec (dfvfs.PathSpec): path specification.
      extraction_worker (Optional[EventExtractorWorker]): worker to process the
          pathspec. If None, a new worker will be created.
      process_archive_files (Optional[bool]): whether archive files should be
          processed.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    mediator = parsers_mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    if not extraction_worker:
      resolver_context = context.Context()

      extraction_worker = worker.EventExtractionWorker(
          resolver_context, process_archive_files=process_archive_files)

    storage_writer.Open()
    storage_writer.WriteSessionStart()

    extraction_worker.ProcessPathSpec(mediator, path_spec)
    event_source = storage_writer.GetFirstWrittenEventSource()
    while event_source:
      extraction_worker.ProcessPathSpec(mediator, event_source.path_spec)
      event_source = storage_writer.GetNextWrittenEventSource()

    storage_writer.WriteSessionCompletion()
    storage_writer.Close()

  def testAnalyzeFileObject(self):
    """Tests the _AnalyzeFileObject function."""
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    knowledge_base_object = knowledge_base.KnowledgeBase()
    mediator = parsers_mediator.ParserMediator(
        storage_writer, knowledge_base_object)

    resolver_context = context.Context()
    extraction_worker = worker.EventExtractionWorker(resolver_context)

    test_analyzer = analyzers_manager_test.TestAnalyzer()
    self.assertEqual(len(test_analyzer.GetResults()), 0)

    extraction_worker._analyzers = [test_analyzer]

    file_entry = self._GetTestFileEntry([u'ímynd.dd'])
    mediator.SetFileEntry(file_entry)

    file_object = file_entry.GetFileObject()

    try:
      extraction_worker._AnalyzeFileObject(mediator, file_object)
    finally:
      file_object.close()

    self.assertEqual(len(mediator._extra_event_attributes), 1)

    event_attribute = mediator._extra_event_attributes.get(u'test_result', None)
    self.assertEqual(event_attribute, u'is_vegetable')

  def testProcessPathSpec(self):
    """Tests the ProcessPathSpec function."""
    session = sessions.Session()

    # Process a file.
    path_spec = self._GetTestFilePathSpec([u'syslog'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 17)

    # Process a compressed file.
    path_spec = self._GetTestFilePathSpec([u'syslog.gz'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 16)

    path_spec = self._GetTestFilePathSpec([u'syslog.bz2'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 15)

    # Process a file in an archive.
    source_path = self._GetTestFilePath([u'syslog.tar'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=path_spec)

    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 13)

    # Process an archive file without "process archive files" mode.
    path_spec = self._GetTestFilePathSpec([u'syslog.tar'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 3)

    # Process an archive file with "process archive files" mode.
    path_spec = self._GetTestFilePathSpec([u'syslog.tar'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, process_archive_files=True)

    self.assertEqual(storage_writer.number_of_events, 16)

    # Process a file in a compressed archive.
    source_path = self._GetTestFilePath([u'syslog.tgz'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=path_spec)

    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 13)

    # Process an archive file with "process archive files" mode.
    path_spec = self._GetTestFilePathSpec([u'syslog.tgz'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, process_archive_files=True)

    self.assertEqual(storage_writer.number_of_events, 17)

    # Process a storage media image with a symbolic link.
    source_path = self._GetTestFilePath([u'image.vmdk'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VMDK, parent=path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=path_spec)
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(storage_writer, path_spec)

    self.assertEqual(storage_writer.number_of_events, 18)

  def testExtractionWorkerHashing(self):
    """Test that the worker sets up and runs hashing code correctly."""
    resolver_context = context.Context()
    extraction_worker = worker.EventExtractionWorker(resolver_context)

    extraction_worker.SetHashers(u'md5')
    self.assertIn(u'hashing', extraction_worker.GetAnalyzerNames())

    session = sessions.Session()
    empty_file_md5 = u'd41d8cd98f00b204e9800998ecf8427e'
    path_spec = self._GetTestFilePathSpec([u'empty_file'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, extraction_worker=extraction_worker)

    for event in storage_writer.events:
      self.assertEqual(getattr(event, u'md5_hash', None), empty_file_md5)

  def testExtractionWorkerYara(self):
    """Tests that the worker applies Yara matching code correctly."""
    resolver_context = context.Context()
    extraction_worker = worker.EventExtractionWorker(resolver_context)

    rule_path = self._GetTestFilePath([u'yara.rules'])
    with open(rule_path, 'r') as rule_file:
      rule_string = rule_file.read()

    extraction_worker.SetYaraRules(rule_string)
    self.assertIn(u'yara', extraction_worker.GetAnalyzerNames())

    session = sessions.Session()
    path_spec = self._GetTestFilePathSpec([u'test_pe.exe'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, extraction_worker=extraction_worker)

    expected_yara_match = u'PEfileBasic,PEfile'
    for event in storage_writer.events:
      yara_match = getattr(event, u'yara_match', None)
      self.assertEqual(yara_match, expected_yara_match)


if __name__ == '__main__':
  unittest.main()
