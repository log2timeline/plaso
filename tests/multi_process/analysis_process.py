#!/usr/bin/env python3
"""Tests for the multi-processing analysis process."""

import os
import time
import unittest

from plaso.analysis import interface as analysis_interface
from plaso.analysis import mediator as analysis_mediator
from plaso.containers import events
from plaso.engine import configurations
from plaso.multi_process import analysis_process
from plaso.multi_process import plaso_queue
from plaso.multi_process import zeromq_queue

from tests import test_lib as shared_test_lib
from tests.multi_process import test_lib


class TestAnalysisPlugin(analysis_interface.AnalysisPlugin):
    """Analysis plugin for testing.

    Attributes:
      examined_events (list[tuple[EventObject, EventData, EventDataStream]]):
          events examined by the plugin.
    """

    NAME = "test_plugin"

    def __init__(self):
        """Initializes an analysis plugin for testing."""
        super().__init__()
        self.examined_events = []

    # pylint: disable=arguments-renamed
    # pylint: disable=unused-argument
    def CompileReport(self, mediator):
        """Compiles a report of the analysis.

        After the plugin has received every copy of an event to
        analyze this function will be called so that the report
        can be assembled.

        Args:
          mediator (AnalysisMediator): mediates interactions between
              analysis plugins and other components, such as storage and dfVFS.
        """
        return

    def ExamineEvent(self, mediator, event, event_data, event_data_stream):
        """Analyzes an event.

        Args:
          mediator (AnalysisMediator): mediates interactions between analysis
              plugins and other components, such as storage and dfVFS.
          event (EventObject): event.
          event_data (EventData): event data.
          event_data_stream (EventDataStream): event data stream.
        """
        self.examined_events.append((event, event_data, event_data_stream))


class TestFailingAnalysisPlugin(TestAnalysisPlugin):
    """Analysis plugin that fails to examine events for testing."""

    NAME = "test_failing_plugin"

    def ExamineEvent(self, mediator, event, event_data, event_data_stream):
        """Analyzes an event.

        Args:
          mediator (AnalysisMediator): mediates interactions between analysis
              plugins and other components, such as storage and dfVFS.
          event (EventObject): event.
          event_data (EventData): event data.
          event_data_stream (EventDataStream): event data stream.

        Raises:
          RuntimeError: always.
        """
        raise RuntimeError("Unable to examine event.")


class AnalysisProcessTest(test_lib.MultiProcessingTestCase):
    """Tests the multi-processing analysis process."""

    # pylint: disable=protected-access

    _QUEUE_TIMEOUT = 5

    def testInitialization(self):
        """Tests the initialization."""
        with shared_test_lib.TempDirectory() as temp_directory:
            configuration = configurations.ProcessingConfiguration()
            configuration.task_storage_path = temp_directory

            test_process = analysis_process.AnalysisProcess(
                None, None, configuration, [], name="TestAnalysis"
            )
            self.assertIsNotNone(test_process)

    def testGetStatus(self):
        """Tests the _GetStatus function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            configuration = configurations.ProcessingConfiguration()
            configuration.task_storage_path = temp_directory

            test_process = analysis_process.AnalysisProcess(
                None, None, configuration, [], name="TestAnalysis"
            )
            status_attributes = test_process._GetStatus()

            self.assertIsNotNone(status_attributes)
            self.assertEqual(status_attributes["identifier"], "TestAnalysis")
            self.assertIsNone(status_attributes["number_of_produced_reports"])

            # Test with an analysis mediator.
            test_mediator = analysis_mediator.AnalysisMediator()
            test_mediator.number_of_produced_analysis_reports = 1
            test_mediator.number_of_produced_event_tags = 5

            test_process._analysis_mediator = test_mediator

            status_attributes = test_process._GetStatus()

            self.assertIsNotNone(status_attributes)
            self.assertEqual(status_attributes["number_of_produced_event_tags"], 5)
            self.assertEqual(status_attributes["number_of_produced_reports"], 1)

    def testMain(self):
        """Tests the _Main function."""
        output_event_queue = zeromq_queue.ZeroMQPushBindQueue(
            name="test output event queue", timeout_seconds=self._QUEUE_TIMEOUT
        )
        output_event_queue.Open()

        input_event_queue = zeromq_queue.ZeroMQPullConnectQueue(
            name="test input event queue",
            delay_open=True,
            port=output_event_queue.port,
            timeout_seconds=self._QUEUE_TIMEOUT,
        )

        analysis_plugin = TestAnalysisPlugin()

        with shared_test_lib.TempDirectory() as temp_directory:
            # Set up the processed for the task storage file generated by the
            # analysis plugin.
            os.mkdir(os.path.join(temp_directory, "processed"))

            configuration = configurations.ProcessingConfiguration()
            configuration.task_storage_path = temp_directory

            test_process = analysis_process.AnalysisProcess(
                input_event_queue,
                analysis_plugin,
                configuration,
                [],
                name="TestAnalysis",
            )

            setattr(test_process, "_FOREMAN_STATUS_WAIT", 1)

            test_process.start()

            output_event_queue.PushItem(plaso_queue.QueueAbort(), block=False)
            output_event_queue.Close(abort=True)

            # Sleep for 1 second to allow the analysis process to terminate.
            # Before the temporary directory is removed.
            time.sleep(1)

    def testProcessEventTriple(self):
        """Tests the _ProcessEventTriple function."""
        event_triple = events.EventTriple()
        event_triple.event = events.EventObject()
        event_triple.event_data = events.EventData()
        event_triple.event_data_stream = events.EventDataStream()

        test_mediator = analysis_mediator.AnalysisMediator()

        with shared_test_lib.TempDirectory() as temp_directory:
            configuration = configurations.ProcessingConfiguration()
            configuration.task_storage_path = temp_directory

            analysis_plugin = TestAnalysisPlugin()
            test_process = analysis_process.AnalysisProcess(
                None, analysis_plugin, configuration, [], name="TestAnalysis"
            )
            test_process._ProcessEventTriple(test_mediator, event_triple)

            self.assertEqual(
                analysis_plugin.examined_events,
                [
                    (
                        event_triple.event,
                        event_triple.event_data,
                        event_triple.event_data_stream,
                    )
                ],
            )

            # Test with an analysis plugin that raises an exception.
            analysis_plugin = TestFailingAnalysisPlugin()
            test_process = analysis_process.AnalysisProcess(
                None, analysis_plugin, configuration, [], name="TestAnalysis"
            )

            with self.assertLogs("multi_process", level="WARNING") as log_context:
                test_process._ProcessEventTriple(test_mediator, event_triple)

            self.assertIn(
                "Unhandled exception while processing event object.",
                log_context.output[0],
            )

    def testSignalAbort(self):
        """Tests the SignalAbort function."""
        with shared_test_lib.TempDirectory() as temp_directory:
            configuration = configurations.ProcessingConfiguration()
            configuration.task_storage_path = temp_directory

            test_process = analysis_process.AnalysisProcess(
                None, None, configuration, [], name="TestAnalysis"
            )
            test_process.SignalAbort()


if __name__ == "__main__":
    unittest.main()
