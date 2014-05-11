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
"""Tests for the OLE Compound File summary and document summary plugins."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import olecf as olecf_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers.olecf_plugins import summary
from plaso.parsers.olecf_plugins import test_lib


class TestSummaryInfoPlugin(test_lib.OleCfPluginTestCase):
  """Tests for the OLECF summary plugins."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._summary_plugin = summary.SummaryInfoPlugin(pre_obj)
    self._document_summary_plugin = summary.DocumentSummaryPlugin(pre_obj)
    self._test_file = self._GetTestFilePath(['Document.doc'])

  def testProcessSummaryInfo(self):
    """Tests the Process function on a SummaryInfo stream."""
    event_generator = self._ParseOleCfFileWithPlugin(
        self._test_file, self._summary_plugin)
    event_objects = self._GetEventObjects(event_generator)

    # There is one summary info stream with three event objects.
    self.assertEquals(len(event_objects), 3)

    event_object = event_objects[0]
    self.assertEquals(event_object.name, u'Summary Information')

    self.assertEquals(event_object.title, u'Table of Context')
    self.assertEquals(event_object.author, u'DAVID NIDES')
    self.assertEquals(event_object.template, u'Normal.dotm')
    self.assertEquals(event_object.last_saved_by, u'Nides')
    self.assertEquals(event_object.revision_number, u'4')
    self.assertEquals(event_object.number_of_characters, 18)
    self.assertEquals(event_object.application, u'Microsoft Office Word')
    self.assertEquals(event_object.security, 0)

    self.assertEquals(event_object.timestamp_desc, u'Document Creation Time')
    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2012-12-10 18:38:00')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'Title: Table of Context '
        u'Author: DAVID NIDES '
        u'Template: Normal.dotm '
        u'Revision number: 4 '
        u'Last saved by: Nides '
        u'Number of pages: 1 '
        u'Number of words: 3 '
        u'Number of characters: 18 '
        u'Application: Microsoft Office Word '
        u'Security: 0')

    expected_msg_short = (
        u'Title: Table of Context '
        u'Author: DAVID NIDES '
        u'Revision number: 4')

    # TODO: add support for:
    #    u'Total edit time (secs): 0 '

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

  def testProcessDocumentSummaryInfo(self):
    """Tests the Process function on a SummaryInfo stream."""
    event_generator = self._ParseOleCfFileWithPlugin(
        self._test_file, self._document_summary_plugin)
    event_objects = self._GetEventObjects(event_generator)

    # There should only be one summary info stream with one event.
    self.assertEquals(len(event_objects), 1)

    event_object = event_objects[0]
    self.assertEquals(event_object.name, u'Document Summary Information')

    self.assertEquals(event_object.number_of_lines, 1)
    self.assertEquals(event_object.number_of_paragraphs, 1)
    self.assertEquals(event_object.company, u'KPMG')
    self.assertFalse(event_object.shared_document)
    self.assertEquals(event_object.application_version, u'14.0')

    # TODO: add support for:
    # self.assertEquals(event_object.is_shared, False)

    expected_msg = (
        u'Number of lines: 1 '
        u'Number of paragraphs: 1 '
        u'Company: KPMG '
        u'Shared document: False '
        u'Application version: 14.0')

    expected_msg_short = (
        u'Company: KPMG')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
