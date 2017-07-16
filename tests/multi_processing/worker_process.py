#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the multi-processing worker process."""

from __future__ import unicode_literals

import unittest

from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import fake_path_spec

from plaso.containers import sessions
from plaso.containers import tasks
from plaso.engine import configurations
from plaso.engine import worker
from plaso.multi_processing import multi_process_queue
from plaso.multi_processing import worker_process

from tests import test_lib as shared_test_lib
from tests.multi_processing import test_lib


class TestEventExtractionWorker(worker.EventExtractionWorker):
  """Event extraction worker for testing."""

  def ProcessPathSpec(self, unused_mediator, unused_path_spec):
    """Processes a path specification.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      path_spec (dfvfs.PathSpec): path specification.
    """
    pass


class TestFailureEventExtractionWorker(worker.EventExtractionWorker):
  """Event extraction worker for testing failure."""

  def ProcessPathSpec(self, unused_mediator, unused_path_spec):
    """Processes a path specification.

    Args:
      mediator (ParserMediator): mediates the interactions between
          parsers and other components, such as storage and abort signals.
      path_spec (dfvfs.PathSpec): path specification.

    Raises:
      dfvfs_errors.CacheFullError: cache full error.
    """
    raise dfvfs_errors.CacheFullError()


class WorkerProcessTest(test_lib.MultiProcessingTestCase):
  """Tests the multi-processing worker process."""

  # pylint: disable=protected-access

  def testInitialization(self):
    """Tests the initialization."""
    test_process = worker_process.WorkerProcess(
        None, None, None, None, None, name='TestWorker')
    self.assertIsNotNone(test_process)

  def testGetStatus(self):
    """Tests the _GetStatus function."""
    test_process = worker_process.WorkerProcess(
        None, None, None, None, None, name='TestWorker')
    status_attributes = test_process._GetStatus()

    self.assertIsNotNone(status_attributes)
    self.assertEqual(status_attributes['identifier'], 'TestWorker')
    self.assertEqual(status_attributes['last_activity_timestamp'], 0.0)
    self.assertIsNone(status_attributes['number_of_produced_errors'])

    session = sessions.Session()
    storage_writer = self._CreateStorageWriter(session)
    knowledge_base = self._CreateKnowledgeBase()
    test_process._parser_mediator = self._CreateParserMediator(
        storage_writer, knowledge_base)
    status_attributes = test_process._GetStatus()

    self.assertIsNotNone(status_attributes)
    self.assertEqual(status_attributes['identifier'], 'TestWorker')
    self.assertEqual(status_attributes['last_activity_timestamp'], 0.0)
    self.assertEqual(status_attributes['number_of_produced_errors'], 0)

  def testMain(self):
    """Tests the _Main function."""
    task_queue = multi_process_queue.MultiProcessingQueue(timeout=1)

    configuration = configurations.ProcessingConfiguration()

    test_process = worker_process.WorkerProcess(
        task_queue, None, None, None, configuration, name='TestWorker')
    test_process._abort = True
    test_process._pid = 0

    test_process._Main()

  def testProcessPathSpec(self):
    """Tests the _ProcessPathSpec function."""
    configuration = configurations.ProcessingConfiguration()

    test_process = worker_process.WorkerProcess(
        None, None, None, None, configuration, name='TestWorker')

    session = sessions.Session()
    storage_writer = self._CreateStorageWriter(session)
    knowledge_base = self._CreateKnowledgeBase()
    parser_mediator = self._CreateParserMediator(storage_writer, knowledge_base)

    path_spec = fake_path_spec.FakePathSpec(location='/test/file')

    extraction_worker = TestEventExtractionWorker()
    test_process._ProcessPathSpec(extraction_worker, parser_mediator, path_spec)
    self.assertEqual(parser_mediator._number_of_errors, 0)

    extraction_worker = TestFailureEventExtractionWorker()
    test_process._ProcessPathSpec(extraction_worker, parser_mediator, path_spec)
    self.assertEqual(parser_mediator._number_of_errors, 0)
    self.assertTrue(test_process._abort)

    test_process._ProcessPathSpec(None, parser_mediator, path_spec)
    self.assertEqual(parser_mediator._number_of_errors, 1)

  def testProcessTask(self):
    """Tests the _ProcessTask function."""
    session = sessions.Session()
    storage_writer = self._CreateStorageWriter(session)
    knowledge_base = self._CreateKnowledgeBase()
    configuration = configurations.ProcessingConfiguration()

    test_process = worker_process.WorkerProcess(
        None, storage_writer, knowledge_base, session.identifier, configuration,
        name='TestWorker')
    test_process._parser_mediator = self._CreateParserMediator(
        storage_writer, knowledge_base)

    task = tasks.Task(session_identifier=session.identifier)
    test_process._ProcessTask(task)

  def testStartAndStopProfiling(self):
    """Tests the _StartProfiling and _StopProfiling functions."""
    with shared_test_lib.TempDirectory() as temp_directory:
      configuration = configurations.ProcessingConfiguration()
      configuration.profiling.directory = temp_directory
      configuration.profiling.profilers = set([
          'memory', 'parsers', 'processing', 'serializers'])

      test_process = worker_process.WorkerProcess(
          None, None, None, None, configuration, name='TestWorker')
      test_process._extraction_worker = TestEventExtractionWorker()

      test_process._StartProfiling()
      test_process._StopProfiling()

  def testSignalAbort(self):
    """Tests the SignalAbort function."""
    test_process = worker_process.WorkerProcess(
        None, None, None, None, None, name='TestWorker')
    test_process.SignalAbort()


if __name__ == '__main__':
  unittest.main()
