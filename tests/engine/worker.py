#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the event extraction worker."""

import collections
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context
from dfvfs.path import factory as path_spec_factory

from plaso.containers import events
from plaso.containers import sessions
from plaso.engine import configurations
from plaso.engine import knowledge_base
from plaso.engine import worker
from plaso.parsers import mediator as parsers_mediator
from plaso.storage.fake import writer as fake_writer

from tests.analyzers import manager as analyzers_manager_test
from tests import test_lib as shared_test_lib


class EventExtractionWorkerTest(shared_test_lib.BaseTestCase):
  """Tests for the event extraction worker."""

  # pylint: disable=protected-access

  def _GetEventDataOfEvent(self, storage_writer, event):
    """Retrieves the event data of an event.

    Args:
      storage_writer (FakeStorageWriter): storage writer.
      event (EventObject): event.

    Return:
      EventData: event data corresponding to the event.
    """
    event_data_identifier = event.GetEventDataIdentifier()
    return storage_writer.GetAttributeContainerByIdentifier(
        events.EventData.CONTAINER_TYPE, event_data_identifier)

  def _GetEventDataStreamOfEventData(self, storage_writer, event_data):
    """Retrieves the event data stream of event data.

    Args:
      storage_writer (FakeStorageWriter): storage writer.
      event_data (EventData): event data.

    Return:
      EventDataStream: event data stream corresponding to the event data.
    """
    event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
    return storage_writer.GetAttributeContainerByIdentifier(
        events.EventDataStream.CONTAINER_TYPE, event_data_stream_identifier)

  def _GetTestFilePathSpec(self, path_segments):
    """Retrieves a path specification of a test file in the test data directory.

    Args:
      path_segments (list[str]): components of a path to a test file, relative
          to the test_data directory.

    Returns:
      dfvfs.PathSpec: path specification.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    test_file_path = self._GetTestFilePath(path_segments)
    self._SkipIfPathNotExists(test_file_path)

    return path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

  def _TestProcessPathSpec(
      self, storage_writer, path_spec, expected_event_counters,
      extraction_worker=None, knowledge_base_values=None,
      process_archives=False):
    """Tests processing a path specification.

    Args:
      storage_writer (StorageWriter): storage writer.
      path_spec (dfvfs.PathSpec): path specification.
      expected_event_counters (dict[str, int|list[int]]): expected event
          counters per event data type.
      extraction_worker (Optional[EventExtractorWorker]): worker to process the
          path specification. If None, a new worker will be created.
      knowledge_base_values (Optional[dict]): knowledge base values.
      process_archives (Optional[bool]): whether archive files should be
          processed.
    """
    session = sessions.Session()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        knowledge_base_object.SetValue(identifier, value)

    resolver_context = context.Context()
    parser_mediator = parsers_mediator.ParserMediator(
        knowledge_base_object, resolver_context=resolver_context)
    parser_mediator.SetStorageWriter(storage_writer)

    if not extraction_worker:
      configuration = configurations.ExtractionConfiguration()
      configuration.process_archives = process_archives

      extraction_worker = worker.EventExtractionWorker()
      extraction_worker.SetExtractionConfiguration(configuration)

    storage_writer.Open()

    try:
      session_start = session.CreateSessionStart()
      storage_writer.AddAttributeContainer(session_start)

      extraction_worker.ProcessPathSpec(parser_mediator, path_spec)
      event_source = storage_writer.GetFirstWrittenEventSource()
      while event_source:
        extraction_worker.ProcessPathSpec(
            parser_mediator, event_source.path_spec)
        event_source = storage_writer.GetNextWrittenEventSource()

      session_completion = session.CreateSessionCompletion()
      storage_writer.AddAttributeContainer(session_completion)

      if expected_event_counters:
        self.CheckEventCounters(storage_writer, expected_event_counters)

    finally:
      storage_writer.Close()

  def CheckEventCounters(self, storage_writer, expected_event_counters):
    """Asserts that the number of events per data type matches.

    Args:
      storage_writer (FakeStorageWriter): storage writer.
      expected_event_counters (dict[str, int|list[int]]): expected event
          counters per event data type.
    """
    event_counters = collections.Counter()
    for event in storage_writer.GetSortedEvents():
      event_data_identifier = event.GetEventDataIdentifier()
      event_data = storage_writer.GetAttributeContainerByIdentifier(
          events.EventData.CONTAINER_TYPE, event_data_identifier)

      event_counters[event_data.data_type] += 1

    for data_type, expected_event_count in expected_event_counters.items():
      event_count = event_counters.pop(data_type, 0)
      if isinstance(expected_event_count, list):
        self.assertIn(event_count, expected_event_count)
      else:
        error_message = (
            'data type: "{0:s}" does not match expected value').format(
                data_type)
        self.assertEqual(event_count, expected_event_count, error_message)

    # Ensure there are no events left unaccounted for.
    self.assertEqual(event_counters, collections.Counter())

  def testAnalyzeDataStream(self):
    """Tests the _AnalyzeDataStream function."""
    knowledge_base_values = {'year': 2016}
    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        knowledge_base_object.SetValue(identifier, value)

    resolver_context = context.Context()
    parser_mediator = parsers_mediator.ParserMediator(
        knowledge_base_object, resolver_context=resolver_context)
    parser_mediator.SetPreferredYear(2016)
    parser_mediator.SetStorageWriter(storage_writer)

    extraction_worker = worker.EventExtractionWorker()

    test_analyzer = analyzers_manager_test.TestAnalyzer()
    self.assertEqual(len(test_analyzer.GetResults()), 0)

    extraction_worker._analyzers = [test_analyzer]

    storage_writer.Open()

    session_start = session.CreateSessionStart()
    storage_writer.AddAttributeContainer(session_start)

    file_entry = self._GetTestFileEntry(['syslog.tgz'])
    parser_mediator.SetFileEntry(file_entry)

    display_name = parser_mediator.GetDisplayName()
    event_data_stream = events.EventDataStream()

    extraction_worker._AnalyzeDataStream(
        file_entry, '', display_name, event_data_stream)

    session_completion = session.CreateSessionCompletion()
    storage_writer.AddAttributeContainer(session_completion)

    storage_writer.Close()

    self.assertIsNotNone(event_data_stream)

    event_attribute = getattr(event_data_stream, 'test_result', None)
    self.assertEqual(event_attribute, 'is_vegetable')

  def testAnalyzeFileObject(self):
    """Tests the _AnalyzeFileObject function."""
    knowledge_base_values = {'year': 2016}
    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        knowledge_base_object.SetValue(identifier, value)

    resolver_context = context.Context()
    parser_mediator = parsers_mediator.ParserMediator(
        knowledge_base_object, resolver_context=resolver_context)
    parser_mediator.SetPreferredYear(2016)
    parser_mediator.SetStorageWriter(storage_writer)

    extraction_worker = worker.EventExtractionWorker()

    test_analyzer = analyzers_manager_test.TestAnalyzer()
    self.assertEqual(len(test_analyzer.GetResults()), 0)

    extraction_worker._analyzers = [test_analyzer]

    storage_writer.Open()

    session_start = session.CreateSessionStart()
    storage_writer.AddAttributeContainer(session_start)

    file_entry = self._GetTestFileEntry(['syslog.tgz'])
    parser_mediator.SetFileEntry(file_entry)

    file_object = file_entry.GetFileObject()
    display_name = parser_mediator.GetDisplayName()
    event_data_stream = events.EventDataStream()

    extraction_worker._AnalyzeFileObject(
        file_object, display_name, event_data_stream)

    session_completion = session.CreateSessionCompletion()
    storage_writer.AddAttributeContainer(session_completion)

    storage_writer.Close()

    self.assertIsNotNone(event_data_stream)

    event_attribute = getattr(event_data_stream, 'test_result', None)
    self.assertEqual(event_attribute, 'is_vegetable')

  def testCanSkipDataStream(self):
    """Tests the _CanSkipDataStream function."""
    extraction_worker = worker.EventExtractionWorker()

    file_entry = self._GetTestFileEntry(['syslog.tgz'])

    result = extraction_worker._CanSkipDataStream(file_entry, None)
    self.assertFalse(result)

  def testCanSkipContentExtraction(self):
    """Tests the _CanSkipContentExtraction function."""
    extraction_worker = worker.EventExtractionWorker()

    file_entry = self._GetTestFileEntry(['syslog.tgz'])

    result = extraction_worker._CanSkipContentExtraction(file_entry)
    self.assertFalse(result)

  def testExtractContentFromDataStream(self):
    """Tests the _ExtractContentFromDataStream function."""
    knowledge_base_values = {'year': 2016}
    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        knowledge_base_object.SetValue(identifier, value)

    resolver_context = context.Context()
    parser_mediator = parsers_mediator.ParserMediator(
        knowledge_base_object, resolver_context=resolver_context)
    parser_mediator.SetPreferredYear(2016)
    parser_mediator.SetStorageWriter(storage_writer)

    extraction_worker = worker.EventExtractionWorker()

    test_analyzer = analyzers_manager_test.TestAnalyzer()
    self.assertEqual(len(test_analyzer.GetResults()), 0)

    extraction_worker._analyzers = [test_analyzer]

    storage_writer.Open()

    session_start = session.CreateSessionStart()
    storage_writer.AddAttributeContainer(session_start)

    file_entry = self._GetTestFileEntry(['syslog.tgz'])
    parser_mediator.SetFileEntry(file_entry)

    extraction_worker._ExtractContentFromDataStream(
        parser_mediator, file_entry, '')

    session_completion = session.CreateSessionCompletion()
    storage_writer.AddAttributeContainer(session_completion)

    storage_writer.Close()

    # TODO: check results in storage writer

  def testExtractMetadataFromFileEntry(self):
    """Tests the _ExtractMetadataFromFileEntry function."""
    knowledge_base_values = {'year': 2016}
    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        knowledge_base_object.SetValue(identifier, value)

    resolver_context = context.Context()
    parser_mediator = parsers_mediator.ParserMediator(
        knowledge_base_object, resolver_context=resolver_context)
    parser_mediator.SetPreferredYear(2016)
    parser_mediator.SetStorageWriter(storage_writer)

    extraction_worker = worker.EventExtractionWorker()

    test_analyzer = analyzers_manager_test.TestAnalyzer()
    self.assertEqual(len(test_analyzer.GetResults()), 0)

    extraction_worker._analyzers = [test_analyzer]

    storage_writer.Open()

    session_start = session.CreateSessionStart()
    storage_writer.AddAttributeContainer(session_start)

    file_entry = self._GetTestFileEntry(['syslog.tgz'])
    parser_mediator.SetFileEntry(file_entry)

    extraction_worker._ExtractMetadataFromFileEntry(
        parser_mediator, file_entry, '')

    session_completion = session.CreateSessionCompletion()
    storage_writer.AddAttributeContainer(session_completion)

    storage_writer.Close()

    # TODO: check results in storage writer

  def testGetArchiveTypes(self):
    """Tests the _GetArchiveTypes function."""
    knowledge_base_values = {'year': 2016}
    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        knowledge_base_object.SetValue(identifier, value)

    resolver_context = context.Context()
    parser_mediator = parsers_mediator.ParserMediator(
        knowledge_base_object, resolver_context=resolver_context)
    parser_mediator.SetPreferredYear(2016)
    parser_mediator.SetStorageWriter(storage_writer)

    extraction_worker = worker.EventExtractionWorker()

    test_analyzer = analyzers_manager_test.TestAnalyzer()
    self.assertEqual(len(test_analyzer.GetResults()), 0)

    extraction_worker._analyzers = [test_analyzer]

    storage_writer.Open()

    session_start = session.CreateSessionStart()
    storage_writer.AddAttributeContainer(session_start)

    extraction_worker = worker.EventExtractionWorker()

    path_spec = self._GetTestFilePathSpec(['syslog.tar'])

    type_indicators = extraction_worker._GetArchiveTypes(
        parser_mediator, path_spec)
    self.assertEqual(type_indicators, [dfvfs_definitions.TYPE_INDICATOR_TAR])

    session_completion = session.CreateSessionCompletion()
    storage_writer.AddAttributeContainer(session_completion)

    storage_writer.Close()

  def testGetCompressedStreamTypes(self):
    """Tests the _GetCompressedStreamTypes function."""
    knowledge_base_values = {'year': 2016}
    session = sessions.Session()

    storage_writer = fake_writer.FakeStorageWriter()

    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        knowledge_base_object.SetValue(identifier, value)

    resolver_context = context.Context()
    parser_mediator = parsers_mediator.ParserMediator(
        knowledge_base_object, resolver_context=resolver_context)
    parser_mediator.SetPreferredYear(2016)
    parser_mediator.SetStorageWriter(storage_writer)

    extraction_worker = worker.EventExtractionWorker()

    test_analyzer = analyzers_manager_test.TestAnalyzer()
    self.assertEqual(len(test_analyzer.GetResults()), 0)

    extraction_worker._analyzers = [test_analyzer]

    storage_writer.Open()

    session_start = session.CreateSessionStart()
    storage_writer.AddAttributeContainer(session_start)

    extraction_worker = worker.EventExtractionWorker()

    path_spec = self._GetTestFilePathSpec(['syslog.tgz'])

    type_indicators = extraction_worker._GetCompressedStreamTypes(
        parser_mediator, path_spec)
    self.assertEqual(type_indicators, [dfvfs_definitions.TYPE_INDICATOR_GZIP])

    session_completion = session.CreateSessionCompletion()
    storage_writer.AddAttributeContainer(session_completion)

    storage_writer.Close()

  def testIsMetadataFile(self):
    """Tests the _IsMetadataFile function."""
    extraction_worker = worker.EventExtractionWorker()

    file_entry = self._GetTestFileEntry(['syslog.tgz'])

    result = extraction_worker._IsMetadataFile(file_entry)
    self.assertFalse(result)

  # TODO: add tests for _ProcessArchiveTypes
  # TODO: add tests for _ProcessCompressedStreamTypes
  # TODO: add tests for _ProcessDirectory
  # TODO: add tests for _ProcessFileEntry
  # TODO: add tests for _ProcessFileEntryDataStream
  # TODO: add tests for _ProcessMetadataFile
  # TODO: add tests for _SetHashers
  # TODO: add tests for _SetYaraRules
  # TODO: add tests for GetAnalyzerNames

  def testProcessPathSpecFile(self):
    """Tests the ProcessPathSpec function on a file."""
    knowledge_base_values = {'year': 2016}

    path_spec = self._GetTestFilePathSpec(['syslog'])
    storage_writer = fake_writer.FakeStorageWriter()

    # Typically there are 3 filestat events, but there can be 4 on platforms
    # that support os.stat_result st_birthtime.
    expected_event_counters = {
        'fs:stat': [3, 4],
        'syslog:cron:task_run': 3,
        'syslog:line': 13}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        knowledge_base_values=knowledge_base_values)

  def testProcessPathSpecCompressedFileGZIP(self):
    """Tests the ProcessPathSpec function on a gzip compressed file."""
    knowledge_base_values = {'year': 2016}

    path_spec = self._GetTestFilePathSpec(['syslog.gz'])
    storage_writer = fake_writer.FakeStorageWriter()

    # Typically there are 3 filestat events, but there can be 4 on platforms
    # that support os.stat_result st_birthtime. There is 1 additional filestat
    # event from the .gz file.
    expected_event_counters = {
        'fs:stat': [4, 5],
        'syslog:cron:task_run': 3,
        'syslog:line': 9}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        knowledge_base_values=knowledge_base_values)

  def testProcessPathSpecCompressedFileBZIP2(self):
    """Tests the ProcessPathSpec function on a bzip2 compressed file."""
    knowledge_base_values = {'year': 2016}

    path_spec = self._GetTestFilePathSpec(['syslog.bz2'])
    storage_writer = fake_writer.FakeStorageWriter()

    # Typically there are 3 filestat events, but there can be 4 on platforms
    # that support os.stat_result st_birthtime.
    expected_event_counters = {
        'fs:stat': [3, 4],
        'syslog:cron:task_run': 3,
        'syslog:line': 9}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        knowledge_base_values=knowledge_base_values)

  def testProcessPathSpecCompressedFileXZ(self):
    """Tests the ProcessPathSpec function on a xz compressed file."""
    knowledge_base_values = {'year': 2016}

    path_spec = self._GetTestFilePathSpec(['syslog.xz'])
    storage_writer = fake_writer.FakeStorageWriter()

    # Typically there are 3 filestat events, but there can be 4 on platforms
    # that support os.stat_result st_birthtime.
    expected_event_counters = {
        'fs:stat': [3, 4],
        'syslog:cron:task_run': 3,
        'syslog:line': 9}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        knowledge_base_values=knowledge_base_values)

  def testProcessPathSpec(self):
    """Tests the ProcessPathSpec function on an archive file."""
    knowledge_base_values = {'year': 2016}

    test_file_path = self._GetTestFilePath(['syslog.tar'])
    self._SkipIfPathNotExists(test_file_path)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location='/syslog',
        parent=path_spec)

    storage_writer = fake_writer.FakeStorageWriter()

    expected_event_counters = {
        'fs:stat': 1,
        'syslog:cron:task_run': 3,
        'syslog:line': 9}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        knowledge_base_values=knowledge_base_values)

    # Process an archive file without "process archive files" mode.
    path_spec = self._GetTestFilePathSpec(['syslog.tar'])
    storage_writer = fake_writer.FakeStorageWriter()

    # Typically there are 3 filestat events, but there can be 4 on platforms
    # that support os.stat_result st_birthtime.
    expected_event_counters = {
        'fs:stat': [3, 4]}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        knowledge_base_values=knowledge_base_values)

    # Process an archive file with "process archive files" mode.
    path_spec = self._GetTestFilePathSpec(['syslog.tar'])
    storage_writer = fake_writer.FakeStorageWriter()

    # Typically there are 3 filestat events, but there can be 4 on platforms
    # that support os.stat_result st_birthtime. There is 1 additional filestat
    # event from the .tar file.
    expected_event_counters = {
        'fs:stat': [4, 5],
        'syslog:cron:task_run': 3,
        'syslog:line': 9}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        knowledge_base_values=knowledge_base_values, process_archives=True)

  def testProcessPathSpecCompressedArchive(self):
    """Tests the ProcessPathSpec function on a compressed archive file."""
    knowledge_base_values = {'year': 2016}

    test_file_path = self._GetTestFilePath(['syslog.tgz'])
    self._SkipIfPathNotExists(test_file_path)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TAR, location='/syslog',
        parent=path_spec)

    storage_writer = fake_writer.FakeStorageWriter()

    expected_event_counters = {
        'fs:stat': 1,
        'syslog:cron:task_run': 3,
        'syslog:line': 9}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        knowledge_base_values=knowledge_base_values)

    # Process an archive file with "process archive files" mode.
    path_spec = self._GetTestFilePathSpec(['syslog.tgz'])
    storage_writer = fake_writer.FakeStorageWriter()

    # Typically there are 3 filestat events, but there can be 4 on platforms
    # that support os.stat_result st_birthtime. There are 2 additional filestat
    # events from the .tar and .gz files.
    expected_event_counters = {
        'fs:stat': [5, 6],
        'syslog:cron:task_run': 3,
        'syslog:line': 9}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        knowledge_base_values=knowledge_base_values, process_archives=True)

  def testProcessPathSpecVMDK(self):
    """Tests the ProcessPathSpec function on a VMDK with symbolic links."""
    knowledge_base_values = {'year': 2016}

    test_file_path = self._GetTestFilePath(['image.vmdk'])
    self._SkipIfPathNotExists(test_file_path)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VMDK, parent=path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location='/',
        parent=path_spec)
    storage_writer = fake_writer.FakeStorageWriter()

    expected_event_counters = {
        'fs:stat': 18}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        knowledge_base_values=knowledge_base_values)

  # TODO: add tests for SetExtractionConfiguration
  # TODO: add tests for SetAnalyzersProfiler
  # TODO: add tests for SetProcessingProfiler
  # TODO: add tests for SignalAbort

  def testExtractionWorkerHashing(self):
    """Test that the worker sets up and runs hashing code correctly."""
    extraction_worker = worker.EventExtractionWorker()

    extraction_worker._SetHashers('md5')
    self.assertIn('hashing', extraction_worker.GetAnalyzerNames())

    knowledge_base_values = {'year': 2016}

    path_spec = self._GetTestFilePathSpec(['empty_file'])
    storage_writer = fake_writer.FakeStorageWriter()

    # Typically there are 3 filestat events, but there can be 4 on platforms
    # that support os.stat_result st_birthtime.
    expected_event_counters = {
        'fs:stat': [3, 4]}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        extraction_worker=extraction_worker,
        knowledge_base_values=knowledge_base_values)

    storage_writer.Open()

    empty_file_md5 = 'd41d8cd98f00b204e9800998ecf8427e'
    for event in storage_writer.GetSortedEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      event_data_stream = self._GetEventDataStreamOfEventData(
          storage_writer, event_data)

      self.assertEqual(event_data_stream.md5_hash, empty_file_md5)

    storage_writer.Close()

  def testExtractionWorkerYara(self):
    """Tests that the worker applies Yara matching code correctly."""
    yara_rule_path = self._GetTestFilePath(['rules.yara'])
    self._SkipIfPathNotExists(yara_rule_path)

    with open(yara_rule_path, 'r', encoding='utf-8') as file_object:
      rule_string = file_object.read()

    extraction_worker = worker.EventExtractionWorker()
    extraction_worker._SetYaraRules(rule_string)
    self.assertIn('yara', extraction_worker.GetAnalyzerNames())

    knowledge_base_values = {'year': 2016}

    path_spec = self._GetTestFilePathSpec(['test_pe.exe'])
    storage_writer = fake_writer.FakeStorageWriter()

    # Typically there are 3 filestat events, but there can be 4 on platforms
    # that support os.stat_result st_birthtime.
    expected_event_counters = {
        'fs:stat': [3, 4],
        'pe': 3}

    self._TestProcessPathSpec(
        storage_writer, path_spec, expected_event_counters,
        extraction_worker=extraction_worker,
        knowledge_base_values=knowledge_base_values)

    storage_writer.Open()

    expected_yara_match = 'PEfileBasic,PEfile'
    for event in storage_writer.GetSortedEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      event_data_stream = self._GetEventDataStreamOfEventData(
          storage_writer, event_data)

      self.assertEqual(event_data_stream.yara_match, expected_yara_match)

    storage_writer.Close()


if __name__ == '__main__':
  unittest.main()
