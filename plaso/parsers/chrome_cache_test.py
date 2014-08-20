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
"""Tests for the Chrome Cache files parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import chrome_cache as chrome_cache_formatter
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import test_lib
from plaso.parsers import chrome_cache


class WinEvtParserTest(test_lib.ParserTestCase):
  """Tests for the Chrome Cache files parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = chrome_cache.ChromeCacheParser(pre_obj)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['chrome_cache', 'index'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 217)

    event_object = event_objects[0]

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2014-04-30 16:44:36.226091')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_original_url = (
        u'https://s.ytimg.com/yts/imgbin/player-common-vfliLfqPT.webp')
    self.assertEqual(event_object.original_url, expected_original_url)

    expected_string = u'Original URL: {0:s}'.format(expected_original_url)

    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
