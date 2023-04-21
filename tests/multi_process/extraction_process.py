#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the multi-processing worker process."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import sessions
from plaso.containers import tasks
from plaso.engine import configurations
from plaso.engine import worker
from plaso.lib import definitions
from plaso.multi_process import extraction_process
from plaso.multi_process import plaso_queue
from plaso.multi_process import zeromq_queue

from tests import test_lib as shared_test_lib
from tests.multi_process import test_lib


class TestEventExtractionWorker(worker.EventExtractionWorker):
  """Event extraction worker for testing."""

  # pylint: disable=unused-argument
  def ProcessPathSpec(
      self, parser_mediator, path_spec, excluded_find_specs=None):
    """Processes a path specification.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      path_spec (dfvfs.PathSpec): path specification.
      excluded_find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
         that are excluded from processing.
    """
    return


class WorkerProcessTest(test_lib.MultiProcessingTestCase):
  """Tests the multi-processing worker process."""

  # pylint: disable=protected-access

  _QUEUE_TIMEOUT = 5

  def testInitialization(self):
    """Tests the initialization."""
    with shared_test_lib.TempDirectory() as temp_directory:
      configuration = configurations.ProcessingConfiguration()
      configuration.task_storage_path = temp_directory

      test_process = extraction_process.ExtractionWorkerProcess(
          None, configuration, [], None, name='TestWorker')
      self.assertIsNotNone(test_process)

  def testGetStatus(self):
    """Tests the _GetStatus function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      configuration = configurations.ProcessingConfiguration()
      configuration.task_storage_path = temp_directory

      test_process = extraction_process.ExtractionWorkerProcess(
          None, configuration, [], None, name='TestWorker')
      status_attributes = test_process._GetStatus()

      self.assertIsNotNone(status_attributes)
      self.assertEqual(status_attributes['identifier'], 'TestWorker')
      self.assertEqual(status_attributes['last_activity_timestamp'], 0.0)

      task_storage_writer = self._CreateStorageWriter()
      test_process._parser_mediator = self._CreateParserMediator(
          task_storage_writer)
      status_attributes = test_process._GetStatus()

      self.assertIsNotNone(status_attributes)
      self.assertEqual(status_attributes['identifier'], 'TestWorker')
      self.assertEqual(status_attributes['last_activity_timestamp'], 0.0)

  def testMain(self):
    """Tests the _Main function."""
    output_task_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
        delay_open=True, linger_seconds=0, maximum_items=1,
        name='test output task queue', timeout_seconds=self._QUEUE_TIMEOUT)
    output_task_queue.Open()

    input_task_queue = zeromq_queue.ZeroMQRequestConnectQueue(
        delay_open=True, linger_seconds=0, name='test input task queue',
        port=output_task_queue.port, timeout_seconds=self._QUEUE_TIMEOUT)

    with shared_test_lib.TempDirectory() as temp_directory:
      configuration = configurations.ProcessingConfiguration()
      configuration.task_storage_path = temp_directory

      test_process = extraction_process.ExtractionWorkerProcess(
          input_task_queue, configuration, [], None, name='TestWorker')

      test_process.start()

      output_task_queue.PushItem(plaso_queue.QueueAbort(), block=False)
      output_task_queue.Close(abort=True)

  def testProcessPathSpec(self):
    """Tests the _ProcessPathSpec function."""
    test_file_path = self._GetTestFilePath(['testdir', 'filter_1.txt'])
    self._SkipIfPathNotExists(test_file_path)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)

    with shared_test_lib.TempDirectory() as temp_directory:
      configuration = configurations.ProcessingConfiguration()
      configuration.task_storage_path = temp_directory

      test_process = extraction_process.ExtractionWorkerProcess(
          None, configuration, [], None, name='TestWorker')

      task_storage_writer = self._CreateStorageWriter()
      parser_mediator = self._CreateParserMediator(task_storage_writer)

      extraction_worker = TestEventExtractionWorker()
      test_process._ProcessPathSpec(
          extraction_worker, parser_mediator, path_spec)
      self.assertEqual(parser_mediator._number_of_extraction_warnings, 0)

      test_process._ProcessPathSpec(None, parser_mediator, path_spec)
      self.assertEqual(parser_mediator._number_of_extraction_warnings, 1)

  def testProcessTask(self):
    """Tests the _ProcessTask function."""
    session = sessions.Session()
    with shared_test_lib.TempDirectory() as temp_directory:
      configuration = configurations.ProcessingConfiguration()
      configuration.task_storage_path = temp_directory
      configuration.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

      test_process = extraction_process.ExtractionWorkerProcess(
          None, configuration, [], None, name='TestWorker')
      test_process._extraction_worker = TestEventExtractionWorker()

      task_storage_writer = self._CreateStorageWriter()
      test_process._parser_mediator = self._CreateParserMediator(
          task_storage_writer)

      task = tasks.Task(session_identifier=session.identifier)
      test_process._ProcessTask(task)

  def testStartAndStopProfiling(self):
    """Tests the _StartProfiling and _StopProfiling functions."""
    with shared_test_lib.TempDirectory() as temp_directory:
      configuration = configurations.ProcessingConfiguration()
      configuration.profiling.directory = temp_directory
      configuration.profiling.profilers = set([
          'memory', 'parsers', 'processing', 'serializers', 'storage',
          'task_queue'])
      configuration.task_storage_path = temp_directory

      test_process = extraction_process.ExtractionWorkerProcess(
          None, configuration, [], None, name='TestWorker')
      test_process._extraction_worker = TestEventExtractionWorker()

      test_process._StartProfiling(None)

      test_process._StartProfiling(configuration.profiling)
      test_process._StopProfiling()

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      configuration = configurations.ProcessingConfiguration()
      configuration.task_storage_path = temp_directory

      test_process = extraction_process.ExtractionWorkerProcess(
          None, configuration, [], None, name='TestWorker')
      test_process.SignalAbort()


if __name__ == '__main__':
  unittest.main()
