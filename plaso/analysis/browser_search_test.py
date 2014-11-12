#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

    self.assertEquals(len(analysis_reports), 1)

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

    self.assertEquals(analysis_report.text, expected_text)
    self.assertEquals(analysis_report.plugin_name, 'browser_search')

    expected_keys = set([u'GoogleSearch'])
    self.assertEquals(set(analysis_report.report_dict.keys()), expected_keys)


if __name__ == '__main__':
  unittest.main()
