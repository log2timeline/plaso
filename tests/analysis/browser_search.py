#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the browser search analysis plugin."""

import unittest

from plaso.analysis import browser_search
from plaso.containers import reports
from plaso.parsers import sqlite

from tests.analysis import test_lib


class BrowserSearchAnalysisTest(test_lib.AnalysisPluginTestCase):
  """Tests for the browser search analysis plugin."""

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    parser = sqlite.SQLiteParser()
    plugin = browser_search.BrowserSearchPlugin()

    storage_writer = self._ParseAndAnalyzeFile(['History'], parser, plugin)

    analysis_results = list(storage_writer.GetAttributeContainers(
        'browser_search_analysis_result'))
    self.assertEqual(len(analysis_results), 4)

    analysis_result = analysis_results[2]
    self.assertEqual(analysis_result.search_engine, 'Google Search')
    self.assertEqual(analysis_result.search_term, 'really really funny cats')
    self.assertEqual(analysis_result.number_of_queries, 1)

    number_of_reports = storage_writer.GetNumberOfAttributeContainers(
        'analysis_report')
    self.assertEqual(number_of_reports, 1)

    analysis_report = storage_writer.GetAttributeContainerByIndex(
        reports.AnalysisReport.CONTAINER_TYPE, 0)
    self.assertIsNotNone(analysis_report)
    self.assertEqual(analysis_report.plugin_name, 'browser_search')


if __name__ == '__main__':
  unittest.main()
