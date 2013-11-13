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
"""Tests for the Opera browser history parsers."""
import os
import unittest

# pylint: disable-msg=W0611
from plaso.formatters import opera as opera_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers import opera


class OperaTypedParserTest(unittest.TestCase):
  """Tests for the Opera Typed History Parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self._parser = opera.OperaTypedHistoryParser(pre_obj)

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testParseFile(self):
    """Read a history file and run a few tests."""
    test_file = os.path.join('test_data', 'typed_history.xml')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self._parser.Parse(file_object))

    self.assertEquals(len(events), 4)

    # Pick two events for additional tests.
    event_one = events[0]
    event_two = events[3]

    # Timestamp is: 2013-11-11T23:45:27Z.
    # date -u -d "2013-11-11T23:45:27Z" +"%s"
    self.assertEquals(event_one.timestamp, 1384213527000000)
    # Timestamp is: 2013-11-11T22:46:07Z.
    # date -u -d "2013-11-11T22:46:07Z" +"%s"
    self.assertEquals(event_two.timestamp, 1384209967000000)

    self.assertEquals(event_one.entry_selection, 'Filled from autocomplete.')
    self.assertEquals(event_two.entry_selection, 'Manually typed.')

    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
        event_one)

    expected_string = u'plaso.kiddaland.net (Filled from autocomplete.)'
    self.assertEquals(msg, expected_string)
    self.assertEquals(msg_short, expected_string)

    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
        event_two)
    expected_string = u'theonion.com (Manually typed.)'
    self.assertEquals(msg, expected_string)
    self.assertEquals(msg_short, expected_string)


class OperaGlobalParserTest(unittest.TestCase):
  """Tests for the Opera Global History parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    self._parser = opera.OperaGlobalHistoryParser(pre_obj)

    # Show full diff results, part of TestCase so does not follow our naming
    # conventions.
    self.maxDiff = None

  def testParseFile(self):
    """Read a history file and run a few tests."""
    test_file = os.path.join('test_data', 'global_history.dat')

    events = None
    with open(test_file, 'rb') as file_object:
      events = list(self._parser.Parse(file_object))

    self.assertEquals(len(events), 37)

    # Pick three "randomly" selected events from the pool.
    event_one = events[4]
    event_two = events[10]
    event_three = events[16]

    # date -u -d @1384209946
    # Mon Nov 11 22:45:46 UTC 2013
    self.assertEquals(event_one.timestamp, 1384209946 * 1000000)

    msg, msg_short = eventdata.EventFormatterManager.GetMessageStrings(
        event_one)
    expected_string = (
        u'http://www.mbl.is/frettir/erlent/2013/11/11/'
        u'karl_bretaprins_faer_ellilifeyri/ (Karl Bretaprins fær ellilífeyri'
        u' - mbl.is) [First and Only Visit]')

    expected_short_string = (
        u'http://www.mbl.is/frettir/erlent/2013/11/11/'
        u'karl_bretaprins_faer_ellilifeyri/...')

    self.assertEquals(msg, expected_string)
    self.assertEquals(msg_short, expected_short_string)

    self.assertEquals(event_two.timestamp, 1384209955 * 1000000)
    self.assertEquals(event_three.timestamp, 1384209976 * 1000000)

    self.assertEquals(event_three.title, (
        u'10 Celebrities You Never Knew Were Abducted And Murdered '
        u'By Andie MacDowell | The Onion - America\'s Finest News Source'))


if __name__ == '__main__':
  unittest.main()
