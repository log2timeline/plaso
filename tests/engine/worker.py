#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the event extraction worker."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context
from dfvfs.path import factory as path_spec_factory

from plaso.containers import sessions
from plaso.engine import configurations
from plaso.engine import knowledge_base
from plaso.engine import worker
from plaso.parsers import mediator as parsers_mediator
from plaso.storage import fake_storage

from tests.analyzers import manager as analyzers_manager_test
from tests import test_lib as shared_test_lib


class EventExtractionWorkerTest(shared_test_lib.BaseTestCase):
  """Tests for the event extraction worker."""

  # pylint: disable=protected-access

  def _TestProcessPathSpec(
      self, storage_writer, path_spec, extraction_worker=None,
      knowledge_base_values=None, process_archives=False):
    """Tests processing a path specification.

    Args:
      storage_writer (StorageWriter): storage writer.
      path_spec (dfvfs.PathSpec): path specification.
      extraction_worker (Optional[EventExtractorWorker]): worker to process the
          pathspec. If None, a new worker will be created.
      knowledge_base_values (Optional[dict]): knowledge base values.
      process_archives (Optional[bool]): whether archive files should be
          processed.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in iter(knowledge_base_values.items()):
        knowledge_base_object.SetValue(identifier, value)

    resolver_context = context.Context()
    mediator = parsers_mediator.ParserMediator(
        storage_writer, knowledge_base_object,
        resolver_context=resolver_context)

    if not extraction_worker:
      configuration = configurations.ExtractionConfiguration()
      configuration.process_archives = process_archives

      extraction_worker = worker.EventExtractionWorker()
      extraction_worker.SetExtractionConfiguration(configuration)

    storage_writer.Open()
    storage_writer.WriteSessionStart()

    extraction_worker.ProcessPathSpec(mediator, path_spec)
    event_source = storage_writer.GetFirstWrittenEventSource()
    while event_source:
      extraction_worker.ProcessPathSpec(mediator, event_source.path_spec)
      event_source = storage_writer.GetNextWrittenEventSource()

    storage_writer.WriteSessionCompletion()
    storage_writer.Close()

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testAnalyzeFileObject(self):
    """Tests the _AnalyzeFileObject function."""
    knowledge_base_values = {u'year': 2016}
    session = sessions.Session()

    storage_writer = fake_storage.FakeStorageWriter(session)

    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in iter(knowledge_base_values.items()):
        knowledge_base_object.SetValue(identifier, value)

    resolver_context = context.Context()
    mediator = parsers_mediator.ParserMediator(
        storage_writer, knowledge_base_object, preferred_year=2016,
        resolver_context=resolver_context)

    extraction_worker = worker.EventExtractionWorker()

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

  @shared_test_lib.skipUnlessHasTestFile([u'syslog'])
  def testProcessPathSpecFile(self):
    """Tests the ProcessPathSpec function on a file."""
    knowledge_base_values = {u'year': 2016}
    session = sessions.Session()

    path_spec = self._GetTestFilePathSpec([u'syslog'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 19)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog.gz'])
  def testProcessPathSpecCompressedFileGZIP(self):
    """Tests the ProcessPathSpec function on a gzip compressed file."""
    knowledge_base_values = {u'year': 2016}
    session = sessions.Session()

    path_spec = self._GetTestFilePathSpec([u'syslog.gz'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 16)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog.bz2'])
  def testProcessPathSpecCompressedFileBZIP2(self):
    """Tests the ProcessPathSpec function on a bzip2 compressed file."""
    knowledge_base_values = {u'year': 2016}
    session = sessions.Session()

    path_spec = self._GetTestFilePathSpec([u'syslog.bz2'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 15)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog.tar'])
  def testProcessPathSpec(self):
    """Tests the ProcessPathSpec function on an archive file."""
    knowledge_base_values = {u'year': 2016}
    session = sessions.Session()

    source_path = self._GetTestFilePath([u'syslog.tar'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=path_spec)

    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 13)

    # Process an archive file without "process archive files" mode.
    path_spec = self._GetTestFilePathSpec([u'syslog.tar'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 3)

    # Process an archive file with "process archive files" mode.
    path_spec = self._GetTestFilePathSpec([u'syslog.tar'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, knowledge_base_values=knowledge_base_values,
        process_archives=True)

    self.assertEqual(storage_writer.number_of_events, 16)

  @shared_test_lib.skipUnlessHasTestFile([u'syslog.tgz'])
  def testProcessPathSpecCompressedArchive(self):
    """Tests the ProcessPathSpec function on a compressed archive file."""
    knowledge_base_values = {u'year': 2016}
    session = sessions.Session()

    source_path = self._GetTestFilePath([u'syslog.tgz'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location=u'/syslog',
        parent=path_spec)

    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 13)

    # Process an archive file with "process archive files" mode.
    path_spec = self._GetTestFilePathSpec([u'syslog.tgz'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, knowledge_base_values=knowledge_base_values,
        process_archives=True)

    self.assertEqual(storage_writer.number_of_events, 17)

  @shared_test_lib.skipUnlessHasTestFile([u'image.vmdk'])
  def testProcessPathSpecVMDK(self):
    """Tests the ProcessPathSpec function on a VMDK with symbolic links."""
    knowledge_base_values = {u'year': 2016}
    session = sessions.Session()

    source_path = self._GetTestFilePath([u'image.vmdk'])
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=source_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VMDK, parent=path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=path_spec)
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, knowledge_base_values=knowledge_base_values)

    self.assertEqual(storage_writer.number_of_events, 18)

  @shared_test_lib.skipUnlessHasTestFile([u'empty_file'])
  def testExtractionWorkerHashing(self):
    """Test that the worker sets up and runs hashing code correctly."""
    extraction_worker = worker.EventExtractionWorker()

    extraction_worker._SetHashers(u'md5')
    self.assertIn(u'hashing', extraction_worker.GetAnalyzerNames())

    knowledge_base_values = {u'year': 2016}
    session = sessions.Session()

    path_spec = self._GetTestFilePathSpec([u'empty_file'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, extraction_worker=extraction_worker,
        knowledge_base_values=knowledge_base_values)

    storage_writer.Open()

    empty_file_md5 = u'd41d8cd98f00b204e9800998ecf8427e'
    for event in storage_writer.GetSortedEvents():
      md5_hash = getattr(event, u'md5_hash', None)
      self.assertEqual(md5_hash, empty_file_md5)

    storage_writer.Close()

  @shared_test_lib.skipUnlessHasTestFile([u'yara.rules'])
  @shared_test_lib.skipUnlessHasTestFile([u'test_pe.exe'])
  def testExtractionWorkerYara(self):
    """Tests that the worker applies Yara matching code correctly."""
    extraction_worker = worker.EventExtractionWorker()

    rule_path = self._GetTestFilePath([u'yara.rules'])
    with open(rule_path, 'r') as rule_file:
      rule_string = rule_file.read()

    extraction_worker._SetYaraRules(rule_string)
    self.assertIn(u'yara', extraction_worker.GetAnalyzerNames())

    knowledge_base_values = {u'year': 2016}
    session = sessions.Session()

    path_spec = self._GetTestFilePathSpec([u'test_pe.exe'])
    storage_writer = fake_storage.FakeStorageWriter(session)
    self._TestProcessPathSpec(
        storage_writer, path_spec, extraction_worker=extraction_worker,
        knowledge_base_values=knowledge_base_values)

    storage_writer.Open()

    expected_yara_match = u'PEfileBasic,PEfile'
    for event in storage_writer.GetSortedEvents():
      yara_match = getattr(event, u'yara_match', None)
      self.assertEqual(yara_match, expected_yara_match)

    storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
