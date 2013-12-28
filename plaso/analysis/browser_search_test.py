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
from plaso.pvfs import utils

import pytz


class BrowserSearchAnalysisTest(unittest.TestCase):
  """Tests for the browser search analysis plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testAnalyzeFile(self):
    """Read a storage file that contains URL data and analyze it."""
    # Create queues and other necessary objects.
    incoming_queue = queue.SingleThreadedQueue()
    outgoing_queue = queue.SingleThreadedQueue()
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.utc

    # Create a parser and open file.
    parser = sqlite.SQLiteParser(pre_obj, None)
    test_file = os.path.join('test_data', 'History')
    file_entry = utils.OpenOSFileEntry(test_file)

    # Initialize plugin.
    analysis_plugin = browser_search.AnalyzeBrowserSearchPlugin(
        pre_obj, incoming_queue, outgoing_queue)

    # Fill the incoming queue with events.
    for event_object in parser.Parse(file_entry):
      incoming_queue.AddEvent(event_object.ToJson())

    incoming_queue.Close()

    # Run the analysis plugin.
    analysis_plugin.RunPlugin()

    # Get the report out.
    outgoing_queue.Close()
    output = []
    for item in outgoing_queue.PopItems():
      output.append(item)

    # There is only a report returned back.
    self.assertEquals(len(output), 1)

    report_string = output[0]
    self.assertEquals(
        report_string[0], analysis_interface.MESSAGE_STRUCT.build(
            analysis_interface.MESSAGE_REPORT))

    report = analysis_interface.AnalysisReport()
    report.FromProtoString(report_string[1:])

    expected_text = """\
 == ENGINE: GoogleSearch ==
1 really really funny cats
1 java plugin
1 funnycats.exe
1 funny cats

"""

    self.assertEquals(expected_text, report.text)
    self.assertEquals(report.plugin_name, 'browser_search')

    self.assertEquals(report.report_dict.keys(), ['GoogleSearch'])


if __name__ == '__main__':
  unittest.main()
