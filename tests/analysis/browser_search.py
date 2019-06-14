#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the browser search analysis plugin."""

from __future__ import unicode_literals

import unittest

from plaso.analysis import browser_search
from plaso.parsers import sqlite

from tests.analysis import test_lib


class BrowserSearchAnalysisTest(test_lib.AnalysisPluginTestCase):
  """Tests for the browser search analysis plugin."""

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    parser = sqlite.SQLiteParser()
    plugin = browser_search.BrowserSearchPlugin()

    storage_writer = self._ParseAndAnalyzeFile(['History'], parser, plugin)

    self.assertEqual(storage_writer.number_of_events, 71)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    # Due to the behavior of the join one additional empty string at the end
    # is needed to create the last empty line.
    expected_text = '\n'.join([
        ' == ENGINE: Google Search ==',
        '1 really really funny cats',
        '1 java plugin',
        '1 funnycats.exe',
        '1 funny cats',
        '',
        ''])

    self.assertEqual(analysis_report.text, expected_text)
    self.assertEqual(analysis_report.plugin_name, 'browser_search')

    expected_keys = set(['Google Search'])
    self.assertEqual(set(analysis_report.report_dict.keys()), expected_keys)


if __name__ == '__main__':
  unittest.main()
