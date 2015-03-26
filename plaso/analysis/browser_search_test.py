#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the browser search analysis plugin."""

import unittest

from plaso.analysis import browser_search
from plaso.analysis import test_lib
# pylint: disable=unused-import
from plaso.formatters import chrome as chrome_formatter
from plaso.lib import event
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import chrome


class BrowserSearchAnalysisTest(test_lib.AnalysisPluginTestCase):
  """Tests for the browser search analysis plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = sqlite.SQLiteParser()

  def testAnalyzeFile(self):
    """Read a storage file that contains URL data and analyze it."""
    knowledge_base = self._SetUpKnowledgeBase()

    test_file = self._GetTestFilePath(['History'])
    event_queue = self._ParseFile(self._parser, test_file, knowledge_base)

    analysis_plugin = browser_search.AnalyzeBrowserSearchPlugin(event_queue)
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEqual(len(analysis_reports), 1)

    analysis_report = analysis_reports[0]

    # Due to the behavior of the join one additional empty string at the end
    # is needed to create the last empty line.
    expected_text = u'\n'.join([
        u' == ENGINE: GoogleSearch ==',
        u'1 really really funny cats',
        u'1 java plugin',
        u'1 funnycats.exe',
        u'1 funny cats',
        u'',
        u''])

    self.assertEqual(analysis_report.text, expected_text)
    self.assertEqual(analysis_report.plugin_name, 'browser_search')

    expected_keys = set([u'GoogleSearch'])
    self.assertEqual(set(analysis_report.report_dict.keys()), expected_keys)


if __name__ == '__main__':
  unittest.main()
