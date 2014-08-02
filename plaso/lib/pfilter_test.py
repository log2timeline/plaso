#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the filters."""

import unittest

from plaso.formatters import interface as formatters_interface
from plaso.lib import event
from plaso.lib import objectfilter
from plaso.lib import pfilter
from plaso.lib import timelib_test
from plaso.parsers import interface as parsers_interface

import pytz


class Empty(object):
  """An empty object."""


class PfilterFakeFormatter(formatters_interface.EventFormatter):
  """A formatter for this fake class."""
  DATA_TYPE = 'Weirdo:Made up Source:Last Written'

  FORMAT_STRING = '{text}'
  FORMAT_STRING_SHORT = '{text_short}'

  SOURCE_LONG = 'Fake Parsing Source'
  SOURCE_SHORT = 'REG'


class PfilterFakeParser(parsers_interface.BaseParser):
  """A fake parser that does not parse anything, but registers."""

  NAME = 'pfilter_fake_parser'

  DATA_TYPE = 'Weirdo:Made up Source:Last Written'

  def Parse(self, unused_file_entry):
    """Extract data from a fake plist file for testing.

    Args:
      unused_file_entry: A file entry object that is not used by
                         the fake parser.

    Yields:
      An event object (instance of EventObject) that contains the parsed
      attributes.
    """
    event_object = event.EventObject()
    event_object.timestamp = timelib_test.CopyStringToTimestamp(
        '2015-11-18 01:15:43')
    event_object.timestamp_desc = 'Last Written'
    event_object.text_short = 'This description is different than the long one.'
    event_object.text = (
        u'User did a very bad thing, bad, bad thing that awoke Dr. Evil.')
    event_object.filename = (
        u'/My Documents/goodfella/Documents/Hideout/myfile.txt')
    event_object.hostname = 'Agrabah'
    event_object.parser = 'Weirdo'
    event_object.inode = 1245
    event_object.display_name = u'unknown:{0:s}'.format(event_object.filename)
    event_object.data_type = self.DATA_TYPE

    yield event_object


class PfilterAnotherParser(PfilterFakeParser):
  """Another fake parser that does nothing but register as a parser."""

  NAME = 'pfilter_another_fake'

  DATA_TYPE = 'Weirdo:AnotherFakeSource'


class PfilterAnotherFakeFormatter(PfilterFakeFormatter):
  """Formatter for the AnotherParser event."""

  DATA_TYPE = 'Weirdo:AnotherFakeSource'
  SOURCE_LONG = 'Another Fake Source'


class PfilterAllEvilParser(PfilterFakeParser):
  """A class that does nothing but has a fancy name."""

  NAME = 'pfilter_evil_fake_parser'

  DATA_TYPE = 'Weirdo:AllEvil'


class PfilterEvilFormatter(PfilterFakeFormatter):
  """Formatter for the AllEvilParser."""

  DATA_TYPE = 'Weirdo:AllEvil'
  SOURCE_LONG = 'A Truly Evil'


class PFilterTest(unittest.TestCase):
  """Simple plaso specific tests to the pfilter implementation."""

  def setUp(self):
    """Set up the necessary variables used in tests."""
    self._pre = Empty()
    self._pre.zone = pytz.UTC

  def testPlasoEvents(self):
    """Test plaso EventObjects, both Python and Protobuf version.

    These are more plaso specific tests than the more generic
    objectfilter ones. It will create an EventObject that stores
    some attributes. These objects will then be serialzed into an
    EventObject protobuf and all tests run against both the native
    Python object as well as the protobuf.
    """
    event_object = event.EventObject()
    event_object.data_type = 'Weirdo:Made up Source:Last Written'
    event_object.timestamp = timelib_test.CopyStringToTimestamp(
        '2015-11-18 01:15:43')
    event_object.timestamp_desc = 'Last Written'
    event_object.text_short = 'This description is different than the long one.'
    event_object.text = (
        u'User did a very bad thing, bad, bad thing that awoke Dr. Evil.')
    event_object.filename = (
        u'/My Documents/goodfella/Documents/Hideout/myfile.txt')
    event_object.hostname = 'Agrabah'
    event_object.parser = 'Weirdo'
    event_object.inode = 1245
    event_object.mydict = {
        'value': 134, 'another': 'value', 'A Key (with stuff)': 'Here'}
    event_object.display_name = u'unknown:{0:s}'.format(event_object.filename)

    # Series of tests.
    query = 'filename contains \'GoodFella\''
    self.RunPlasoTest(event_object, query, True)

    # Double negative matching -> should be the same
    # as a positive one.
    query = 'filename not not contains \'GoodFella\''
    my_parser = pfilter.BaseParser(query)
    self.assertRaises(
        objectfilter.ParseError,
        my_parser.Parse)

    # Test date filtering.
    query = 'date >= \'2015-11-18\''
    self.RunPlasoTest(event_object, query, True)

    query = 'date < \'2015-11-19\''
    self.RunPlasoTest(event_object, query, True)

    # 2015-11-18T01:15:43
    query = (
        'date < \'2015-11-18T01:15:44.341\' and date > \'2015-11-18 01:15:42\'')
    self.RunPlasoTest(event_object, query, True)

    query = 'date > \'2015-11-19\''
    self.RunPlasoTest(event_object, query, False)

    # Perform few attribute tests.
    query = 'filename not contains \'sometext\''
    self.RunPlasoTest(event_object, query, True)

    query = (
        'timestamp_desc CONTAINS \'written\' AND date > \'2015-11-18\' AND '
        'date < \'2015-11-25 12:56:21\' AND (source_short contains \'LOG\' or '
        'source_short CONTAINS \'REG\')')
    self.RunPlasoTest(event_object, query, True)

    query = 'parser is not \'Made\''
    self.RunPlasoTest(event_object, query, True)

    query = 'parser is not \'Weirdo\''
    self.RunPlasoTest(event_object, query, False)

    query = 'mydict.value is 123'
    self.RunPlasoTest(event_object, query, False)

    query = 'mydict.akeywithstuff contains "ere"'
    self.RunPlasoTest(event_object, query, True)

    query = 'mydict.value is 134'
    self.RunPlasoTest(event_object, query, True)

    query = 'mydict.value < 200'
    self.RunPlasoTest(event_object, query, True)

    query = 'mydict.another contains "val"'
    self.RunPlasoTest(event_object, query, True)

    query = 'mydict.notthere is 123'
    self.RunPlasoTest(event_object, query, False)

    query = 'source_long not contains \'Fake\''
    self.RunPlasoTest(event_object, query, False)

    query = 'source is \'REG\''
    self.RunPlasoTest(event_object, query, True)

    query = 'source is not \'FILE\''
    self.RunPlasoTest(event_object, query, True)

    # Multiple attributes.
    query = (
        'source_long is \'Fake Parsing Source\' AND description_long '
        'regexp \'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self.RunPlasoTest(event_object, query, False)

    query = (
        'source_long is \'Fake Parsing Source\' AND text iregexp '
        '\'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self.RunPlasoTest(event_object, query, True)

  def RunPlasoTest(self, obj, query, result):
    """Run a simple test against an event object."""
    my_parser = pfilter.BaseParser(query).Parse()
    matcher = my_parser.Compile(
        pfilter.PlasoAttributeFilterImplementation)

    self.assertEqual(result, matcher.Matches(obj))


if __name__ == "__main__":
  unittest.main()
