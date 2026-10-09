#!/usr/bin/env python3
"""Tests for the browser search analysis plugin."""

import collections
import time
import unittest

from plaso.analysis import browser_search
from plaso.containers import reports
from plaso.lib import definitions
from plaso.parsers import sqlite

from tests.analysis import test_lib


class BrowserSearchAnalysisTest(test_lib.AnalysisPluginTestCase):
    """Tests for the browser search analysis plugin."""

    def testExamineEventAndCompileReport(self):
        """Tests the ExamineEvent and CompileReport functions."""
        parser = sqlite.SQLiteParser()
        plugin = browser_search.BrowserSearchPlugin()

        storage_writer = self._ParseAndAnalyzeFile(
            ["chrome", "History"], parser, plugin
        )
        analysis_results = list(
            storage_writer.GetAttributeContainers("browser_search_analysis_result")
        )
        self.assertEqual(len(analysis_results), 4)

        analysis_result = analysis_results[2]
        self.assertEqual(analysis_result.search_engine, "Google Search")
        self.assertEqual(analysis_result.search_term, "really really funny cats")
        self.assertEqual(analysis_result.number_of_queries, 1)

        number_of_reports = storage_writer.GetNumberOfAttributeContainers(
            "analysis_report"
        )
        self.assertEqual(number_of_reports, 1)

        analysis_report = storage_writer.GetAttributeContainerByIndex(
            reports.AnalysisReport.CONTAINER_TYPE, 0
        )
        self.assertIsNotNone(analysis_report)

        self.assertEqual(analysis_report.plugin_name, "browser_search")

        expected_analysis_counter = collections.Counter(
            {
                "Google Search:funny cats": 1,
                "Google Search:funnycats.exe": 1,
                "Google Search:java plugin": 1,
                "Google Search:really really funny cats": 1,
            }
        )
        self.assertEqual(analysis_report.analysis_counter, expected_analysis_counter)

    def testGoogleSearchFilterExtractsNormalQuery(self):
        """Tests that a regular Google search URL still extracts its term."""
        plugin = browser_search.BrowserSearchPlugin()

        event_values_list = [
            {
                "data_type": "chrome:history:page_visited",
                "timestamp": "2020-01-01 12:00:00",
                "timestamp_desc": definitions.TIME_DESCRIPTION_LAST_VISITED,
                "url": "https://www.google.com/search?q=really+really+funny+cats",
            }
        ]

        storage_writer = self._AnalyzeEvents(event_values_list, plugin)

        analysis_results = list(
            storage_writer.GetAttributeContainers("browser_search_analysis_result")
        )
        self.assertEqual(len(analysis_results), 1)

        analysis_result = analysis_results[0]
        self.assertEqual(analysis_result.search_engine, "Google Search")
        self.assertEqual(analysis_result.search_term, "really really funny cats")
        self.assertEqual(analysis_result.number_of_queries, 1)

    def testGoogleSearchFilterOnLongURL(self):
        """Tests that the Google Search filter stays fast on a long URL.

        A long URL value that contains many slash-free "google." tokens but no
        "/search" path made the unbounded Google Search filter expression rescan
        the remainder of the value from every "google." token, so the time to
        examine a single event grew with the square of the URL length. This
        regression test asserts the filter runs in time proportional to the URL
        length instead.
        """
        plugin = browser_search.BrowserSearchPlugin()

        long_url = "https://www.google.com/url?q=" + ("www.google." * 32000)

        event_values_list = [
            {
                "data_type": "chrome:history:page_visited",
                "timestamp": "2020-01-01 12:00:00",
                "timestamp_desc": definitions.TIME_DESCRIPTION_LAST_VISITED,
                "url": long_url,
            }
        ]

        start_time = time.monotonic()
        storage_writer = self._AnalyzeEvents(event_values_list, plugin)
        elapsed_time = time.monotonic() - start_time

        # The unbounded expression needs roughly 10 seconds for this input; the
        # bounded expression needs tens of milliseconds. A generous budget keeps
        # the test from flaking on slow machines while still catching a
        # regression to superlinear behavior.
        self.assertLess(elapsed_time, 2.0)

        # The long URL is not a Google search, so no result is produced.
        analysis_results = list(
            storage_writer.GetAttributeContainers("browser_search_analysis_result")
        )
        self.assertEqual(len(analysis_results), 0)


if __name__ == "__main__":
    unittest.main()
