#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the browser search analysis plugin."""

import unittest

from plaso.analysis import browser_search
from plaso.engine import single_process
from plaso.parsers import sqlite

from tests.analysis import test_lib


class BrowserSearchAnalysisTest(test_lib.AnalysisPluginTestCase):
  """Tests for the browser search analysis plugin."""

  def testAnalyzeFile(self):
    """Read a storage file that contains URL data and analyze it."""
    parser = sqlite.SQLiteParser()
    knowledge_base = self._SetUpKnowledgeBase()
    storage_writer = self._ParseFile([u'History'], parser, knowledge_base)

    self.assertEqual(len(storage_writer.events), 71)

    event_queue = single_process.SingleProcessQueue()
    event_queue_producer = test_lib.TestEventObjectProducer(
        event_queue, storage_writer)
    event_queue_producer.Run()

    analysis_plugin = browser_search.BrowserSearchPlugin(event_queue)
    analysis_report_queue_consumer = self._RunAnalysisPlugin(
        analysis_plugin, knowledge_base)
    analysis_reports = self._GetAnalysisReportsFromQueue(
        analysis_report_queue_consumer)

    self.assertEqual(len(analysis_reports), 1)

    analysis_report = analysis_reports[0]

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
