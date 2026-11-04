#!/usr/bin/env python3
"""Tests for the status view."""

import sys
import unittest

from unittest import mock

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

import plaso

from plaso.cli import status_view
from plaso.cli import views
from plaso.engine import processing_status

from tests.cli import test_lib


class StatusViewTest(test_lib.CLIToolTestCase):
    """Tests for the status view."""

    # pylint: disable=protected-access

    def _MockTime(self):
        """Mock function to simulate time.time()

        Returns:
          int: stored time via self._mocked_time
        """
        return self._mocked_time

    def setUp(self):
        """Makes preparations before running an individual test."""
        self.mock_time = mock.patch("plaso.cli.status_view.time.time", self._MockTime)
        self._mocked_time = 0
        self.mock_time.start()

    def tearDown(self):
        """Cleans up after running an individual test."""
        self.mock_time.stop()

    def _CheckOutput(self, output, expected_output):
        """Compares the output against the expected output.

        The actual processing time is ignored, since it can vary.

        Args:
          output (str): tool output.
          expected_output (list[str]): expected tool output.
        """
        output = output.split("\n")

        self.assertEqual(output[:4], expected_output[:4])
        self.assertTrue(output[4].startswith("Processing time\t\t: "))
        self.assertEqual(output[5:], expected_output[5:])

    def _CreateProcessingStatus(self):
        """Creates a processing status with a foreman and a worker status.

        Returns:
          ProcessingStatus: processing status.
        """
        process_status = processing_status.ProcessingStatus()
        process_status.UpdateForemanStatus(
            "f_identifier",
            "f_status",
            123,
            2048,
            "f_test_file",
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
        )
        process_status.UpdateWorkerStatus(
            "w_identifier",
            "w_status",
            456,
            0,
            "w_test_file",
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
        )
        return process_status

    def _CreateEventsStatus(self):
        """Creates an events status.

        Returns:
          EventsStatus: events status.
        """
        events_status = processing_status.EventsStatus()
        events_status.number_of_filtered_events = 1
        events_status.number_of_events_from_time_slice = 2
        events_status.number_of_duplicate_events = 3
        events_status.number_of_macb_grouped_events = 4
        events_status.total_number_of_events = 10
        return events_status

    def _FormatTableHeader(self, table_header):
        """Formats a table header the way the status view writes it.

        Args:
          table_header (str): table header.

        Returns:
          str: table header, in bold if ANSI is supported.
        """
        if not sys.platform.startswith("win"):
            table_header = f"\x1b[1m{table_header:s}\x1b[0m"
        return table_header

    def testAddsAnalysisProcessStatusTableRow(self):
        """Tests the _AddsAnalysisProcessStatusTableRow function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        process_status = self._CreateProcessingStatus()

        table_view = views.CLITabularTableView(column_sizes=[15, 7, 15, 15, 15, 15, 0])
        foreman_status = process_status.foreman_status
        test_view._AddsAnalysisProcessStatusTableRow(foreman_status, table_view)

        foreman_status.number_of_consumed_events = None
        test_view._AddsAnalysisProcessStatusTableRow(foreman_status, table_view)

        table_view.Write(output_writer)

        expected_output = [
            (
                "f_identifier    "
                "123     "
                "f_status        "
                "2.0 KiB         "
                "5 (5)           "
                "8 (8)           "
                "10 (10)"
            ),
            (
                "f_identifier    "
                "123     "
                "f_status        "
                "2.0 KiB         "
                "                "
                "8 (8)           "
                "10 (10)"
            ),
            "",
        ]
        output = output_writer.ReadOutput()
        self.assertEqual(output.split("\n"), expected_output)

    def testAddExtractionProcessStatusTableRow(self):
        """Tests the _AddExtractionProcessStatusTableRow function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        process_status = self._CreateProcessingStatus()

        table_view = views.CLITabularTableView(column_sizes=[15, 7, 15, 15, 15, 15, 0])
        foreman_status = process_status.foreman_status
        test_view._AddExtractionProcessStatusTableRow(foreman_status, table_view, True)
        test_view._AddExtractionProcessStatusTableRow(foreman_status, table_view, False)

        table_view.Write(output_writer)

        expected_output = [
            (
                "f_identifier    "
                "123     "
                "f_status        "
                "2.0 KiB         "
                "2 (2)           "
                "6 (6)           "
                "f_test_file"
            ),
            (
                "f_identifier    "
                "123     "
                "f_status        "
                "2.0 KiB         "
                "2 (2)           "
                "4 (4)           "
                "f_test_file"
            ),
            "",
        ]
        output = output_writer.ReadOutput()
        self.assertEqual(output.split("\n"), expected_output)

    def testClearScreen(self):
        """Tests the _ClearScreen function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")

        test_view._have_ansi_support = True
        test_view._ClearScreen()

        output = output_writer.ReadOutput()
        self.assertEqual(output, "\x1b[2J\x1b[H")

        if not sys.platform.startswith("win"):
            test_view._have_ansi_support = False
            test_view._ClearScreen()

            output = output_writer.ReadOutput()
            self.assertEqual(output, "")

    def testFormatSizeInUnitsOf1024(self):
        """Tests the _FormatSizeInUnitsOf1024 function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")

        self.assertEqual(test_view._FormatSizeInUnitsOf1024(0), "0 B")
        self.assertEqual(test_view._FormatSizeInUnitsOf1024(1023), "1023 B")
        self.assertEqual(test_view._FormatSizeInUnitsOf1024(1024), "1.0 KiB")
        self.assertEqual(test_view._FormatSizeInUnitsOf1024(1536), "1.5 KiB")
        self.assertEqual(test_view._FormatSizeInUnitsOf1024(1024**2), "1.0 MiB")
        self.assertEqual(test_view._FormatSizeInUnitsOf1024(5 * 1024**3), "5.0 GiB")
        self.assertEqual(test_view._FormatSizeInUnitsOf1024(1024**4), "1.0 TiB")

    # TODO: add tests for _FormatSizeInUnitsOf1024

    def testPrintAnalysisStatusHeader(self):
        """Tests the _PrintAnalysisStatusHeader function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        test_view.SetStorageFileInformation("/test/storage.plaso")

        process_status = processing_status.ProcessingStatus()
        test_view._PrintAnalysisStatusHeader(process_status)

        expected_output = [
            "Storage file\t\t: /test/storage.plaso",
            "Processing time\t\t: 00:00:00",
            "",
            "",
        ]
        output = output_writer.ReadOutput()
        self.assertEqual(output.split("\n"), expected_output)

        process_status.UpdateEventsStatus(self._CreateEventsStatus())
        test_view._PrintAnalysisStatusHeader(process_status)

        table_header = self._FormatTableHeader(
            "Events:         "
            "Filtered        "
            "In time slice   "
            "Duplicates      "
            "MACB grouped    "
            "Total"
        )
        expected_output = [
            "Storage file\t\t: /test/storage.plaso",
            "Processing time\t\t: 00:00:00",
            "",
            table_header,
            (
                "                "
                "1               "
                "2               "
                "3               "
                "4               "
                "10"
            ),
            "",
            "",
        ]
        output = output_writer.ReadOutput()
        self.assertEqual(output.split("\n"), expected_output)

    def testPrintAnalysisStatusUpdateLinear(self):
        """Tests the _PrintAnalysisStatusUpdateLinear function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        process_status = self._CreateProcessingStatus()

        test_view._PrintAnalysisStatusUpdateLinear(process_status)

        expected_output = (
            "Processing time: 00:00:00\n"
            "f_identifier (PID: 123) status: f_status, events consumed: 5\n"
            "w_identifier (PID: 456) status: w_status, events consumed: 5\n"
            "\n"
        )
        output = output_writer.ReadOutput()
        self.assertEqual(output, expected_output)

    def testPrintAnalysisStatusUpdateWindow(self):
        """Tests the _PrintAnalysisStatusUpdateWindow function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        test_view.SetStorageFileInformation("/test/storage.plaso")

        process_status = self._CreateProcessingStatus()
        test_view._PrintAnalysisStatusUpdateWindow(process_status)

        table_header = self._FormatTableHeader(
            "Identifier              "
            "PID     "
            "Status          "
            "Memory          "
            "Events          "
            "Tags            "
            "Reports"
        )
        expected_output = [
            f"plaso - test_tool version {plaso.__version__!s}",
            "",
            "Storage file\t\t: /test/storage.plaso",
            "Processing time\t\t: 00:00:00",
            "",
            table_header,
            (
                "f_identifier            "
                "123     "
                "f_status        "
                "2.0 KiB         "
                "5 (5)           "
                "8 (8)           "
                "10 (10)"
            ),
            (
                "w_identifier            "
                "456     "
                "w_status        "
                "0 B             "
                "5 (5)           "
                "8 (8)           "
                "10 (10)"
            ),
            "",
            "",
        ]
        output = output_writer.ReadOutput()
        self.assertEqual(output.split("\n"), expected_output)

        process_status.aborted = True
        test_view._PrintAnalysisStatusUpdateWindow(process_status)

        output = output_writer.ReadOutput()
        self.assertTrue(
            output.endswith("\n\nProcessing aborted - waiting for clean up.\n\n")
        )

    def testPrintEventsStatus(self):
        """Tests the _PrintEventsStatus function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        test_view._have_ansi_support = False

        test_view._PrintEventsStatus(None)

        output = output_writer.ReadOutput()
        self.assertEqual(output, "")

        test_view._PrintEventsStatus(self._CreateEventsStatus())

        expected_output = [
            "",
            (
                "Events:         "
                "Filtered        "
                "In time slice   "
                "Duplicates      "
                "MACB grouped    "
                "Total"
            ),
            (
                "                "
                "1               "
                "2               "
                "3               "
                "4               "
                "10"
            ),
            "",
        ]
        output = output_writer.ReadOutput()
        self.assertEqual(output.split("\n"), expected_output)

    def testPrintExtractionStatusUpdateLinear(self):
        """Tests the PrintExtractionStatusUpdateLinear function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        test_view.SetSourceInformation(
            "/test/source/path", dfvfs_definitions.SOURCE_TYPE_DIRECTORY
        )
        process_status = processing_status.ProcessingStatus()
        process_status.UpdateForemanStatus(
            "f_identifier",
            "f_status",
            123,
            0,
            "f_test_file",
            1,
            29,
            1,
            2,
            3,
            456,
            5,
            6,
            9,
            10,
        )
        test_view._PrintExtractionStatusUpdateLinear(process_status)

        expected_output = (
            "Processing time: 00:00:00\n"
            "f_identifier (PID: 123) status: f_status, event data produced: 2, "
            "events produced: 456, file: f_test_file\n"
            "\n"
        )

        output = output_writer.ReadOutput()
        self.assertEqual(output, expected_output)

        process_status.UpdateWorkerStatus(
            "w_identifier",
            "w_status",
            123,
            0,
            "w_test_file",
            1,
            2,
            3,
            4,
            5,
            6,
            9,
            10,
            11,
            12,
        )
        test_view._PrintExtractionStatusUpdateLinear(process_status)

        expected_output = (
            "Processing time: 00:00:00\n"
            "f_identifier (PID: 123) status: f_status, event data produced: 2, "
            "events produced: 456, file: f_test_file\n"
            "w_identifier (PID: 123) status: w_status, event data produced: 6, "
            "file: w_test_file\n"
            "\n"
        )
        output = output_writer.ReadOutput()
        self.assertEqual(output, expected_output)

    def testPrintExtractionStatusUpdateWindow(self):
        """Tests the _PrintExtractionStatusUpdateWindow function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        test_view.SetSourceInformation(
            "/test/source/path", dfvfs_definitions.SOURCE_TYPE_DIRECTORY
        )
        process_status = processing_status.ProcessingStatus()
        process_status.UpdateForemanStatus(
            "f_identifier",
            "f_status",
            123,
            0,
            "f_test_file",
            1,
            29,
            1,
            2,
            3,
            456,
            5,
            6,
            9,
            10,
        )
        test_view._PrintExtractionStatusUpdateWindow(process_status)

        table_header = (
            "Identifier      "
            "PID     "
            "Status          "
            "Memory          "
            "Sources         "
            "Events          "
            "File"
        )
        if not sys.platform.startswith("win"):
            table_header = f"\x1b[1m{table_header:s}\x1b[0m"

        expected_output = [
            f"plaso - test_tool version {plaso.__version__!s}",
            "",
            "Source path\t\t: /test/source/path",
            "Source type\t\t: directory",
            "Processing time\t\t: 00:00:00",
            "",
            table_header,
            (
                "f_identifier    "
                "123     "
                "f_status        "
                "0 B             "
                "29 (29)         "
                "456 (456)       "
                "f_test_file"
            ),
            "",
            "",
        ]
        output = output_writer.ReadOutput()
        self._CheckOutput(output, expected_output)

        process_status.UpdateWorkerStatus(
            "w_identifier",
            "w_status",
            123,
            0,
            "w_test_file",
            1,
            2,
            3,
            4,
            5,
            6,
            9,
            10,
            11,
            12,
        )
        test_view._PrintExtractionStatusUpdateWindow(process_status)

        table_header = (
            "Identifier      "
            "PID     "
            "Status          "
            "Memory          "
            "Sources         "
            "Event Data      "
            "File"
        )
        if not sys.platform.startswith("win"):
            table_header = f"\x1b[1m{table_header:s}\x1b[0m"

        expected_output = [
            f"plaso - test_tool version {plaso.__version__!s}",
            "",
            "Source path\t\t: /test/source/path",
            "Source type\t\t: directory",
            "Processing time\t\t: 00:00:00",
            "",
            table_header,
            (
                "f_identifier    "
                "123     "
                "f_status        "
                "0 B             "
                "29 (29)         "
                "2 (2)           "
                "f_test_file"
            ),
            (
                "w_identifier    "
                "123     "
                "w_status        "
                "0 B             "
                "2 (2)           "
                "4 (4)           "
                "w_test_file"
            ),
            "",
            "",
        ]
        output = output_writer.ReadOutput()
        self._CheckOutput(output, expected_output)

    def testFormatProcessingTime(self):
        """Tests the _FormatProcessingTime function."""
        output_writer = test_lib.TestOutputWriter()

        process_status = processing_status.ProcessingStatus()

        test_view = status_view.StatusView(output_writer, "test_tool")
        test_view.SetSourceInformation(
            "/test/source/path", dfvfs_definitions.SOURCE_TYPE_DIRECTORY
        )
        process_status.start_time = 0
        processing_time = test_view._FormatProcessingTime(process_status)

        self.assertEqual(processing_time, "00:00:00")

        self._mocked_time = 12 * 60 * 60 + 31 * 60 + 15
        processing_time = test_view._FormatProcessingTime(process_status)

        self.assertEqual(processing_time, "12:31:15")

        self._mocked_time = 24 * 60 * 60
        processing_time = test_view._FormatProcessingTime(process_status)

        self.assertEqual(processing_time, "1 day, 00:00:00")

        self._mocked_time = 5 * 24 * 60 * 60 + 5 * 60 * 60 + 61
        processing_time = test_view._FormatProcessingTime(process_status)

        self.assertEqual(processing_time, "5 days, 05:01:01")

    def testPrintTasksStatus(self):
        """Tests the _PrintTasksStatus function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        test_view._have_ansi_support = False

        process_status = processing_status.ProcessingStatus()

        test_view._PrintTasksStatus(None)
        test_view._PrintTasksStatus(process_status)

        output = output_writer.ReadOutput()
        self.assertEqual(output, "")

        tasks_status = processing_status.TasksStatus()
        tasks_status.number_of_queued_tasks = 1
        tasks_status.number_of_tasks_processing = 2
        tasks_status.number_of_tasks_pending_merge = 3
        tasks_status.number_of_abandoned_tasks = 4
        tasks_status.total_number_of_tasks = 10
        process_status.UpdateTasksStatus(tasks_status)

        test_view._PrintTasksStatus(process_status)

        expected_output = [
            "",
            (
                "Tasks:          "
                "Queued  "
                "Processing      "
                "Merging         "
                "Abandoned       "
                "Total"
            ),
            (
                "                "
                "1       "
                "2               "
                "3               "
                "4               "
                "10"
            ),
            "",
        ]
        output = output_writer.ReadOutput()
        self.assertEqual(output.split("\n"), expected_output)

    def testGetAnalysisStatusUpdateCallback(self):
        """Tests the GetAnalysisStatusUpdateCallback function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")

        test_view.SetMode(status_view.StatusView.MODE_FILE)
        callback = test_view.GetAnalysisStatusUpdateCallback()
        self.assertEqual(callback, test_view._PrintAnalysisStatusUpdateFile)

        test_view.SetMode(status_view.StatusView.MODE_LINEAR)
        callback = test_view.GetAnalysisStatusUpdateCallback()
        self.assertEqual(callback, test_view._PrintAnalysisStatusUpdateLinear)

        test_view.SetMode(status_view.StatusView.MODE_WINDOW)
        callback = test_view.GetAnalysisStatusUpdateCallback()
        self.assertEqual(callback, test_view._PrintAnalysisStatusUpdateWindow)

        test_view.SetMode("bogus")
        callback = test_view.GetAnalysisStatusUpdateCallback()
        self.assertIsNone(callback)

    def testGetExtractionStatusUpdateCallback(self):
        """Tests the GetExtractionStatusUpdateCallback function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")

        test_view.SetMode(status_view.StatusView.MODE_FILE)
        callback = test_view.GetExtractionStatusUpdateCallback()
        self.assertEqual(callback, test_view._PrintExtractionStatusUpdateFile)

        test_view.SetMode(status_view.StatusView.MODE_LINEAR)
        callback = test_view.GetExtractionStatusUpdateCallback()
        self.assertEqual(callback, test_view._PrintExtractionStatusUpdateLinear)

        test_view.SetMode(status_view.StatusView.MODE_WINDOW)
        callback = test_view.GetExtractionStatusUpdateCallback()
        self.assertEqual(callback, test_view._PrintExtractionStatusUpdateWindow)

        test_view.SetMode("bogus")
        callback = test_view.GetExtractionStatusUpdateCallback()
        self.assertIsNone(callback)

    def testPrintExtractionStatusHeader(self):
        """Tests the PrintExtractionStatusHeader function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        test_view.SetSourceInformation(
            "/test/source/path", dfvfs_definitions.SOURCE_TYPE_DIRECTORY
        )
        test_view.PrintExtractionStatusHeader(None)

    def testPrintExtractionSummary(self):
        """Tests the PrintExtractionSummary function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")

        test_view.PrintExtractionSummary(None, 0)

        output = output_writer.ReadOutput()
        self.assertEqual(output, "WARNING: missing processing status information.\n\n")

        process_status = processing_status.ProcessingStatus()
        test_view.PrintExtractionSummary(process_status, 0)

        output = output_writer.ReadOutput()
        self.assertEqual(output, "Processing completed.\n\n")

        test_view.PrintExtractionSummary(process_status, 2)

        expected_output = (
            "Processing completed.\n"
            "\n"
            "Number of warnings generated while extracting events: 2.\n"
            "\n"
            "Use pinfo to inspect warnings in more detail.\n"
            "\n"
        )
        output = output_writer.ReadOutput()
        self.assertEqual(output, expected_output)

        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_FAKE, location="/test/file\x01name"
        )
        process_status.error_path_specs = [path_spec]
        test_view.PrintExtractionSummary(process_status, 0)

        expected_output = (
            "Processing completed with errors.\n"
            "\n"
            "Path specifications that could not be processed:\n"
            "type: FAKE, location: /test/file\\x01name\n"
            "\n"
            "\n"
        )
        output = output_writer.ReadOutput()
        self.assertEqual(output, expected_output)

        process_status.aborted = True
        test_view.PrintExtractionSummary(process_status, 2)

        output = output_writer.ReadOutput()
        self.assertEqual(output, "\n")

    def testSetMode(self):
        """Tests the SetMode function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        self.assertEqual(test_view._mode, status_view.StatusView.MODE_WINDOW)

        test_view.SetMode(status_view.StatusView.MODE_LINEAR)
        self.assertEqual(test_view._mode, status_view.StatusView.MODE_LINEAR)

    def testSetSourceInformation(self):
        """Tests the SetSourceInformation function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        test_view.SetSourceInformation(
            "/test/source/image.raw",
            dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE,
            artifact_filters=["WindowsEventLogs", "WindowsRegistryFiles"],
            filter_file="/test/filter.txt",
        )
        test_view.PrintExtractionStatusHeader(None)

        expected_output = (
            "Source path\t\t: /test/source/image.raw\n"
            "Source type\t\t: storage media image\n"
            "Artifact filters\t: WindowsEventLogs, WindowsRegistryFiles\n"
            "Filter file\t\t: /test/filter.txt\n"
            "Processing time\t\t: 00:00:00\n"
            "\n"
        )
        output = output_writer.ReadOutput()
        self.assertEqual(output, expected_output)

        test_view.SetSourceInformation("/test/source/path", "bogus")
        self.assertEqual(test_view._source_type, "UNKNOWN")
        self.assertIsNone(test_view._artifact_filters)
        self.assertIsNone(test_view._filter_file)

    def testSetStorageFileInformation(self):
        """Tests the SetStorageFileInformation function."""
        output_writer = test_lib.TestOutputWriter()

        test_view = status_view.StatusView(output_writer, "test_tool")
        self.assertIsNone(test_view._storage_file_path)

        test_view.SetStorageFileInformation("/test/storage.plaso")
        self.assertEqual(test_view._storage_file_path, "/test/storage.plaso")


if __name__ == "__main__":
    unittest.main()
