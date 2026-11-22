#!/usr/bin/env python3
"""Tests for the task-based multi-process processing analysis engine."""

import gzip
import logging
import multiprocessing
import os
import shutil
import time
import unittest

from plaso.analysis import tagging
from plaso.containers import sessions
from plaso.engine import configurations
from plaso.engine import process_info
from plaso.lib import definitions
from plaso.lib import loggers
from plaso.multi_process import analysis_engine
from plaso.multi_process import plaso_xmlrpc
from plaso.storage import factory as storage_factory

from tests import test_lib as shared_test_lib
from tests.filters import test_lib as filters_test_lib
from tests.multi_process import test_lib


class AnalysisEngineMultiProcessEngineTest(test_lib.MultiProcessingTestCase):
    """Tests for the task-based multi-process processing analysis engine."""

    # pylint: disable=protected-access

    def _CreateTestEngine(self):
        """Creates an engine with a registered and monitored analysis process.

        The RPC client of the analysis process connects to a port without a RPC
        server, therefore querying the process status via RPC fails.

        Returns:
          tuple[AnalysisMultiProcessEngine, TestProcess]: engine and analysis
              process.
        """
        pid = os.getpid()
        process = test_lib.TestProcess("tagging", pid)

        rpc_client = plaso_xmlrpc.XMLProcessStatusRPCClient()
        rpc_client.Open("localhost", process.rpc_port.value)

        test_engine = analysis_engine.AnalysisMultiProcessEngine(worker_memory_limit=0)
        test_engine._processes_per_pid[pid] = process
        test_engine._process_information_per_pid[pid] = process_info.ProcessInfo(pid)
        test_engine._rpc_clients_per_pid[pid] = rpc_client

        return test_engine, process

    def testInternalAnalyzeEvents(self):
        """Tests the _AnalyzeEvents function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        test_tagging_file_path = self._GetTestFilePath(["tagging_file", "valid.txt"])
        self._SkipIfPathNotExists(test_tagging_file_path)

        session = sessions.Session()

        analysis_plugin = tagging.TaggingAnalysisPlugin()
        analysis_plugin.SetAndLoadTagFile(test_tagging_file_path)

        analysis_plugins = {"tagging": analysis_plugin}

        configuration = configurations.ProcessingConfiguration()
        test_engine = analysis_engine.AnalysisMultiProcessEngine()

        with shared_test_lib.TempDirectory() as temp_directory:
            temp_file = os.path.join(temp_directory, "storage.plaso")
            shutil.copyfile(test_file_path, temp_file)

            storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
                definitions.DEFAULT_STORAGE_FORMAT
            )
            test_engine._processing_configuration = configuration
            test_engine._session = session

            test_engine._storage_file_path = temp_directory
            test_engine._StartTaskStorage(definitions.STORAGE_FORMAT_SQLITE)

            test_engine._StartAnalysisProcesses(analysis_plugins)

            storage_writer.Open(path=temp_file)

            try:
                events_counter = test_engine._AnalyzeEvents(
                    storage_writer, analysis_plugins
                )
            finally:
                storage_writer.Close()

            test_engine._StopAnalysisProcesses()

        self.assertIsNotNone(events_counter)
        self.assertEqual(events_counter["Events filtered"], 0)
        self.assertEqual(events_counter["Events processed"], 38)

    def testInternalCheckStatusAnalysisProcessWithRPCError(self):
        """Tests the _CheckStatusAnalysisProcess function with a RPC error."""
        test_engine, process = self._CreateTestEngine()

        test_engine._CheckStatusAnalysisProcess(process.pid)

        worker_status = test_engine._processing_status.workers_status[0]
        self.assertEqual(worker_status.status, "RPC error")
        self.assertEqual(test_engine._rpc_errors_per_pid[process.pid], 1)
        self.assertFalse(process.terminated)

    def testInternalCheckStatusAnalysisProcessWithMaximumRPCErrors(self):
        """Tests the _CheckStatusAnalysisProcess function with too many RPC errors."""
        test_engine, process = self._CreateTestEngine()
        test_engine._rpc_errors_per_pid[process.pid] = test_engine._MAXIMUM_RPC_ERRORS

        test_engine._CheckStatusAnalysisProcess(process.pid)

        worker_status = test_engine._processing_status.workers_status[0]
        self.assertEqual(worker_status.status, definitions.STATUS_INDICATOR_KILLED)
        self.assertTrue(process.terminated)

    def testInternalCheckStatusAnalysisProcessCompleted(self):
        """Tests the _CheckStatusAnalysisProcess function on a completed process."""
        test_engine = analysis_engine.AnalysisMultiProcessEngine()

        with self.assertRaises(KeyError):
            test_engine._CheckStatusAnalysisProcess(1)

        process = multiprocessing.Process(name="Worker_00")
        test_engine._processes_per_pid[1] = process
        test_engine._process_information_per_pid[1] = None
        test_engine._completed_analysis_processes.add(1)

        test_engine._CheckStatusAnalysisProcess(1)

        worker_status = test_engine._processing_status.workers_status[0]
        self.assertEqual(worker_status.identifier, "Worker_00")
        self.assertEqual(worker_status.pid, 1)
        self.assertEqual(worker_status.status, definitions.STATUS_INDICATOR_COMPLETED)
        self.assertEqual(worker_status.used_memory, 0)

        self.assertIn(1, test_engine._process_information_per_pid)

    # TODO: add test for _StartAnalysisProcesses.

    def testInternalStatusUpdateThreadMain(self):
        """Tests the _StatusUpdateThreadMain function."""
        processing_status_updates = []

        def _StatusUpdateCallback(processing_status):
            """Records the processing status and stops the status updates.

            Args:
              processing_status (ProcessingStatus): processing status.
            """
            processing_status_updates.append(processing_status)
            test_engine._status_update_active = False

        test_engine = analysis_engine.AnalysisMultiProcessEngine()
        test_engine._status_update_active = True
        test_engine._status_update_callback = _StatusUpdateCallback
        test_engine._status_update_interval = 0.01

        test_engine._StatusUpdateThreadMain()

        self.assertEqual(len(processing_status_updates), 1)

        foreman_status = processing_status_updates[0].foreman_status
        self.assertIsNotNone(foreman_status)
        self.assertEqual(foreman_status.identifier, "Main")
        self.assertEqual(foreman_status.status, definitions.STATUS_INDICATOR_IDLE)

    # TODO: add test for _StopAnalysisProcesses.

    def testAnalyzeEvents(self):
        """Tests the AnalyzeEvents function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        test_tagging_file_path = self._GetTestFilePath(["tagging_file", "valid.txt"])
        self._SkipIfPathNotExists(test_tagging_file_path)

        session = sessions.Session()

        data_location = ""

        analysis_plugin = tagging.TaggingAnalysisPlugin()
        analysis_plugin.SetAndLoadTagFile(test_tagging_file_path)

        analysis_plugins = {"tagging": analysis_plugin}

        configuration = configurations.ProcessingConfiguration()
        test_engine = analysis_engine.AnalysisMultiProcessEngine()

        with shared_test_lib.TempDirectory() as temp_directory:
            temp_file = os.path.join(temp_directory, "storage.plaso")
            shutil.copyfile(test_file_path, temp_file)

            storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
                definitions.DEFAULT_STORAGE_FORMAT
            )
            storage_writer.Open(path=temp_file)

            try:
                number_of_reports = storage_writer.GetNumberOfAttributeContainers(
                    "analysis_report"
                )
                self.assertEqual(number_of_reports, 2)

                test_engine.AnalyzeEvents(
                    session,
                    storage_writer,
                    data_location,
                    analysis_plugins,
                    configuration,
                    storage_file_path=temp_directory,
                )
                number_of_reports = storage_writer.GetNumberOfAttributeContainers(
                    "analysis_report"
                )
                self.assertEqual(number_of_reports, 3)

            finally:
                storage_writer.Close()

    def testAnalyzeEventsWithCompressedLog(self):
        """Tests that analysis processes do not corrupt a compressed log file."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        test_tagging_file_path = self._GetTestFilePath(["tagging_file", "valid.txt"])
        self._SkipIfPathNotExists(test_tagging_file_path)

        session = sessions.Session()

        data_location = ""

        analysis_plugin = tagging.TaggingAnalysisPlugin()
        analysis_plugin.SetAndLoadTagFile(test_tagging_file_path)

        analysis_plugins = {"tagging": analysis_plugin}

        test_engine = analysis_engine.AnalysisMultiProcessEngine()

        original_handlers = list(logging.root.handlers)
        for handler in original_handlers:
            logging.root.removeHandler(handler)

        with shared_test_lib.TempDirectory() as temp_directory:
            try:
                temp_file = os.path.join(temp_directory, "storage.plaso")
                shutil.copyfile(test_file_path, temp_file)

                log_file = os.path.join(temp_directory, "test.log.gz")
                loggers.ConfigureLogging(filename=log_file)

                configuration = configurations.ProcessingConfiguration()
                configuration.log_filename = log_file

                storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
                    definitions.DEFAULT_STORAGE_FORMAT
                )
                storage_writer.Open(path=temp_file)

                logging.warning("before analysis")

                try:
                    test_engine.AnalyzeEvents(
                        session,
                        storage_writer,
                        data_location,
                        analysis_plugins,
                        configuration,
                        storage_file_path=temp_directory,
                    )
                finally:
                    storage_writer.Close()

                logging.warning("after analysis")

                for handler in list(logging.root.handlers):
                    logging.root.removeHandler(handler)
                    handler.close()

                with gzip.open(log_file, "rt", encoding="utf-8") as file_object:
                    log_text = file_object.read()

            finally:
                for handler in list(logging.root.handlers):
                    logging.root.removeHandler(handler)
                    handler.close()
                for handler in original_handlers:
                    logging.root.addHandler(handler)

        self.assertIn("before analysis", log_text)
        self.assertIn("after analysis", log_text)

    def testAnalyzeEventsWithoutParserCount(self):
        """Tests the AnalyzeEvents function on a storage file without counts."""
        test_tagging_file_path = self._GetTestFilePath(["tagging_file", "valid.txt"])
        self._SkipIfPathNotExists(test_tagging_file_path)

        session = sessions.Session()

        data_location = ""

        analysis_plugin = tagging.TaggingAnalysisPlugin()
        analysis_plugin.SetAndLoadTagFile(test_tagging_file_path)

        analysis_plugins = {"tagging": analysis_plugin}

        configuration = configurations.ProcessingConfiguration()
        test_engine = analysis_engine.AnalysisMultiProcessEngine()

        with shared_test_lib.TempDirectory() as temp_directory:
            temp_file = os.path.join(temp_directory, "storage.plaso")

            storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
                definitions.DEFAULT_STORAGE_FORMAT
            )
            storage_writer.Open(path=temp_file)

            try:
                # A storage file of an extraction that generated no events has no
                # parser count attribute containers.
                storage_writer.AddAttributeContainer(session)

                has_parser_count = storage_writer.HasAttributeContainers("parser_count")
                self.assertFalse(has_parser_count)

                test_engine.AnalyzeEvents(
                    session,
                    storage_writer,
                    data_location,
                    analysis_plugins,
                    configuration,
                    storage_file_path=temp_directory,
                )
                self.assertEqual(test_engine._events_status.total_number_of_events, 0)

            finally:
                storage_writer.Close()

    def testAnalyzeEventsWithEventFilter(self):
        """Tests the AnalyzeEvents function with an event filter."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        test_tagging_file_path = self._GetTestFilePath(["tagging_file", "valid.txt"])
        self._SkipIfPathNotExists(test_tagging_file_path)

        session = sessions.Session()

        data_location = ""

        analysis_plugin = tagging.TaggingAnalysisPlugin()
        analysis_plugin.SetAndLoadTagFile(test_tagging_file_path)

        analysis_plugins = {"tagging": analysis_plugin}

        configuration = configurations.ProcessingConfiguration()
        test_engine = analysis_engine.AnalysisMultiProcessEngine()
        test_filter = filters_test_lib.TestEventFilter()

        with shared_test_lib.TempDirectory() as temp_directory:
            temp_file = os.path.join(temp_directory, "storage.plaso")
            shutil.copyfile(test_file_path, temp_file)

            storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
                definitions.DEFAULT_STORAGE_FORMAT
            )
            storage_writer.Open(path=temp_file)

            try:
                number_of_reports = storage_writer.GetNumberOfAttributeContainers(
                    "analysis_report"
                )
                self.assertEqual(number_of_reports, 2)

                test_engine.AnalyzeEvents(
                    session,
                    storage_writer,
                    data_location,
                    analysis_plugins,
                    configuration,
                    event_filter=test_filter,
                    storage_file_path=temp_directory,
                )
                number_of_reports = storage_writer.GetNumberOfAttributeContainers(
                    "analysis_report"
                )
                self.assertEqual(number_of_reports, 3)

            finally:
                storage_writer.Close()

    def testInternalUpdateProcessingStatus(self):
        """Tests the _UpdateProcessingStatus function."""
        # The worker timeout is specified in minutes.
        test_engine = analysis_engine.AnalysisMultiProcessEngine(worker_timeout=5.0)

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

    # TODO: add bogus data location test.


if __name__ == "__main__":
    unittest.main()
