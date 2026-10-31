#!/usr/bin/env python3
"""Tests the multi-process processing engine."""

import collections
import multiprocessing
import os
import time
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import event_sources
from plaso.containers import sessions
from plaso.containers import warnings
from plaso.lib import definitions
from plaso.engine import configurations
from plaso.multi_process import extraction_engine
from plaso.storage import factory as storage_factory
from plaso.storage.fake import writer as fake_writer
from plaso.storage.sqlite import writer as sqlite_writer

from tests import test_lib as shared_test_lib


class TestExtractionMultiProcessEngineWithPathSpecsLimit(
    extraction_engine.ExtractionMultiProcessEngine
):
    """Multi-process extraction engine with a small path specifications limit."""

    _MAXIMUM_NUMBER_OF_PATH_SPECS_PER_TASK = 2


class TestExtractionMultiProcessEngineWithDataSizeLimit(
    extraction_engine.ExtractionMultiProcessEngine
):
    """Multi-process extraction engine with a small task data size limit."""

    _MAXIMUM_TASK_DATA_SIZE = 1


class ExtractionMultiProcessEngineTest(shared_test_lib.BaseTestCase):
    """Tests for the task-based multi-process extraction engine."""

    def _ProcessSource(self, source_path_spec):
        """Tests the PreprocessSource and ProcessSource functions.

        Args:
          path_spec (dfvfs.PathSpec): path specification of the source.
        """
        test_artifacts_path = shared_test_lib.GetTestFilePath(["artifacts"])
        self._SkipIfPathNotExists(test_artifacts_path)

        test_engine = extraction_engine.ExtractionMultiProcessEngine(
            maximum_number_of_tasks=100
        )
        test_engine.BuildArtifactsRegistry(test_artifacts_path, None)

        session = sessions.Session()

        processing_configuration = configurations.ProcessingConfiguration()
        processing_configuration.data_location = shared_test_lib.DATA_PATH
        processing_configuration.parser_filter_expression = "filestat"
        processing_configuration.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

        with shared_test_lib.TempDirectory() as temp_directory:
            temp_file = os.path.join(temp_directory, "storage.plaso")
            storage_writer = sqlite_writer.SQLiteStorageWriter()
            storage_writer.Open(path=temp_file)

            try:
                system_configurations = test_engine.PreprocessSource(
                    [source_path_spec], storage_writer
                )
                # The method is named ProcessSourceMulti because pylint 2.6.0 and later
                # gets confused about keyword arguments when ProcessSource is used.
                processing_status = test_engine.ProcessSourceMulti(
                    storage_writer,
                    session.identifier,
                    processing_configuration,
                    system_configurations,
                    [source_path_spec],
                    storage_file_path=temp_directory,
                )
                number_of_events = storage_writer.GetNumberOfAttributeContainers(
                    "event"
                )
                number_of_extraction_warnings = (
                    storage_writer.GetNumberOfAttributeContainers("extraction_warning")
                )
                number_of_recovery_warnings = (
                    storage_writer.GetNumberOfAttributeContainers("recovery_warning")
                )
                parsers_counter = collections.Counter(
                    {
                        parser_count.name: parser_count.number_of_events
                        for parser_count in storage_writer.GetAttributeContainers(
                            "parser_count"
                        )
                    }
                )

            finally:
                storage_writer.Close()

        self.assertFalse(processing_status.aborted)

        self.assertEqual(number_of_events, 15)
        self.assertEqual(number_of_extraction_warnings, 0)
        self.assertEqual(number_of_recovery_warnings, 0)

        expected_parsers_counter = collections.Counter({"filestat": 15, "total": 15})
        self.assertEqual(parsers_counter, expected_parsers_counter)

    def _CreateEventSourceHeap(self):
        """Creates an event source heap with a directory and 3 regular files.

        Returns:
          _EventSourceHeap: event source heap.
        """
        # pylint: disable=protected-access
        event_source_heap = extraction_engine._EventSourceHeap()

        test_directory_path = self._GetTestFilePath(["testdir"])
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_directory_path
        )
        event_source = event_sources.EventSource(
            file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY,
            path_spec=path_spec,
        )
        event_source_heap.PushEventSource(event_source)

        for filename in ("filter_1.txt", "filter2.txt", "filter_3.txt"):
            test_file_path = self._GetTestFilePath(["testdir", filename])
            path_spec = path_spec_factory.Factory.NewPathSpec(
                dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
            )
            event_source = event_sources.EventSource(
                file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_FILE,
                path_spec=path_spec,
            )
            event_source_heap.PushEventSource(event_source)

        return event_source_heap

    def testCreateTask(self):
        """Tests the _CreateTask function."""
        # pylint: disable=protected-access
        test_directory_path = self._GetTestFilePath(["testdir"])
        self._SkipIfPathNotExists(test_directory_path)

        session = sessions.Session()
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        test_engine = extraction_engine.ExtractionMultiProcessEngine(
            number_of_worker_processes=1
        )

        # A directory event source is not combined with other event sources.
        event_source_heap = self._CreateEventSourceHeap()
        event_source = event_source_heap.PopEventSource()
        task = test_engine._CreateTask(
            storage_writer,
            session.identifier,
            event_source,
            event_source_heap=event_source_heap,
        )
        self.assertIsNotNone(task)
        self.assertEqual(task.GetPathSpecs(), [event_source.path_spec])
        self.assertEqual(len(event_source_heap), 3)

        # Regular file event sources are combined into a single task.
        event_source = event_source_heap.PopEventSource()
        task = test_engine._CreateTask(
            storage_writer,
            session.identifier,
            event_source,
            event_source_heap=event_source_heap,
        )
        self.assertIsNotNone(task)
        self.assertEqual(task.path_spec, event_source.path_spec)
        self.assertEqual(len(task.path_specs), 3)
        self.assertEqual(len(event_source_heap), 0)

        # Without an event source heap a task contains a single event source.
        event_source_heap = self._CreateEventSourceHeap()
        event_source_heap.PopEventSource()
        event_source = event_source_heap.PopEventSource()
        task = test_engine._CreateTask(storage_writer, session.identifier, event_source)
        self.assertIsNotNone(task)
        self.assertIsNone(task.path_specs)
        self.assertEqual(len(event_source_heap), 2)

        # The number of path specifications per task is limited.
        test_engine = TestExtractionMultiProcessEngineWithPathSpecsLimit(
            number_of_worker_processes=1
        )

        event_source_heap = self._CreateEventSourceHeap()
        event_source_heap.PopEventSource()
        event_source = event_source_heap.PopEventSource()
        task = test_engine._CreateTask(
            storage_writer,
            session.identifier,
            event_source,
            event_source_heap=event_source_heap,
        )
        self.assertIsNotNone(task)
        self.assertEqual(len(task.path_specs), 2)
        self.assertEqual(len(event_source_heap), 1)

        # The size of the data of the regular files per task is limited.
        test_engine = TestExtractionMultiProcessEngineWithDataSizeLimit(
            number_of_worker_processes=1
        )

        event_source_heap = self._CreateEventSourceHeap()
        event_source_heap.PopEventSource()
        event_source = event_source_heap.PopEventSource()
        task = test_engine._CreateTask(
            storage_writer,
            session.identifier,
            event_source,
            event_source_heap=event_source_heap,
        )
        self.assertIsNotNone(task)
        self.assertIsNone(task.path_specs)
        self.assertEqual(len(event_source_heap), 2)

        # Event sources are left in the heap for the other worker processes.
        test_engine = extraction_engine.ExtractionMultiProcessEngine(
            number_of_worker_processes=4
        )

        event_source_heap = self._CreateEventSourceHeap()
        event_source_heap.PopEventSource()
        event_source = event_source_heap.PopEventSource()
        task = test_engine._CreateTask(
            storage_writer,
            session.identifier,
            event_source,
            event_source_heap=event_source_heap,
        )
        self.assertIsNotNone(task)
        self.assertIsNone(task.path_specs)
        self.assertEqual(len(event_source_heap), 2)

        storage_writer.Close()

    def testInternalProcessEventSourcesWithFailedTask(self):
        """Tests the _ProcessEventSources function with a failed task."""
        # pylint: disable=protected-access

        test_engine = extraction_engine.ExtractionMultiProcessEngine()
        test_task_manager = test_engine._task_manager

        session = sessions.Session()

        processing_configuration = configurations.ProcessingConfiguration()
        processing_configuration.data_location = shared_test_lib.DATA_PATH
        processing_configuration.task_storage_format = definitions.STORAGE_FORMAT_SQLITE

        test_engine._processing_configuration = processing_configuration
        test_engine._task_storage_format = definitions.STORAGE_FORMAT_SQLITE

        completed_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location="/completed"
        )
        failed_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location="/failed"
        )

        with shared_test_lib.TempDirectory() as temp_directory:
            temp_file = os.path.join(temp_directory, "storage.plaso")
            test_engine._storage_file_path = temp_file
            test_engine._StartTaskStorage(definitions.STORAGE_FORMAT_SQLITE)

            # A task that a worker completed, stored as a worker would store it.
            completed_task = test_task_manager.CreateTask(
                session.identifier, storage_format=definitions.STORAGE_FORMAT_SQLITE
            )
            completed_task.path_spec = completed_path_spec
            test_task_manager.UpdateTaskAsProcessingByIdentifier(
                completed_task.identifier
            )

            task_storage_writer = (
                storage_factory.StorageFactory.CreateTaskStorageWriter(
                    definitions.STORAGE_FORMAT_SQLITE
                )
            )
            task_storage_writer.Open(
                path=test_engine._GetProcessedStorageFilePath(completed_task),
                session_identifier=session.identifier,
                task_identifier=completed_task.identifier,
            )
            try:
                task_storage_writer.AddAttributeContainer(completed_task)
                warning = warnings.ExtractionWarning(
                    message="Completed task warning", path_spec=completed_path_spec
                )
                task_storage_writer.AddAttributeContainer(warning)
            finally:
                task_storage_writer.Close()

            # A task that never completes, since the worker processing it, and the
            # workers processing its retries, stop reporting.
            failed_task = test_task_manager.CreateTask(
                session.identifier, storage_format=definitions.STORAGE_FORMAT_SQLITE
            )
            failed_task.path_spec = failed_path_spec
            test_task_manager.UpdateTaskAsProcessingByIdentifier(failed_task.identifier)
            failed_task.last_processing_time -= (
                2
                * test_task_manager._TASK_INACTIVE_TIME
                * definitions.MICROSECONDS_PER_SECOND
            )
            self.assertTrue(test_task_manager.HasPendingTasks())

            number_of_retries = 0
            retry_task = test_task_manager.CreateRetryTask()
            while retry_task and number_of_retries < 100:
                number_of_retries += 1
                test_task_manager._AbandonQueuedTasks()
                retry_task = test_task_manager.CreateRetryTask()

            self.assertEqual(
                number_of_retries, test_task_manager._MAXIMUM_NUMBER_OF_RETRIES
            )

            storage_writer = sqlite_writer.SQLiteStorageWriter()
            storage_writer.Open(path=temp_file)

            try:
                test_engine._ProcessEventSources(storage_writer, session.identifier)

                extraction_warnings = list(
                    storage_writer.GetAttributeContainers("extraction_warning")
                )
            finally:
                storage_writer.Close()

            processed_task_storage_files = os.listdir(
                test_engine._processed_task_storage_path
            )
            merge_task_storage_files = os.listdir(test_engine._merge_task_storage_path)
            test_engine._StopTaskStorage(
                definitions.STORAGE_FORMAT_SQLITE, session.identifier, abort=True
            )

        self.assertEqual(test_engine._status, definitions.STATUS_INDICATOR_IDLE)
        self.assertFalse(test_task_manager.HasPendingTasks())

        tasks_status = test_task_manager.GetStatusInformation()
        self.assertEqual(tasks_status.number_of_abandoned_tasks, 4)
        self.assertEqual(tasks_status.number_of_queued_tasks, 0)
        self.assertEqual(tasks_status.number_of_tasks_pending_merge, 0)
        self.assertEqual(tasks_status.number_of_tasks_processing, 0)

        # The task storage of the completed task was merged and removed.
        self.assertEqual(processed_task_storage_files, [])
        self.assertEqual(merge_task_storage_files, [])

        # The failed task is reported once, after the completed task was merged.
        warnings_per_message = {
            warning.message: warning.path_spec for warning in extraction_warnings
        }
        self.assertEqual(len(extraction_warnings), 2)
        self.assertEqual(
            warnings_per_message,
            {
                "Completed task warning": completed_path_spec,
                "Worker failed to process path specification": failed_path_spec,
            },
        )
        self.assertEqual(
            test_engine._processing_status.error_path_specs, [failed_path_spec]
        )

    def testInternalUpdateProcessingStatus(self):
        """Tests the _UpdateProcessingStatus function."""
        # pylint: disable=protected-access

        # The worker timeout is specified in minutes.
        test_engine = extraction_engine.ExtractionMultiProcessEngine(worker_timeout=5.0)

        process = multiprocessing.Process(name="Worker_00")
        test_engine._processes_per_pid[1] = process
        test_engine._process_information_per_pid[1] = None

        process_status = {
            "last_activity_timestamp": time.time() - 60.0,
            "processing_status": definitions.STATUS_INDICATOR_RUNNING,
        }
        test_engine._UpdateProcessingStatus(1, process_status, 0)

        worker_status = test_engine._processing_status.workers_status[0]
        self.assertEqual(worker_status.status, definitions.STATUS_INDICATOR_RUNNING)

        process_status = {
            "last_activity_timestamp": time.time() - 600.0,
            "processing_status": definitions.STATUS_INDICATOR_RUNNING,
        }
        test_engine._UpdateProcessingStatus(1, process_status, 0)

        worker_status = test_engine._processing_status.workers_status[0]
        self.assertEqual(
            worker_status.status, definitions.STATUS_INDICATOR_NOT_RESPONDING
        )

    def testProcessSource(self):
        """Tests the PreprocessSource and ProcessSource functions."""
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        source_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_EXT, location="/", parent=os_path_spec
        )
        self._ProcessSource(source_path_spec)

    def testProcessSourceWithTsk(self):
        """Tests the PreprocessSource and ProcessSource functions."""
        # Testing with TSK helps catch potential issues with TSKTime.
        test_file_path = self._GetTestFilePath(["ímynd.dd"])
        self._SkipIfPathNotExists(test_file_path)

        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path
        )
        source_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK, location="/", parent=os_path_spec
        )
        self._ProcessSource(source_path_spec)


if __name__ == "__main__":
    unittest.main()
