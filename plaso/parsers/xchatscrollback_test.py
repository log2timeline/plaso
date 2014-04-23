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
"""Tests for the xchatscrollback log parser."""

import pytz
import unittest

# pylint: disable=unused-import
from plaso.formatters import xchatscrollback as xchatscrollback_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers import xchatscrollback as xchatscrollback_parser
from plaso.parsers import test_lib


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class XChatScrollbackUnitTest(test_lib.ParserTestCase):
  """Tests for the xchatscrollback log parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    pre_obj.zone = pytz.timezone('UTC')
    self._parser = xchatscrollback_parser.XChatScrollbackParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['xchatscrollback.log'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 10)

    self.assertEquals(event_objects[0].timestamp, 1232074579000000)
    self.assertEquals(event_objects[1].timestamp, 1232074587000000)
    self.assertEquals(event_objects[2].timestamp, 1232315916000000)
    self.assertEquals(event_objects[3].timestamp, 1232315916000000)
    self.assertEquals(event_objects[4].timestamp, 1232959856000000)
    self.assertEquals(event_objects[5].timestamp, 0)
    self.assertEquals(event_objects[7].timestamp, 1232959862000000)
    self.assertEquals(event_objects[8].timestamp, 1232959932000000)
    self.assertEquals(event_objects[9].timestamp, 1232959993000000)

    expected_string = u'[] * Speaking now on ##plaso##'
    self._TestGetMessageStrings(
        event_objects[0], expected_string, expected_string)

    expected_string = u'[] * Joachim \xe8 uscito (Client exited)'
    self._TestGetMessageStrings(
        event_objects[1], expected_string, expected_string)

    expected_string = u'[] Tcl interface unloaded'
    self._TestGetMessageStrings(
        event_objects[2], expected_string, expected_string)

    expected_string = u'[] Python interface unloaded'
    self._TestGetMessageStrings(
        event_objects[3], expected_string, expected_string)

    expected_string = u'[] * Topic of #plasify \xe8: .'
    self._TestGetMessageStrings(
        event_objects[6], expected_string, expected_string)

    expected_string = u'[nickname: fpi] Hi Kristinn!'
    self._TestGetMessageStrings(
        event_objects[8], expected_string, expected_string)

    expected_string = u'[nickname: Kristinn] GO AND WRITE PARSERS!!! O_o'
    self._TestGetMessageStrings(
        event_objects[9], expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
