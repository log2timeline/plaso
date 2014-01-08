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
"""Tests for the browser_search analysis plugin."""

import os
import unittest

from plaso.analysis import browser_search
# pylint: disable-msg=unused-import
from plaso.formatters import chrome as chrome_formatter
from plaso.lib import analysis_interface
from plaso.lib import preprocess
from plaso.lib import queue
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import chrome
from plaso.pvfs import pfile

import pytz


class BrowserSearchAnalysisTest(unittest.TestCase):
  """Tests for the browser search analysis plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.utc
    self._parser = sqlite.SQLiteParser(pre_obj, None)

    # Create queues and other necessary objects.
    self._incoming_queue = queue.SingleThreadedQueue()
    self._outgoing_queue = queue.SingleThreadedQueue()

    # Initialize plugin.
    self._analysis_plugin = browser_search.AnalyzeBrowserSearchPlugin(
        pre_obj, self._incoming_queue, self._outgoing_queue)

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testAnalyzeFile(self):
    """Read a storage file that contains URL data and analyze it."""
    test_file = os.path.join('test_data', 'History')
    path_spec = pfile.PFileResolver.CopyPathToPathSpec('OS', test_file)
    file_entry = pfile.PFileResolver.OpenFileEntry(path_spec)

    # Fill the incoming queue with events.
    for event_object in self._parser.Parse(file_entry):
      self._incoming_queue.AddEvent(event_object.ToJson())

    self._incoming_queue.Close()

    # Run the analysis plugin.
    self._analysis_plugin.RunPlugin()

    # Get the report out.
    self._outgoing_queue.Close()
    output = []
    for item in self._outgoing_queue.PopItems():
      output.append(item)

    # There is only a report returned back.
    self.assertEquals(len(output), 1)

    report_string = output[0]
    self.assertEquals(
        report_string[0], analysis_interface.MESSAGE_STRUCT.build(
            analysis_interface.MESSAGE_REPORT))

    report = analysis_interface.AnalysisReport()
    report.FromProtoString(report_string[1:])

    # Due to the behavior of the join one additional empty string at the end
    # is needed to create the last empty line.
    expected_text = '\n'.join([
        u' == ENGINE: GoogleSearch ==',
        u'1 really really funny cats',
        u'1 java plugin',
        u'1 funnycats.exe',
        u'1 funny cats',
        u'',
        u''])

    self.assertEquals(expected_text, report.text)
    self.assertEquals(report.plugin_name, 'browser_search')

    self.assertEquals(report.report_dict.keys(), ['GoogleSearch'])


if __name__ == '__main__':
  unittest.main()
