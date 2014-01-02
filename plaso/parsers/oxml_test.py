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
"""Tests for the OXML parser."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import oxml as oxml_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import oxml
from plaso.parsers import test_lib


class OXMLTest(test_lib.ParserTestCase):
  """Tests for the OXML parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self._parser = oxml.OpenXMLParser(pre_obj)
    # Show full diff results, part of TestCase so does not
    # follow our naming conventions.
    self.maxDiff = None

  def testParse(self):
    """Tests the Parse function."""
    test_file = os.path.join('test_data', 'Document.docx')
    events = self._ParseFile(self._parser, test_file)
    event_container = self._GetEventContainer(events)

    self.assertEquals(len(event_container.events), 2)

    event_object = event_container.events[0]

    # Date: 2012-11-07T23:29:00.000000+00:00.
    self.assertEquals(event_object.timestamp, 1352330940000000)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)

    event_object = event_container.events[1]

    self.assertEquals(event_object.num_chars, u'13')
    self.assertEquals(event_object.total_time, u'1385')
    self.assertEquals(event_object.characters_with_spaces, u'14')
    self.assertEquals(event_object.i4, u'1')
    self.assertEquals(event_object.app_version, u'14.0000')
    self.assertEquals(event_object.num_lines, u'1')
    self.assertEquals(event_object.scale_crop, u'false')
    self.assertEquals(event_object.num_pages, u'1')
    self.assertEquals(event_object.num_words, u'2')
    self.assertEquals(event_object.links_up_to_date, u'false')
    self.assertEquals(event_object.num_paragraphs, u'1')
    self.assertEquals(event_object.doc_security, u'0')
    self.assertEquals(event_object.hyperlinks_changed, u'false')
    self.assertEquals(event_object.revision_num, u'3')
    self.assertEquals(event_object.last_saved_by, u'Nides')
    self.assertEquals(event_object.author, u'Nides')
    self.assertEquals(
        event_object.creating_app, u'Microsoft Office Word')
    self.assertEquals(event_object.template, u'Normal.dotm')

    expected_msg = (
        u'Creating App: Microsoft Office Word '
        u'App version: 14.0000 '
        u'Last saved by: Nides '
        u'Author: Nides '
        u'Revision Num: 3 '
        u'Template: Normal.dotm '
        u'Num pages: 1 '
        u'Num words: 2 '
        u'Num chars: 13 '
        u'Num lines: 1 '
        u'Hyperlinks changed: false '
        u'Links up to date: false '
        u'Scale crop: false')
    expected_msg_short = (
        u'Author: Nides')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
