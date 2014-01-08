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
"""Tests for the OLE Compound File (OLECF) parser."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import olecf as olecf_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import olecf
from plaso.parsers import test_lib


class TestOleCfParser(test_lib.ParserTestCase):
  """Tests for the OLECF parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self._parser = olecf.OleCfParser(pre_obj, None)

    # Show full diff results, part of TestCase so does not
    # follow our naming conventions.
    self.maxDiff = None

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['Document.doc'])
    events = self._ParseFile(self._parser, test_file)
    event_containers = self._GetEventContainers(events)

    self.assertEquals(len(event_containers), 5)

    # Check the Root Entry event.
    event_container = event_containers[0]

    self.assertEquals(len(event_container.events), 1)
    self.assertEquals(event_container.name, u'Root Entry')

    event_object = event_container.events[0]

    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.MODIFICATION_TIME)
    # May 16, 2013 02:29:49.795000000 UTC.
    self.assertEquals(event_object.timestamp, 1368671389795000)

    expected_string = (
        u'Name: Root Entry')

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    # Check the Summary Information.
    event_container = event_containers[1]

    self.assertEquals(len(event_container.events), 2)
    self.assertEquals(event_container.name, u'Summary Information')

    self.assertEquals(event_container.title, u'Table of Context')
    self.assertEquals(event_container.author, u'DAVID NIDES')
    self.assertEquals(event_container.template, u'Normal.dotm')
    self.assertEquals(event_container.last_saved_by, u'Nides')
    self.assertEquals(event_container.revision_number, u'4')
    self.assertEquals(event_container.number_of_characters, 18)
    self.assertEquals(event_container.application, u'Microsoft Office Word')
    self.assertEquals(event_container.security, 0)

    event_object = event_container.events[0]

    self.assertEquals(event_object.timestamp_desc, u'Document Creation Time')
    # Date: 2012-12-10T18:38:00.000000+00:00.
    self.assertEquals(event_object.timestamp, 1355164680000000)

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

    # Check the Document Summary Information.
    event_container = event_containers[2]

    self.assertEquals(len(event_container.events), 1)
    self.assertEquals(event_container.name, u'Document Summary Information')

    self.assertEquals(event_container.number_of_lines, 1)
    self.assertEquals(event_container.number_of_paragraphs, 1)
    self.assertEquals(event_container.company, u'KPMG')
    self.assertFalse(event_container.shared_document)
    self.assertEquals(event_container.application_version, u'14.0')

    # TODO: add support for:
    # self.assertEquals(event_container.is_shared, False)

    event_object = event_container.events[0]

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
