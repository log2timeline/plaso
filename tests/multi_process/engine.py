#!/usr/bin/env python3
"""Tests the multi-process processing engine."""

import multiprocessing
import os
import sys
import unittest

from plaso.engine import process_info
from plaso.lib import definitions
from plaso.multi_process import engine
from plaso.multi_process import plaso_xmlrpc

from tests import test_lib as shared_test_lib


class TestProcess:
    """Process for testing.

    Attributes:
      is_terminated (bool): True if terminate was called.
      join_timeouts (list[float]): timeouts of the calls to join.
      name (str): process name.
      pid (int): process identifier (PID).
      rpc_port (multiprocessing.Value): port number of the process status RPC
          server.
    """

    def __init__(self, pid, name, is_alive=True, stops_on_terminate=True):
        """Initializes a process for testing.

        Args:
          pid (int): process identifier (PID).
          name (str): process name.
          is_alive (Optional[bool]): True if the process is alive.
          stops_on_terminate (Optional[bool]): True if the process stops when
              terminate is called.
        """
        super().__init__()
        self._is_alive = is_alive
        self._stops_on_terminate = stops_on_terminate
        self.is_terminated = False
        self.join_timeouts = []
        self.name = name
        self.pid = pid
        self.rpc_port = multiprocessing.Value("I", 0)

    # The following methods are part of the multiprocessing.Process interface
    # hence their names do not follow the style guide.

    def is_alive(self):  # pylint: disable=invalid-name
        """Determines if the process is alive.

        Returns:
          bool: True if the process is alive.
        """
        return self._is_alive

    def join(self, timeout=None):  # pylint: disable=invalid-name
        """Joins the process.

        Args:
          timeout (Optional[float]): number of seconds to wait for the process
              to join, where None represents no timeout.
        """
        self.join_timeouts.append(timeout)

    def terminate(self):  # pylint: disable=invalid-name
        """Terminates the process."""
        self.is_terminated = True
        if self._stops_on_terminate:
            self._is_alive = False


class TestEngine(engine.MultiProcessEngine):
    """Multi-process engine for testing.

    Attributes:
      killed_pids (list[int]): process identifiers (PIDs) of the processes
          the engine attempted to kill.
      number_of_status_updates (int): number of times the status was updated.
      processing_status_updates (list[tuple[int, dict[str, object], int]]):
          arguments of the processing status updates.
      started_process_names (list[str]): names of the worker processes the engine
          attempted to start.
    """

    def __init__(self):
        """Initializes a multi-process engine for testing."""
        super().__init__()
        self.killed_pids = []
        self.number_of_status_updates = 0
        self.processing_status_updates = []
        self.started_process_names = []

    def _KillProcess(self, pid):
        """Records the process instead of issuing a SIGKILL or equivalent.

        Args:
          pid (int): process identifier (PID).
        """
        self.killed_pids.append(pid)

    def _StartWorkerProcess(self, process_name):
        """Records the worker process to start.

        Args:
          process_name (str): process name.

        Returns:
          TestProcess: worker process.
        """
        self.started_process_names.append(process_name)
        return TestProcess(2000, process_name)

    def _UpdateProcessingStatus(self, pid, process_status, used_memory):
        """Records the processing status update.

        Args:
          pid (int): process identifier (PID) of the worker process.
          process_status (dict[str, object]): status values received from
              the worker process.
          used_memory (int): size of used memory in bytes.
        """
        self.processing_status_updates.append((pid, process_status, used_memory))

    def _UpdateStatus(self):
        """Updates the status."""
        self.number_of_status_updates += 1


class MultiProcessEngineTest(shared_test_lib.BaseTestCase):
    """Tests for the multi-process engine."""

    # pylint: disable=protected-access

    # TODO: add test for _CheckStatusWorkerProcess

    # The process identifiers (PIDs) used in these tests are made up, therefore
    # the test engine records attempts to kill a process instead.

    def testAbortJoin(self):
        """Tests the _AbortJoin function."""
        test_engine = TestEngine()

        alive_process = TestProcess(1001, "Worker_00")
        stopped_process = TestProcess(1002, "Worker_01", is_alive=False)
        test_engine._RegisterProcess(alive_process)
        test_engine._RegisterProcess(stopped_process)

        test_engine._AbortJoin(timeout=2.0)

        self.assertEqual(alive_process.join_timeouts, [2.0])
        self.assertEqual(stopped_process.join_timeouts, [2.0])

        test_engine._AbortJoin()

        self.assertEqual(alive_process.join_timeouts, [2.0, None])

    def testAbortKill(self):
        """Tests the _AbortKill function."""
        test_engine = TestEngine()

        test_engine._RegisterProcess(TestProcess(1001, "Worker_00"))
        test_engine._RegisterProcess(TestProcess(1002, "Worker_01", is_alive=False))

        test_engine._AbortKill()

        self.assertEqual(test_engine.killed_pids, [1001])

    def testAbortTerminate(self):
        """Tests the _AbortTerminate function."""
        test_engine = TestEngine()

        alive_process = TestProcess(1001, "Worker_00")
        stopped_process = TestProcess(1002, "Worker_01", is_alive=False)
        test_engine._RegisterProcess(alive_process)
        test_engine._RegisterProcess(stopped_process)

        test_engine._AbortTerminate()

        self.assertTrue(alive_process.is_terminated)
        self.assertFalse(stopped_process.is_terminated)
        self.assertEqual(test_engine.killed_pids, [])

    def testCheckStatusWorkerProcess(self):
        """Tests the _CheckStatusWorkerProcess function."""
        test_engine = TestEngine()
        test_engine._worker_memory_limit = 0

        with self.assertRaises(KeyError):
            test_engine._CheckStatusWorkerProcess(1001)

        # Test with a process that has stopped.
        test_process = TestProcess(1001, "Worker_00", is_alive=False)
        test_engine._RegisterProcess(test_process)

        test_engine._process_information_per_pid[1001] = process_info.ProcessInfo(
            os.getpid()
        )
        test_engine._rpc_clients_per_pid[1001] = (
            plaso_xmlrpc.XMLProcessStatusRPCClient()
        )

        test_engine._CheckStatusWorkerProcess(1001)

        self.assertEqual(len(test_engine.processing_status_updates), 1)
        pid, process_status, _ = test_engine.processing_status_updates[0]
        self.assertEqual(pid, 1001)
        self.assertEqual(process_status, {"processing_status": "killed"})

        self.assertTrue(test_process.is_terminated)
        self.assertEqual(test_engine.killed_pids, [])
        self.assertNotIn(1001, test_engine._process_information_per_pid)
        self.assertNotIn(1001, test_engine._rpc_clients_per_pid)
        self.assertEqual(test_engine.started_process_names, ["Worker_00"])

    def testCheckStatusWorkerProcessWithStatus(self):
        """Tests the _CheckStatusWorkerProcess function with a process status."""
        expected_process_status = {
            "processing_status": definitions.STATUS_INDICATOR_RUNNING
        }

        rpc_server = plaso_xmlrpc.XMLProcessStatusRPCServer(
            lambda: expected_process_status
        )
        rpc_port = None
        for port in range(52000, 52100):
            if rpc_server.Start("localhost", port):
                rpc_port = port
                break

        self.assertIsNotNone(rpc_port)

        test_engine = TestEngine()
        test_engine._worker_memory_limit = 0

        test_process = TestProcess(1001, "Worker_00")
        test_engine._RegisterProcess(test_process)

        rpc_client = plaso_xmlrpc.XMLProcessStatusRPCClient()
        rpc_client.Open("localhost", rpc_port)

        test_engine._process_information_per_pid[1001] = process_info.ProcessInfo(
            os.getpid()
        )
        test_engine._rpc_clients_per_pid[1001] = rpc_client
        test_engine._rpc_errors_per_pid[1001] = 3

        try:
            test_engine._CheckStatusWorkerProcess(1001)
        finally:
            rpc_server.Stop()

        self.assertEqual(len(test_engine.processing_status_updates), 1)
        pid, process_status, _ = test_engine.processing_status_updates[0]
        self.assertEqual(pid, 1001)
        self.assertEqual(process_status, expected_process_status)

        self.assertEqual(test_engine._rpc_errors_per_pid[1001], 0)
        self.assertFalse(test_process.is_terminated)
        self.assertIn(1001, test_engine._process_information_per_pid)
        self.assertEqual(test_engine.started_process_names, [])

    @unittest.skipIf(sys.platform.startswith("win"), "not supported on Windows")
    def testKillProcess(self):
        """Tests the _KillProcess function."""
        test_engine = TestEngine()

        # A PID that exceeds the maximum PID supported by the operating system
        # cannot refer to an existing process.
        with self.assertLogs("multi_process", level="ERROR") as log_context:
            engine.MultiProcessEngine._KillProcess(test_engine, 0x7FFFFFFF)

        self.assertIn("Unable to kill process 2147483647", log_context.output[0])

    def testQueryProcessStatus(self):
        """Tests the _QueryProcessStatus function."""
        test_engine = TestEngine()

        test_process = TestProcess(1001, "Worker_00", is_alive=False)
        process_status = test_engine._QueryProcessStatus(test_process)
        self.assertIsNone(process_status)

        test_process = TestProcess(1002, "Worker_01")
        test_engine._rpc_clients_per_pid[1002] = (
            plaso_xmlrpc.XMLProcessStatusRPCClient()
        )

        # The RPC client was not opened, therefore no status is returned.
        process_status = test_engine._QueryProcessStatus(test_process)
        self.assertIsNone(process_status)

    def testRaiseIfNotMonitored(self):
        """Tests the _RaiseIfNotMonitored function."""
        test_engine = TestEngine()

        with self.assertRaisesRegex(KeyError, "1001"):
            test_engine._RaiseIfNotMonitored(1001)

        test_engine._process_information_per_pid[1001] = None
        test_engine._RaiseIfNotMonitored(1001)

    def testRaiseIfNotRegistered(self):
        """Tests the _RaiseIfNotRegistered function."""
        test_engine = TestEngine()

        with self.assertRaisesRegex(KeyError, "1001"):
            test_engine._RaiseIfNotRegistered(1001)

        test_engine._RegisterProcess(TestProcess(1001, "Worker_00"))
        test_engine._RaiseIfNotRegistered(1001)

    def testRegisterProcess(self):
        """Tests the _RegisterProcess function."""
        test_engine = TestEngine()

        test_process = TestProcess(1001, "Worker_00")
        test_engine._RegisterProcess(test_process)

        self.assertIs(test_engine._processes_per_pid[1001], test_process)

        with self.assertRaises(KeyError):
            test_engine._RegisterProcess(TestProcess(1001, "Worker_01"))

        self.assertIs(test_engine._processes_per_pid[1001], test_process)

        with self.assertRaises(ValueError):
            test_engine._RegisterProcess(None)

    def testStartMonitoringProcess(self):
        """Tests the _StartMonitoringProcess function."""
        test_engine = TestEngine()

        with self.assertRaises(ValueError):
            test_engine._StartMonitoringProcess(None)

        # The process information requires the PID of an existing process.
        test_process = TestProcess(os.getpid(), "Worker_00")
        test_process.rpc_port.value = 52000

        test_engine._StartMonitoringProcess(test_process)

        self.assertIn(test_process.pid, test_engine._process_information_per_pid)
        self.assertIn(test_process.pid, test_engine._rpc_clients_per_pid)

        with self.assertRaises(KeyError):
            test_engine._StartMonitoringProcess(test_process)

        # Test with a RPC client that already exists.
        del test_engine._process_information_per_pid[test_process.pid]

        with self.assertRaises(KeyError):
            test_engine._StartMonitoringProcess(test_process)

    def testStartMonitoringProcessWithoutRPCPort(self):
        """Tests the _StartMonitoringProcess function without a RPC port."""
        test_engine = TestEngine()
        setattr(test_engine, "_RPC_SERVER_TIMEOUT", 0.2)

        test_process = TestProcess(os.getpid(), "Worker_00")

        with self.assertRaises(OSError):
            test_engine._StartMonitoringProcess(test_process)

        self.assertNotIn(test_process.pid, test_engine._process_information_per_pid)
        self.assertNotIn(test_process.pid, test_engine._rpc_clients_per_pid)

    def testStartStatusUpdateThread(self):
        """Tests the _StartStatusUpdateThread function."""
        test_engine = TestEngine()
        test_engine._status_update_interval = 0.01

        test_engine._StartStatusUpdateThread()

        try:
            self.assertTrue(test_engine._status_update_active)
            self.assertIsNotNone(test_engine._status_update_thread)
            self.assertTrue(test_engine._status_update_thread.is_alive())

        finally:
            test_engine._StopStatusUpdateThread()

    def testStopMonitoringProcess(self):
        """Tests the _StopMonitoringProcess function."""
        test_engine = TestEngine()

        with self.assertRaises(ValueError):
            test_engine._StopMonitoringProcess(None)

        test_process = TestProcess(1001, "Worker_00")

        with self.assertRaises(KeyError):
            test_engine._StopMonitoringProcess(test_process)

        test_engine._process_information_per_pid[1001] = None
        test_engine._rpc_clients_per_pid[1001] = (
            plaso_xmlrpc.XMLProcessStatusRPCClient()
        )
        test_engine._rpc_errors_per_pid[1001] = 1

        test_engine._StopMonitoringProcess(test_process)

        self.assertNotIn(1001, test_engine._process_information_per_pid)
        self.assertNotIn(1001, test_engine._rpc_clients_per_pid)
        self.assertNotIn(1001, test_engine._rpc_errors_per_pid)

    def testStopMonitoringProcesses(self):
        """Tests the _StopMonitoringProcesses function."""
        test_engine = TestEngine()

        for pid, name in ((1001, "Worker_00"), (1002, "Worker_01")):
            test_engine._RegisterProcess(TestProcess(pid, name))
            test_engine._process_information_per_pid[pid] = None
            test_engine._rpc_clients_per_pid[pid] = (
                plaso_xmlrpc.XMLProcessStatusRPCClient()
            )

        test_engine._StopMonitoringProcesses()

        self.assertEqual(test_engine._process_information_per_pid, {})
        self.assertEqual(test_engine._rpc_clients_per_pid, {})
        self.assertEqual(len(test_engine._processes_per_pid), 2)

        # Test with a monitored process that is not registered.
        test_engine._process_information_per_pid[1003] = None

        with self.assertRaises(KeyError):
            test_engine._StopMonitoringProcesses()

    def testStopStatusUpdateThread(self):
        """Tests the _StopStatusUpdateThread function."""
        test_engine = TestEngine()
        test_engine._status_update_interval = 0.01

        # Test without a status update thread.
        test_engine._StopStatusUpdateThread()

        self.assertEqual(test_engine.number_of_status_updates, 1)

        test_engine._StartStatusUpdateThread()
        status_update_thread = test_engine._status_update_thread

        test_engine._StopStatusUpdateThread()

        self.assertFalse(test_engine._status_update_active)
        self.assertIsNone(test_engine._status_update_thread)
        self.assertFalse(status_update_thread.is_alive())

        # The status is updated at least once more on stop.
        self.assertGreaterEqual(test_engine.number_of_status_updates, 2)

    def testTerminateProcess(self):
        """Tests the _TerminateProcess function."""
        test_engine = TestEngine()

        test_process = TestProcess(1001, "Worker_00")

        with self.assertLogs("multi_process", level="WARNING"):
            test_engine._TerminateProcess(test_process)

        self.assertTrue(test_process.is_terminated)
        self.assertEqual(
            test_process.join_timeouts, [test_engine._PROCESS_JOIN_TIMEOUT]
        )
        self.assertEqual(test_engine.killed_pids, [])

        # Test with a process that does not stop when terminated.
        test_process = TestProcess(1002, "Worker_01", stops_on_terminate=False)

        with self.assertLogs("multi_process", level="WARNING"):
            test_engine._TerminateProcess(test_process)

        self.assertTrue(test_process.is_terminated)
        self.assertEqual(test_engine.killed_pids, [1002])


if __name__ == "__main__":
    unittest.main()
