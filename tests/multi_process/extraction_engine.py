#!/usr/bin/env python3
"""Tests the multi-process processing engine."""

import collections
import multiprocessing
import os
import time
import unittest

from acstore.containers import interface as containers_interface
from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import artifacts
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import sessions
from plaso.containers import warnings
from plaso.lib import definitions
from plaso.engine import configurations
from plaso.multi_process import extraction_engine
from plaso.multi_process import merge_helpers
from plaso.multi_process import zeromq_queue
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


class EventSourceHeapTest(shared_test_lib.BaseTestCase):
    """Tests for the event source heap."""

    # pylint: disable=protected-access

    def testPeekEventSource(self):
        """Tests the PeekEventSource function."""
        event_source_heap = extraction_engine._EventSourceHeap()

        self.assertEqual(len(event_source_heap), 0)
        self.assertIsNone(event_source_heap.PeekEventSource())

        event_source = event_sources.EventSource()
        event_source_heap.PushEventSource(event_source)

        self.assertEqual(len(event_source_heap), 1)
        self.assertEqual(event_source_heap.PeekEventSource(), event_source)
        self.assertEqual(len(event_source_heap), 1)


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

    def testInternalFillEventSourceHeap(self):
        """Tests the _FillEventSourceHeap function."""
        # pylint: disable=protected-access
        test_engine = extraction_engine.ExtractionMultiProcessEngine()

        event_source_heap = extraction_engine._EventSourceHeap()

        with shared_test_lib.TempDirectory() as temp_directory:
            temp_file = os.path.join(temp_directory, "storage.plaso")
            storage_writer = sqlite_writer.SQLiteStorageWriter()
            storage_writer.Open(path=temp_file)

            try:
                result = test_engine._FillEventSourceHeap(
                    storage_writer, event_source_heap, start_with_first=True
                )
                self.assertFalse(result)

                event_source = event_sources.EventSource()
                storage_writer.AddAttributeContainer(event_source)

                result = test_engine._FillEventSourceHeap(
                    storage_writer, event_source_heap, start_with_first=True
                )
                self.assertTrue(result)

                result = test_engine._FillEventSourceHeap(
                    storage_writer, event_source_heap
                )
                self.assertFalse(result)

            finally:
                storage_writer.Close()

        self.assertIsNotNone(event_source_heap.PopEventSource())
        self.assertIsNone(event_source_heap.PopEventSource())

    def testInternalGetIdleSleepTime(self):
        """Tests the _GetIdleSleepTime function."""
        # pylint: disable=protected-access
        test_engine = extraction_engine.ExtractionMultiProcessEngine()

        minimum_sleep_time = test_engine._IDLE_SLEEP_MINIMUM_SECONDS
        maximum_sleep_time = test_engine._IDLE_SLEEP_MAXIMUM_SECONDS

        idle_sleep_time = test_engine._GetIdleSleepTime(0.0)
        self.assertEqual(idle_sleep_time, minimum_sleep_time)

        idle_sleep_time = test_engine._GetIdleSleepTime(idle_sleep_time)
        self.assertEqual(idle_sleep_time, minimum_sleep_time * 2.0)

        for _ in range(100):
            idle_sleep_time = test_engine._GetIdleSleepTime(idle_sleep_time)
            self.assertLessEqual(idle_sleep_time, maximum_sleep_time)

        self.assertEqual(idle_sleep_time, maximum_sleep_time)

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

    def testInternalCreateTask(self):
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
        self.assertEqual(task.path_specs, [event_source.path_spec])
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
        self.assertEqual(task.path_specs[0], event_source.path_spec)
        self.assertEqual(len(task.path_specs), 3)
        self.assertEqual(len(event_source_heap), 0)

        # Without an event source heap a task contains a single event source.
        event_source_heap = self._CreateEventSourceHeap()
        event_source_heap.PopEventSource()
        event_source = event_source_heap.PopEventSource()
        task = test_engine._CreateTask(storage_writer, session.identifier, event_source)
        self.assertIsNotNone(task)
        self.assertEqual(task.path_specs, [event_source.path_spec])
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
        self.assertEqual(task.path_specs, [event_source.path_spec])
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
        self.assertEqual(task.path_specs, [event_source.path_spec])
        self.assertEqual(len(event_source_heap), 2)

        # No task is created for an event source that is excluded from extraction.
        test_engine._excluded_file_system_find_specs = [
            file_system_searcher.FindSpec(
                case_sensitive=False,
                location=event_source.path_spec.location,
                location_separator=os.path.sep,
            )
        ]

        task = test_engine._CreateTask(storage_writer, session.identifier, event_source)
        self.assertIsNone(task)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # No task is created for an event source that cannot be opened.
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS,
            location=os.path.join(test_directory_path, "bogus.txt"),
        )
        event_source = event_sources.EventSource(
            file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_FILE,
            path_spec=path_spec,
        )

        task = test_engine._CreateTask(storage_writer, session.identifier, event_source)
        self.assertIsNone(task)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 1)

        # An event source that cannot be opened is not added to a task.
        test_engine = extraction_engine.ExtractionMultiProcessEngine(
            number_of_worker_processes=1
        )

        bogus_event_source = event_source

        event_source_heap = self._CreateEventSourceHeap()
        event_source_heap.PopEventSource()
        event_source = event_source_heap.PopEventSource()

        event_source_heap = extraction_engine._EventSourceHeap()
        event_source_heap.PushEventSource(bogus_event_source)

        task = test_engine._CreateTask(
            storage_writer,
            session.identifier,
            event_source,
            event_source_heap=event_source_heap,
        )
        self.assertIsNotNone(task)
        self.assertEqual(task.path_specs, [event_source.path_spec])
        self.assertEqual(len(event_source_heap), 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 2)

        storage_writer.Close()

    def testInternalCheckStatusWorkerProcessWithKilledWorker(self):
        """Tests the _CheckStatusWorkerProcess function with a killed worker."""
        # pylint: disable=protected-access

        test_engine = extraction_engine.ExtractionMultiProcessEngine(
            number_of_worker_processes=1
        )

        with shared_test_lib.TempDirectory() as temp_directory:
            processing_configuration = configurations.ProcessingConfiguration()
            processing_configuration.data_location = shared_test_lib.DATA_PATH
            processing_configuration.task_storage_format = (
                definitions.STORAGE_FORMAT_SQLITE
            )
            processing_configuration.task_storage_path = temp_directory

            test_engine._processing_configuration = processing_configuration
            test_engine._system_configurations = []
            test_engine._windows_event_log_providers = []

            test_engine._task_queue = zeromq_queue.ZeroMQBufferedReplyBindQueue(
                delay_open=True,
                linger_seconds=0,
                maximum_items=1,
                name="main_task_queue",
                timeout_seconds=test_engine._ZEROMQ_NO_WORKER_REQUEST_TIME_SECONDS,
            )
            test_engine._task_queue.Open()
            test_engine._task_queue_port = test_engine._task_queue.port

            try:
                process = test_engine._StartWorkerProcess("Worker_00")
                self.assertIsNotNone(process)

                pid = process.pid
                self.assertIn(pid, test_engine._process_information_per_pid)

                test_engine._KillProcess(pid)
                # A SIGKILL cannot be handled, hence join returns once the worker
                # process has been terminated.
                process.join()
                self.assertFalse(process.is_alive())

                test_engine._CheckStatusWorkerProcess(pid)

                # The killed worker process is no longer monitored and exactly one
                # replacement worker process was started.
                self.assertNotIn(pid, test_engine._process_information_per_pid)
                self.assertNotIn(pid, test_engine._rpc_clients_per_pid)
                self.assertEqual(len(test_engine._processes_per_pid), 2)
                self.assertEqual(len(test_engine._process_information_per_pid), 1)
                self.assertEqual(test_engine._last_worker_number, 2)

                replacement_pid = next(iter(test_engine._process_information_per_pid))
                replacement_process = test_engine._processes_per_pid[replacement_pid]
                self.assertEqual(replacement_process.name, "Worker_01")

                workers_status_per_pid = {
                    worker_status.pid: worker_status
                    for worker_status in test_engine._processing_status.workers_status
                }
                self.assertEqual(
                    workers_status_per_pid[pid].status,
                    definitions.STATUS_INDICATOR_KILLED,
                )

                # A next status update does not start another replacement worker
                # process for the killed worker process.
                test_engine._UpdateStatus()

                self.assertEqual(len(test_engine._processes_per_pid), 2)
                self.assertEqual(len(test_engine._process_information_per_pid), 1)
                self.assertEqual(test_engine._last_worker_number, 2)

                workers_status_per_pid = {
                    worker_status.pid: worker_status
                    for worker_status in test_engine._processing_status.workers_status
                }
                self.assertNotIn(
                    workers_status_per_pid[replacement_pid].status,
                    definitions.ERROR_STATUS_INDICATORS,
                )

            finally:
                test_engine._StopMonitoringProcesses()
                test_engine._AbortKill()
                for process in test_engine._processes_per_pid.values():
                    process.join()

                test_engine._task_queue.Close(abort=True)

    def testInternalMergeAttributeContainerWithMissingReference(self):
        """Tests the _MergeAttributeContainer function with a missing reference."""
        # pylint: disable=protected-access

        test_engine = extraction_engine.ExtractionMultiProcessEngine()

        task_storage_writer = fake_writer.FakeStorageWriter()
        task_storage_writer.Open()

        merge_helper = merge_helpers.ExtractionTaskMergeHelper(
            task_storage_writer, "task"
        )

        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            event_data = events.EventData()
            event_data.SetIdentifier(
                containers_interface.AttributeContainerIdentifier(
                    name="event_data", sequence_number=1
                )
            )
            event_data.SetEventDataStreamIdentifier(
                containers_interface.AttributeContainerIdentifier(
                    name="event_data_stream", sequence_number=1
                )
            )
            test_engine._MergeAttributeContainer(
                storage_writer, merge_helper, event_data
            )

            event_definition = artifacts.WindowsWevtTemplateEvent()
            event_definition.SetIdentifier(
                containers_interface.AttributeContainerIdentifier(
                    name="windows_wevt_template_event", sequence_number=1
                )
            )
            event_definition.SetMessageFileIdentifier(
                containers_interface.AttributeContainerIdentifier(
                    name="windows_eventlog_message_file", sequence_number=1
                )
            )
            test_engine._MergeAttributeContainer(
                storage_writer, merge_helper, event_definition
            )

            number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
                "event_data"
            )
            number_of_event_definitions = storage_writer.GetNumberOfAttributeContainers(
                "windows_wevt_template_event"
            )
            extraction_warnings = list(
                storage_writer.GetAttributeContainers("extraction_warning")
            )

        finally:
            storage_writer.Close()
            task_storage_writer.Close()

        self.assertEqual(number_of_event_data, 0)
        self.assertEqual(number_of_event_definitions, 0)
        self.assertEqual(len(extraction_warnings), 2)

        expected_message = (
            "Unable to merge event_data attribute container: event_data.1 since "
            "corresponding event data stream: event_data_stream.1 could not be found."
        )
        self.assertEqual(extraction_warnings[0].message, expected_message)

        expected_message = (
            "Unable to merge WEVT_TEMPLATE event definition attribute container: "
            "windows_wevt_template_event.1 since corresponding Windows EventLog "
            "message file: windows_eventlog_message_file.1 could not be found."
        )
        self.assertEqual(extraction_warnings[1].message, expected_message)

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
            completed_task.path_specs = [completed_path_spec]
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
            failed_task.path_specs = [failed_path_spec]
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
