#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Tests for the xchatlog parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import xchatlog as xchatlog_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers import xchatlog
from plaso.parsers import test_lib

__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class XChatLogUnitTest(test_lib.ParserTestCase):
  """Tests for the xchatlog parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    pre_obj.SetTimezone('Europe/Rome')
    self._parser = xchatlog.XChatLogParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['xchat.log'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 9)

    # expr `date -u -d "2011-12-31 21:11:55+01:00" +"%s%N"` \/ 1000
    self.assertEquals(event_objects[0].timestamp, 1325362315000000)
    # expr `date -u -d "2011-12-31 23:00:00+01:00" +"%s%N"` \/ 1000
    self.assertEquals(event_objects[7].timestamp, 1325368800000000)
    # expr `date -u -d  "2011-12-31 23:59:00+01:00" +"%s%N"` \/ 1000
    self.assertEquals(event_objects[8].timestamp, 1325372340000000)

    expected_string = u'XChat start logging'
    self._TestGetMessageStrings(
        event_objects[0], expected_string, expected_string)

    expected_string = u'--> You are now talking on #gugle'
    self._TestGetMessageStrings(
        event_objects[1], expected_string, expected_string)

    expected_string = u'--- Topic for #gugle is plaso, a difficult word'
    self._TestGetMessageStrings(
        event_objects[2], expected_string, expected_string)

    expected_string = u'Topic for #gugle set by Kristinn'
    self._TestGetMessageStrings(
        event_objects[3], expected_string, expected_string)

    expected_string = u'--- Joachim gives voice to fpi'
    self._TestGetMessageStrings(
        event_objects[4], expected_string, expected_string)

    expected_string = u'* XChat here'
    self._TestGetMessageStrings(
        event_objects[5], expected_string, expected_string)

    expected_string = u'[nickname: fpi] ola plas-ing guys!'
    self._TestGetMessageStrings(
        event_objects[6], expected_string, expected_string)

    expected_string = u'[nickname: STRANGER] \u65e5\u672c'
    self._TestGetMessageStrings(
        event_objects[7], expected_string, expected_string)

    expected_string = u'XChat end logging'
    self._TestGetMessageStrings(
        event_objects[8], expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
