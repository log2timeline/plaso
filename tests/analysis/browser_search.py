#!/usr/bin/env python3
"""Tests for the browser search analysis plugin."""

import collections
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

    def testGoogleSearchFilterExtractsLongQuery(self):
        """Tests that a Google search URL with a long query extracts its term."""
        plugin = browser_search.BrowserSearchPlugin()

        search_term = " ".join(["cat"] * 5000)
        query_value = "+".join(["cat"] * 5000)

        event_values_list = [
            {
                "data_type": "chrome:history:page_visited",
                "timestamp": "2020-01-01 12:00:00",
                "timestamp_desc": definitions.TIME_DESCRIPTION_LAST_VISITED,
                "url": "https://www.google.co.uk:443/search?q=" + query_value,
            }
        ]

        storage_writer = self._AnalyzeEvents(event_values_list, plugin)

        analysis_results = list(
            storage_writer.GetAttributeContainers("browser_search_analysis_result")
        )
        self.assertEqual(len(analysis_results), 1)

        analysis_result = analysis_results[0]
        self.assertEqual(analysis_result.search_engine, "Google Search")
        self.assertEqual(analysis_result.search_term, search_term)
        self.assertEqual(analysis_result.number_of_queries, 1)

    def testExamineEventWithSearchEngines(self):
        """Tests the ExamineEvent function with URLs of each search engine."""
        plugin = browser_search.BrowserSearchPlugin()

        test_values = [
            ("Bing", "https://www.bing.com/search?q=funny+cats&form=QBLH"),
            ("DuckDuckGo", "https://duckduckgo.com/?q=funny+cats&t=h_"),
            ("GMail", "https://mail.google.com/mail/u/0/#search/funny+cats"),
            ("Google Docs", "https://docs.google.com/document/u/0/?q=funny+cats"),
            ("Google Drive", "https://drive.google.com/drive/search?q=funny+cats"),
            ("Google Search", "https://www.google.com/search?q=funny%20cats&ie=UTF-8"),
            (
                "Google Sites",
                (
                    "https://sites.google.com/site/test/system/app/pages/"
                    "search?q=funny+cats"
                ),
            ),
            ("Yahoo", "https://search.yahoo.com/search?p=funny+cats&fr=yfp"),
            ("Yandex", "https://www.yandex.com/search/?text=funny+cats&lr=1"),
            ("Youtube", "https://www.youtube.com/search?q=funny+cats"),
        ]

        event_values_list = [
            {
                "data_type": "chrome:history:page_visited",
                "timestamp": "2020-01-01 12:00:00",
                "timestamp_desc": definitions.TIME_DESCRIPTION_LAST_VISITED,
                "url": url,
            }
            for _, url in test_values
        ]

        storage_writer = self._AnalyzeEvents(event_values_list, plugin)

        analysis_results = list(
            storage_writer.GetAttributeContainers("browser_search_analysis_result")
        )
        search_queries = sorted(
            (
                analysis_result.search_engine,
                analysis_result.search_term,
                analysis_result.number_of_queries,
            )
            for analysis_result in analysis_results
        )
        expected_search_queries = sorted(
            (engine, "funny cats", 1) for engine, _ in test_values
        )
        self.assertEqual(search_queries, expected_search_queries)

    def testExamineEventWithoutSearchQuery(self):
        """Tests the ExamineEvent function with URLs without a search query."""
        plugin = browser_search.BrowserSearchPlugin()

        urls = [
            "https://www.bing.com/maps?q=funny+cats",
            "https://duckduckgo.com/about",
            "https://mail.google.com/mail/u/0/#inbox",
            "https://docs.google.com/document/u/0/",
            "https://sites.google.com/site/test/?q=funny+cats",
            "https://search.yahoo.com/search?fr=yfp",
            "https://www.yandex.com/search/?lr=1",
            "https://www.youtube.com/watch?v=funny_cats",
        ]

        event_values_list = [
            {
                "data_type": "chrome:history:page_visited",
                "timestamp": "2020-01-01 12:00:00",
                "timestamp_desc": definitions.TIME_DESCRIPTION_LAST_VISITED,
                "url": url,
            }
            for url in urls
        ]

        storage_writer = self._AnalyzeEvents(event_values_list, plugin)

        number_of_results = storage_writer.GetNumberOfAttributeContainers(
            "browser_search_analysis_result"
        )
        self.assertEqual(number_of_results, 0)


if __name__ == "__main__":
    unittest.main()
