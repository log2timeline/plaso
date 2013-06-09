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
"""Tests for the OLECF parser."""

import os
import unittest

from plaso.formatters import olecf
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import olecf


class OLECFTest(unittest.TestCase):
  """Tests for the OLECF parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self.test_parser = olecf.OLECF(pre_obj)
    # Show full diff results, part of TestCase so does not 
    # follow our naming conventions.
    self.maxDiff = None

  def testParseFile(self):
    """Read a OLECF file and run a few tests."""
    test_file = os.path.join('test_data', 'Document.doc')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self.test_parser.Parse(file_object))

    self.assertEquals(len(events), 2)

    # Date: 2012-12-10T18:38:00.000000+00:00.
    self.assertEquals(events[0].timestamp, 1355164680000000)
    self.assertEquals(events[0].timestamp_desc,
                      eventdata.EventTimestamp.CREATION_TIME)

    event_object = events[1]

    self.assertEquals(event_object.num_chars, 18)
    self.assertEquals(event_object.revision_number, '4')
    self.assertEquals(event_object.last_saved_by, 'Nides')
    self.assertEquals(event_object.author, 'DAVID NIDES')
    self.assertEquals(event_object.title, 'Table of Context')
    self.assertEquals(event_object.security, 0)
    self.assertEquals(event_object.creating_application,
                      'Microsoft Office Word')
    self.assertEquals(event_object.codepage, 1252)
    self.assertEquals(event_object.template, 'Normal.dotm')
    self.assertEquals(event_object.company, 'KPMG')
    self.assertEquals(event_object.manager, None)
    self.assertEquals(event_object.slides, None)
    self.assertEquals(event_object.hidden_slides, None)
    self.assertEquals(event_object.version, 917504)
    self.assertEquals(event_object.doc_version, None)
    self.assertEquals(event_object.m_notes, None)
    self.assertEquals(event_object.dig_sig, None)
    self.assertEquals(event_object.shared_doc, False)
    self.assertEquals(event_object.language, None)
    self.assertEquals(event_object.mm_clips, None)

    # Test the event specific formatter.
    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
         event_object)

    # TODO: Add test for msg_short.
    self.assertEquals(msg, (
        u'Creating application: Microsoft Office Word Title: '
        'Table of Context Last saved by: Nides Author: '
        'DAVID NIDES Total edit time (secs): 0 Revision number: '
        '4 Version: 917504 Template: Normal.dotm Num pages: '
        '1 Num words: 3 Num chars: 18 Company: KPMG Security: '
        '0 Codepage: 1252'))


if __name__ == '__main__':
  unittest.main()
