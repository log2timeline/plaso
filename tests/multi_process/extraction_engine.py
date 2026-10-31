#!/usr/bin/env python3
"""Tests the multi-process processing engine."""

import collections
import multiprocessing
import os
import time
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import sessions
from plaso.containers import warnings
from plaso.lib import definitions
from plaso.engine import configurations
from plaso.multi_process import extraction_engine
from plaso.storage import factory as storage_factory
from plaso.storage.sqlite import writer as sqlite_writer

from tests import test_lib as shared_test_lib


class TestFailingMergeExtractionMultiProcessEngine(
    extraction_engine.ExtractionMultiProcessEngine
):
    """Extraction multi-process engine of which every merge check fails."""

    # Number of merge checks after which the task scheduler loop is aborted,
    # so that the test fails instead of hangs when the loop does not stop.
    _MAXIMUM_NUMBER_OF_MERGE_CHECKS = 1000

    def __init__(self, fail_extraction_warning=False):
        """Initializes a test extraction multi-process engine.

        Args:
          fail_extraction_warning (Optional[bool]): True if producing an
              extraction warning should fail as well.
        """
        super().__init__()
        self._fail_extraction_warning = fail_extraction_warning
        self.number_of_merge_checks = 0

    def _MergeTaskStorage(self, storage_writer, session_identifier):
        """Merges a task storage with the session storage.

        Args:
          storage_writer (StorageWriter): storage writer for a session storage.
          session_identifier (str): the identifier of the session.

        Raises:
          RuntimeError: always.
        """
        self.number_of_merge_checks += 1
        if self.number_of_merge_checks >= self._MAXIMUM_NUMBER_OF_MERGE_CHECKS:
            self._abort = True

        raise RuntimeError("Unable to check task storage to merge.")

    def _ProduceExtractionWarning(self, storage_writer, message, path_spec):
        """Produces an extraction warning.

        Args:
          storage_writer (StorageWriter): storage writer for a session storage.
          message (str): message of the warning.
          path_spec (dfvfs.PathSpec): path specification.

        Raises:
          RuntimeError: if producing an extraction warning should fail.
        """
        if self._fail_extraction_warning:
            raise RuntimeError("Unable to produce extraction warning.")

        # The task scheduler loop can pass "N/A" instead of a path specification,
        # which cannot be stored.
        if path_spec == "N/A":
            path_spec = None

        super()._ProduceExtractionWarning(storage_writer, message, path_spec)


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

    def _ProcessEventSourcesWithRepeatingError(self, test_engine):
        """Processes event sources with an error that repeats on every iteration.

        Args:
          test_engine (TestFailingMergeExtractionMultiProcessEngine): test
              extraction multi-process engine.

        Returns:
          int: number of extraction warnings.
        """
        # pylint: disable=protected-access
        session = sessions.Session()

        test_engine._processing_configuration = configurations.ProcessingConfiguration()
        test_engine._task_storage_format = definitions.STORAGE_FORMAT_SQLITE

        with shared_test_lib.TempDirectory() as temp_directory:
            test_engine._storage_file_path = os.path.join(
                temp_directory, "storage.plaso"
            )
            test_engine._StartTaskStorage(definitions.STORAGE_FORMAT_SQLITE)

            storage_writer = sqlite_writer.SQLiteStorageWriter()
            storage_writer.Open(path=test_engine._storage_file_path)

            try:
                test_engine._ProcessEventSources(storage_writer, session.identifier)

                number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
                    "extraction_warning"
                )

            finally:
                storage_writer.Close()

            test_engine._StopTaskStorage(
                definitions.STORAGE_FORMAT_SQLITE, session.identifier, abort=True
            )

        return number_of_warnings

    def testInternalProcessEventSourcesWithRepeatingError(self):
        """Tests the _ProcessEventSources function with a repeating error."""
        # pylint: disable=protected-access
        test_engine = TestFailingMergeExtractionMultiProcessEngine()

        number_of_warnings = self._ProcessEventSourcesWithRepeatingError(test_engine)

        maximum_number_of_errors = test_engine._MAXIMUM_NUMBER_OF_CONSECUTIVE_ERRORS
        self.assertEqual(test_engine.number_of_merge_checks, maximum_number_of_errors)
        self.assertEqual(number_of_warnings, maximum_number_of_errors)
        self.assertTrue(test_engine._abort)
        self.assertTrue(test_engine._processing_status.aborted)

    def testInternalProcessEventSourcesWithRepeatingWarningError(self):
        """Tests the _ProcessEventSources function with a failing warning."""
        # pylint: disable=protected-access
        test_engine = TestFailingMergeExtractionMultiProcessEngine(
            fail_extraction_warning=True
        )

        number_of_warnings = self._ProcessEventSourcesWithRepeatingError(test_engine)

        maximum_number_of_errors = test_engine._MAXIMUM_NUMBER_OF_CONSECUTIVE_ERRORS
        self.assertEqual(test_engine.number_of_merge_checks, maximum_number_of_errors)
        self.assertEqual(number_of_warnings, 0)
        self.assertTrue(test_engine._abort)
        self.assertTrue(test_engine._processing_status.aborted)

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
