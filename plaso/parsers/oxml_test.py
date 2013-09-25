#!/usr/bin/python
# -*- coding: utf-8 -*-
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

# Shut up pylint.
# * W0611: 28,0: Unused import oxml_formatter
# pylint: disable=W0611
from plaso.formatters import oxml as oxml_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import oxml


class OXMLTest(unittest.TestCase):
  """Tests for the OXML parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.test_parser = oxml.OpenXMLParser(pre_obj)
    # Show full diff results, part of TestCase so does not
    # follow our naming conventions.
    self.maxDiff = None

  def testParseFile(self):
    """Read a OLECF file and run a few tests."""
    test_file = os.path.join('test_data', 'Document.docx')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    self.assertEquals(len(events), 2)

    # Date: 2012-11-07T23:29:00.000000+00:00.
    self.assertEquals(events[0].timestamp, 1352330940000000)
    self.assertEquals(events[0].timestamp_desc,
                      eventdata.EventTimestamp.CREATION_TIME)

    event_object = events[1]

    self.assertEquals(event_object.num_chars, '13')
    self.assertEquals(event_object.total_time, '1385')
    self.assertEquals(event_object.characters_with_spaces, '14')
    self.assertEquals(event_object.i4, '1')
    self.assertEquals(event_object.app_version, '14.0000')
    self.assertEquals(event_object.num_lines, '1')
    self.assertEquals(event_object.scale_crop, 'false')
    self.assertEquals(event_object.num_pages, '1')
    self.assertEquals(event_object.num_words, '2')
    self.assertEquals(event_object.links_up_to_date, 'false')
    self.assertEquals(event_object.num_paragraphs, '1')
    self.assertEquals(event_object.doc_security, '0')
    self.assertEquals(event_object.hyperlinks_changed, 'false')
    self.assertEquals(event_object.revision_num, '3')
    self.assertEquals(event_object.last_saved_by, 'Nides')
    self.assertEquals(event_object.author, 'Nides')
    self.assertEquals(event_object.creating_app,
                      'Microsoft Office Word')
    self.assertEquals(event_object.template, 'Normal.dotm')

    # Test the event specific formatter.
    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    # TODO: Add test for msg_short.
    self.assertEquals(msg, (
      u'Creating App: Microsoft Office Word App '
      'version: 14.0000 Last saved by: Nides Author: Nides '
      'Revision Num: 3 '
      'Template: Normal.dotm Num pages: 1 '
      'Num words: 2 Num chars: 13 Num lines: 1 '
      'Hyperlinks changed: false '
      'Links up to date: false '
      'Scale crop: false'))


if __name__ == '__main__':
  unittest.main()
