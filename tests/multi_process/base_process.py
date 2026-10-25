#!/usr/bin/env python3
"""Tests for the multi-processing base process."""

import os
import signal
import unittest

from plaso.engine import configurations
from plaso.multi_process import base_process
from plaso.multi_process import plaso_xmlrpc

from tests import test_lib as shared_test_lib


class TestProcess(base_process.MultiProcessBaseProcess):
    """Implementation of the multi-processing base process for testing.

    Attributes:
      abort_signaled (bool): True if abort was signaled.
      critical_error_handled (bool): True if a critical error was handled.
    """

    def __init__(self, processing_configuration, **kwargs):
        """Initializes a process for testing.

        Args:
          processing_configuration (ProcessingConfiguration): processing
              configuration.
          kwargs (dict[str,object]): keyword arguments to pass to
              multiprocessing.Process.
        """
        super().__init__(processing_configuration, **kwargs)
        self.abort_signaled = False
        self.critical_error_handled = False

    def _GetStatus(self):
        """Returns status information.

        Returns:
          dict[str, object]: status attributes, indexed by name.
        """
        # TODO: implement.
        return {}

    def _Main(self):
        """The process main loop.

        This method is called when the process is ready to start. A sub class should
        override this method to do the necessary actions in the main loop.
        """
        # TODO: implement.
        return

    def _OnCriticalError(self):
        """The process on critical error handler."""
        self.critical_error_handled = True
        super()._OnCriticalError()

    def SignalAbort(self):
        """Signals the process to abort."""
        self.abort_signaled = True


class MultiProcessBaseProcessTest(shared_test_lib.BaseTestCase):
    """Tests the multi-processing base process."""

    # pylint: disable=protected-access

    def testInitialization(self):
        """Tests the initialization."""
        configuration = configurations.ProcessingConfiguration()

        test_process = TestProcess(configuration, name="TestBase")
        self.assertIsNotNone(test_process)

    def testName(self):
        """Tests the name property."""
        configuration = configurations.ProcessingConfiguration()

        test_process = TestProcess(configuration, name="TestBase")
        self.assertEqual(test_process.name, "TestBase")

    def testOnCriticalError(self):
        """Tests the _OnCriticalError function."""
        configuration = configurations.ProcessingConfiguration()

        test_process = TestProcess(configuration, name="TestBase")

        # The default critical error handler does not change the process state.
        result = base_process.MultiProcessBaseProcess._OnCriticalError(test_process)
        self.assertIsNone(result)

        self.assertFalse(test_process.abort_signaled)
        self.assertFalse(test_process.critical_error_handled)
        self.assertIsNone(test_process._rpc_server)

    def testSigSegvHandler(self):
        """Tests the _SigSegvHandler function."""
        configuration = configurations.ProcessingConfiguration()

        test_process = TestProcess(configuration, name="TestBase")

        # Without an original SIGSEGV handler the handler only invokes the critical
        # error handler.
        sigsegv_handler = signal.getsignal(signal.SIGSEGV)
        test_process._SigSegvHandler(signal.SIGSEGV, None)

        self.assertTrue(test_process.critical_error_handled)
        self.assertEqual(signal.getsignal(signal.SIGSEGV), sigsegv_handler)

    def testSigTermHandler(self):
        """Tests the _SigTermHandler function."""
        configuration = configurations.ProcessingConfiguration()

        test_process = TestProcess(configuration, name="TestBase")
        test_process._SigTermHandler(signal.SIGTERM, None)

        self.assertTrue(test_process.abort_signaled)
        self.assertFalse(test_process.critical_error_handled)

    def testStartProcessStatusRPCServer(self):
        """Tests the _StartProcessStatusRPCServer function."""
        configuration = configurations.ProcessingConfiguration()

        test_process = TestProcess(configuration, name="TestBase")
        test_process._pid = os.getpid()

        test_process._StartProcessStatusRPCServer()

        rpc_server = test_process._rpc_server
        try:
            self.assertIsNotNone(rpc_server)
            self.assertNotEqual(test_process.rpc_port.value, 0)

            # Test that a running RPC server is not replaced.
            test_process._StartProcessStatusRPCServer()
            self.assertIs(test_process._rpc_server, rpc_server)

            rpc_client = plaso_xmlrpc.XMLProcessStatusRPCClient()
            result = rpc_client.Open("localhost", test_process.rpc_port.value)
            self.assertTrue(result)

            process_status = rpc_client.CallFunction()
            rpc_client.Close()

        finally:
            rpc_server.Stop()

        self.assertEqual(process_status, {})

    # TODO: add test for _StopProcessStatusRPCServer.
    # TODO: add test for _WaitForStatusNotRunning.
    # TODO: add test for run.


if __name__ == "__main__":
    unittest.main()
