#!/usr/bin/env python3
"""Tests for the multi-processing worker process."""

import os
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
from plaso.storage import factory as storage_factory

from tests import test_lib as shared_test_lib
from tests.multi_process import test_lib


class TestEventExtractionWorker(worker.EventExtractionWorker):
    """Event extraction worker for testing."""

    # pylint: disable=unused-argument
    def ProcessPathSpec(self, parser_mediator, path_spec, excluded_find_specs=None):
        """Processes a path specification.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          path_spec (dfvfs.PathSpec): path specification.
          excluded_find_specs (Optional[list[dfvfs.FindSpec]]): find specifications
             that are excluded from processing.
        """
        return


class TestEventExtractionWorkerWithMissingDirectory(worker.EventExtractionWorker):
    """Event extraction worker for testing with a missing local directory."""

    def __init__(self, missing_path_spec):
        """Initializes an event extraction worker for testing.

        Args:
          missing_path_spec (dfvfs.PathSpec): path specification of a local
              directory that does not exist.
        """
        super().__init__()
        self._missing_path_spec = missing_path_spec

    def PopLocalDirectoryPathSpec(self):
        """Pops the path specification of a sub directory to process locally.

        Returns:
          dfvfs.PathSpec: path specification of a sub directory or None if there
              are no more sub directories to process locally.
        """
        if self._missing_path_spec:
            path_spec = self._missing_path_spec
            self._missing_path_spec = None
            return path_spec

        return super().PopLocalDirectoryPathSpec()


class TestExtractionWorkerProcess(extraction_process.ExtractionWorkerProcess):
    """Extraction worker process for testing."""

    _MAXIMUM_NUMBER_OF_LOCAL_DIRECTORIES = 1


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
                None, configuration, [], [], None, name="TestWorker"
            )
            self.assertIsNotNone(test_process)

    def testGetStatus(self):
        """Tests the _GetStatus function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            configuration = configurations.ProcessingConfiguration()
            configuration.task_storage_path = temp_directory

            test_process = extraction_process.ExtractionWorkerProcess(
                None, configuration, [], [], None, name="TestWorker"
            )
            status_attributes = test_process._GetStatus()

            self.assertIsNotNone(status_attributes)
            self.assertEqual(status_attributes["identifier"], "TestWorker")
            self.assertEqual(status_attributes["last_activity_timestamp"], 0.0)

            task_storage_writer = self._CreateStorageWriter()
            test_process._parser_mediator = self._CreateParserMediator(
                task_storage_writer
            )
            status_attributes = test_process._GetStatus()

            self.assertIsNotNone(status_attributes)
            self.assertEqual(status_attributes["identifier"], "TestWorker")
            self.assertEqual(status_attributes["last_activity_timestamp"], 0.0)

    def testMain(self):
        """Tests the _Main function."""
        output_task_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
            delay_open=True,
            linger_seconds=0,
            maximum_items=1,
            name="test output task queue",
            timeout_seconds=self._QUEUE_TIMEOUT,
        )
        output_task_queue.Open()

        input_task_queue = zeromq_queue.ZeroMQRequestConnectQueue(
            delay_open=True,
            linger_seconds=0,
            name="test input task queue",
            port=output_task_queue.port,
            timeout_seconds=self._QUEUE_TIMEOUT,
        )
        with shared_test_lib.TempDirectory() as temp_directory:
            configuration = configurations.ProcessingConfiguration()
            configuration.task_storage_path = temp_directory

            test_process = extraction_process.ExtractionWorkerProcess(
                input_task_queue, configuration, [], [], None, name="TestWorker"
            )
            test_process.start()

            output_task_queue.PushItem(plaso_queue.QueueAbort(), block=False)
            output_task_queue.Close(abort=True)

    def testProcessPathSpec(self):
        """Tests the _ProcessPathSpec function."""
        test_file_path = self._GetTestFilePath(["testdir", "filter_1.txt"])
        self._SkipIfPathNotExists(test_file_path)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        with shared_test_lib.TempDirectory() as temp_directory:
            configuration = configurations.ProcessingConfiguration()
            configuration.task_storage_path = temp_directory

            test_process = extraction_process.ExtractionWorkerProcess(
                None, configuration, [], [], None, name="TestWorker"
            )
            task_storage_writer = self._CreateStorageWriter()
            parser_mediator = self._CreateParserMediator(task_storage_writer)

            extraction_worker = TestEventExtractionWorker()
            test_process._ProcessPathSpec(extraction_worker, parser_mediator, path_spec)
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
                None, configuration, [], [], None, name="TestWorker"
            )
            test_process._extraction_worker = TestEventExtractionWorker()

            task_storage_writer = self._CreateStorageWriter()
            test_process._parser_mediator = self._CreateParserMediator(
                task_storage_writer
            )
            task = tasks.Task(session_identifier=session.identifier)
            test_process._ProcessTask(task)

    def testProcessTaskWithLocalDirectories(self):
        """Tests the _ProcessTask function with local directory processing."""
        test_file_path = self._GetTestFilePath(["ext4.raw"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_EXT, location="/", parent=os_path_spec
        )

        session = sessions.Session()
        with shared_test_lib.TempDirectory() as temp_directory:
            configuration = configurations.ProcessingConfiguration()
            configuration.task_storage_path = temp_directory
            configuration.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

            os.mkdir(os.path.join(temp_directory, "processed"))

            test_process = TestExtractionWorkerProcess(
                None, configuration, [], [], None, name="TestWorker"
            )
            test_process._extraction_worker = worker.EventExtractionWorker()
            test_process._extraction_worker.SetLocalDirectoryProcessing(True)

            task_storage_writer = self._CreateStorageWriter()
            test_process._parser_mediator = self._CreateParserMediator(
                task_storage_writer
            )
            task = tasks.Task(session_identifier=session.identifier)
            task.path_spec = path_spec
            test_process._ProcessTask(task)

            self.assertEqual(test_process._number_of_consumed_sources, 2)
            self.assertIsNone(
                test_process._extraction_worker.PopLocalDirectoryPathSpec()
            )

            storage_file_path = test_process._GetProcessedStorageFilePath(
                definitions.STORAGE_FORMAT_SQLITE, task
            )
            storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
                storage_file_path
            )
            try:
                event_source_locations = sorted(
                    event_source.path_spec.location
                    for event_source in storage_reader.GetAttributeContainers(
                        "event_source"
                    )
                )
            finally:
                storage_reader.Close()

        # The sub directories are processed depth-first, where "/a_directory" is
        # processed as part of the task and "/lost+found" is produced as an event
        # source, since only 1 sub directory is processed as part of the task.
        self.assertEqual(
            event_source_locations,
            [
                "/a_directory/a_file",
                "/a_directory/another_file",
                "/a_link",
                "/lost+found",
                "/passwords.txt",
            ],
        )

    def testProcessTaskWithMissingLocalDirectory(self):
        """Tests the _ProcessTask function with a missing local directory."""
        session = sessions.Session()
        with shared_test_lib.TempDirectory() as temp_directory:
            configuration = configurations.ProcessingConfiguration()
            configuration.task_storage_path = temp_directory
            configuration.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

            os.mkdir(os.path.join(temp_directory, "processed"))

            missing_path = os.path.join(temp_directory, "missing")
            missing_path_spec = path_spec_factory.Factory.NewPathSpec(
                dfvfs_definitions.TYPE_INDICATOR_OS, location=missing_path
            )
            path_spec = path_spec_factory.Factory.NewPathSpec(
                dfvfs_definitions.TYPE_INDICATOR_OS,
                location=os.path.join(temp_directory, "processed"),
            )

            test_process = extraction_process.ExtractionWorkerProcess(
                None, configuration, [], [], None, name="TestWorker"
            )
            test_process._extraction_worker = (
                TestEventExtractionWorkerWithMissingDirectory(missing_path_spec)
            )
            test_process._extraction_worker.SetLocalDirectoryProcessing(True)

            task_storage_writer = self._CreateStorageWriter()
            test_process._parser_mediator = self._CreateParserMediator(
                task_storage_writer
            )
            task = tasks.Task(session_identifier=session.identifier)
            task.path_spec = path_spec
            test_process._ProcessTask(task)

            storage_file_path = test_process._GetProcessedStorageFilePath(
                definitions.STORAGE_FORMAT_SQLITE, task
            )
            storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
                storage_file_path
            )
            try:
                event_source_locations = [
                    event_source.path_spec.location
                    for event_source in storage_reader.GetAttributeContainers(
                        "event_source"
                    )
                ]
            finally:
                storage_reader.Close()

        # A local directory that cannot be opened is produced as an event source,
        # so that the foreman produces an extraction warning for it.
        self.assertEqual(event_source_locations, [missing_path])

    def testStartAndStopProfiling(self):
        """Tests the _StartProfiling and _StopProfiling functions."""
        with shared_test_lib.TempDirectory() as temp_directory:
            configuration = configurations.ProcessingConfiguration()
            configuration.profiling.directory = temp_directory
            configuration.profiling.profilers = set(
                [
                    "memory",
                    "parsers",
                    "processing",
                    "serializers",
                    "storage",
                    "task_queue",
                ]
            )
            configuration.task_storage_path = temp_directory

            test_process = extraction_process.ExtractionWorkerProcess(
                None, configuration, [], [], None, name="TestWorker"
            )
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
                None, configuration, [], [], None, name="TestWorker"
            )
            test_process.SignalAbort()


if __name__ == "__main__":
    unittest.main()
