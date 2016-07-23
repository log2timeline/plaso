#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the browser search analysis plugin."""

import unittest

from plaso.analysis import browser_search
from plaso.analysis import mediator
from plaso.parsers import sqlite

from tests.analysis import test_lib


class BrowserSearchAnalysisTest(test_lib.AnalysisPluginTestCase):
  """Tests for the browser search analysis plugin."""

  def testExamineEvent(self):
    """Tests the ExamineEvent function."""
    knowledge_base = self._SetUpKnowledgeBase()
    analysis_mediator = mediator.AnalysisMediator(None, knowledge_base)

    parser = sqlite.SQLiteParser()
    storage_writer = self._ParseFile([u'History'], parser, knowledge_base)

    self.assertEqual(len(storage_writer.events), 71)

    analysis_plugin = browser_search.BrowserSearchPlugin()

    for event in storage_writer.events:
      analysis_plugin.ExamineEvent(analysis_mediator, event)

    analysis_report = analysis_plugin.CompileReport(analysis_mediator)
    self.assertIsNotNone(analysis_report)

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
