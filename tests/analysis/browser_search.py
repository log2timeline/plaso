#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the browser search analysis plugin."""

import unittest

from plaso.analysis import browser_search
from plaso.parsers import sqlite

from tests import test_lib as shared_test_lib
from tests.analysis import test_lib


@shared_test_lib.skipUnlessHasTestFile([u'History'])
class BrowserSearchAnalysisTest(test_lib.AnalysisPluginTestCase):
  """Tests for the browser search analysis plugin."""

  def testExamineEventAndCompileReport(self):
    """Tests the ExamineEvent and CompileReport functions."""
    parser = sqlite.SQLiteParser()
    plugin = browser_search.BrowserSearchPlugin()

    storage_writer = self._ParseAndAnalyzeFile([u'History'], parser, plugin)

    self.assertEqual(storage_writer.number_of_events, 71)

    self.assertEqual(len(storage_writer.analysis_reports), 1)

    analysis_report = storage_writer.analysis_reports[0]

    # Due to the behavior of the join one additional empty string at the end
    # is needed to create the last empty line.
    expected_text = u'\n'.join([
        u' == ENGINE: Google Search ==',
        u'1 really really funny cats',
        u'1 java plugin',
        u'1 funnycats.exe',
        u'1 funny cats',
        u'',
        u''])

    self.assertEqual(analysis_report.text, expected_text)
    self.assertEqual(analysis_report.plugin_name, u'browser_search')

    expected_keys = set([u'Google Search'])
    self.assertEqual(set(analysis_report.report_dict.keys()), expected_keys)


if __name__ == '__main__':
  unittest.main()
