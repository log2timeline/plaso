#!/usr/bin/env python3
"""Tests for the multi-processing base process."""

import unittest

from plaso.engine import configurations
from plaso.multi_process import base_process

from tests import test_lib as shared_test_lib


class TestProcess(base_process.MultiProcessBaseProcess):
    """Implementation of the multi-processing base process for testing."""

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

    def SignalAbort(self):
        """Signals the process to abort."""
        # TODO: implement.
        return


class FailingTestProcess(TestProcess):
    """Implementation of the multi-processing base process that fails."""

    def _Main(self):
        """The process main loop.

        Raises:
          RuntimeError: always.
        """
        raise RuntimeError("Main loop failed for testing.")


class MultiProcessBaseProcessTest(shared_test_lib.BaseTestCase):
    """Tests the multi-processing base process."""

    # pylint: disable=protected-access

    def testInitialization(self):
        """Tests the initialization."""
        configuration = configurations.ProcessingConfiguration()

        test_process = TestProcess(configuration, name="TestBase")
        self.assertIsNotNone(test_process)

    # TODO: add test for name property.
    # TODO: add test for _OnCriticalError.
    # TODO: add test for _SigSegvHandler.
    # TODO: add test for _SigTermHandler.
    # TODO: add test for _StartProcessStatusRPCServer.
    # TODO: add test for _StopProcessStatusRPCServer.

    def testRunWithFailingMain(self):
        """Tests that the process exits when the main loop raises."""
        configuration = configurations.ProcessingConfiguration()

        test_process = FailingTestProcess(configuration, name="TestFailing")
        test_process.start()
        try:
            test_process.join(timeout=60)
            self.assertFalse(test_process.is_alive())
            self.assertEqual(test_process.exitcode, 1)

        finally:
            if test_process.is_alive():
                test_process.kill()
                test_process.join()


if __name__ == "__main__":
    unittest.main()
