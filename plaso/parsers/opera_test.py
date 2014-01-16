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
"""Tests for the Opera browser history parsers."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import opera as opera_formatter
from plaso.lib import event
from plaso.parsers import opera
from plaso.parsers import test_lib


class OperaTypedParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Typed History parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = opera.OperaTypedHistoryParser(pre_obj, None)

  def testParse(self):
    """Tests the Parse function."""
    test_file = self._GetTestFilePath(['typed_history.xml'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 4)

    event_object = event_objects[0]

    # Timestamp is: 2013-11-11T23:45:27Z.
    # date -u -d "2013-11-11T23:45:27Z" +"%s"
    self.assertEquals(event_object.timestamp, 1384213527000000)
    self.assertEquals(event_object.entry_selection, 'Filled from autocomplete.')

    expected_string = u'plaso.kiddaland.net (Filled from autocomplete.)'

    self._TestGetMessageStrings(event_object, expected_string, expected_string)

    event_object = event_objects[3]

    # Timestamp is: 2013-11-11T22:46:07Z.
    # date -u -d "2013-11-11T22:46:07Z" +"%s"
    self.assertEquals(event_object.timestamp, 1384209967000000)
    self.assertEquals(event_object.entry_selection, 'Manually typed.')

    expected_string = u'theonion.com (Manually typed.)'

    self._TestGetMessageStrings(event_object, expected_string, expected_string)


class OperaGlobalParserTest(test_lib.ParserTestCase):
  """Tests for the Opera Global History parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._parser = opera.OperaGlobalHistoryParser(pre_obj, None)

  def testParseFile(self):
    """Read a history file and run a few tests."""
    test_file = self._GetTestFilePath(['global_history.dat'])
    event_generator = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjects(event_generator)

    self.assertEquals(len(event_objects), 37)

    event_object = event_objects[4]

    # date -u -d @1384209946
    # Mon Nov 11 22:45:46 UTC 2013
    self.assertEquals(event_object.timestamp, 1384209946 * 1000000)

    expected_msg = (
        u'http://www.mbl.is/frettir/erlent/2013/11/11/'
        u'karl_bretaprins_faer_ellilifeyri/ (Karl Bretaprins fær ellilífeyri'
        u' - mbl.is) [First and Only Visit]')
    expected_msg_short = (
        u'http://www.mbl.is/frettir/erlent/2013/11/11/'
        u'karl_bretaprins_faer_ellilifeyri/...')

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = event_objects[10]

    # date -u -d @1384209955
    # Mon Nov 11 22:45:55 UTC 2013
    self.assertEquals(event_object.timestamp, 1384209955 * 1000000)

    event_object = event_objects[16]

    # date -u -d @1384209976
    # Mon Nov 11 22:46:16 UTC 2013
    self.assertEquals(event_object.timestamp, 1384209976 * 1000000)

    expected_title = (
        u'10 Celebrities You Never Knew Were Abducted And Murdered '
        u'By Andie MacDowell | The Onion - America\'s Finest News Source')

    self.assertEquals(event_object.title, expected_title)


if __name__ == '__main__':
  unittest.main()
