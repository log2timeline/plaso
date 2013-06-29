#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""Tests for plaso.lib.pfilter."""
import unittest
import pytz
import re

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import objectfilter
from plaso.lib import parser
from plaso.lib import pfilter
from plaso.lib import putils
from plaso.lib import storage
from plaso.lib import utils

__pychecker__ = 'no-funcdoc'


class Empty(object):
  """An empty object."""


class PfilterFakeFormatter(eventdata.EventFormatter):
  """A formatter for this fake class."""
  DATA_TYPE = 'Weirdo:Made up Source:Last Written'

  FORMAT_STRING = '{text}'
  FORMAT_STRING_SHORT = '{text_short}'

  SOURCE_LONG = 'Fake Parsing Source'
  SOURCE_SHORT = 'REG'


class PfilterFakeParser(parser.PlasoParser):
  """A fake parser that does not parse anything, but registers."""

  DATA_TYPE = 'Weirdo:Made up Source:Last Written'

  def Parse(self, unused_filehandle):
    """A parse method yields a single event."""
    evt = event.EventObject()
    # 2015-11-18T01:15:43
    evt.timestamp = 1447809343000000
    evt.timestamp_desc = 'Last Written'
    evt.text_short = 'This description is different than the long one.'
    evt.text = (
        u'User did a very bad thing, bad, bad thing that awoke Dr. Evil.')
    evt.filename = '/My Documents/goodfella/Documents/Hideout/myfile.txt'
    evt.hostname = 'Agrabah'
    evt.parser = 'Weirdo'
    evt.inode = '1245'
    evt.display_name = u'unknown:%s' % evt.filename
    evt.data_type = self.DATA_TYPE

    yield evt


class PfilterAnotherParser(PfilterFakeParser):
  """Another fake parser that does nothing but register as a parser."""

  DATA_TYPE = 'Weirdo:AnotherFakeSource'


class PfilterAnotherFakeFormatter(PfilterFakeFormatter):
  """Formatter for the AnotherParser event."""

  DATA_TYPE = 'Weirdo:AnotherFakeSource'
  SOURCE_LONG = 'Another Fake Source'


class PfilterAllEvilParser(PfilterFakeParser):
  """A class that does nothing but has a fancy name."""

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
    objectfilter ones. It will create an EventContainer that stores
    some attributes and then an EventObject that is stored inside
    that container. These objects will then be serialzed into an
    EventObject protobuf and all tests run against both the native
    Python object as well as the protobuf.
    """
    container = event.EventContainer()
    container.data_type = 'Weirdo:Made up Source:Last Written'

    evt = event.EventObject()
    # 2015-11-18T01:15:43
    evt.timestamp = 1447809343000000
    evt.timestamp_desc = 'Last Written'
    evt.text_short = 'This description is different than the long one.'
    evt.text = (
        u'User did a very bad thing, bad, bad thing that awoke Dr. Evil.')
    evt.filename = '/My Documents/goodfella/Documents/Hideout/myfile.txt'
    evt.hostname = 'Agrabah'
    evt.parser = 'Weirdo'
    evt.inode = '1245'
    evt.mydict = {'value': 134, 'another': 'value',
                  'A Key (with stuff)': 'Here'}
    evt.display_name = u'unknown:%s' % evt.filename

    container.Append(evt)

    # Series of tests.
    query = 'filename contains \'GoodFella\''
    self.RunPlasoTest(evt, query, True)

    # Double negative matching -> should be the same
    # as a positive one.
    query = 'filename not not contains \'GoodFella\''
    parser = pfilter.PlasoParser(query)
    self.assertRaises(
        objectfilter.ParseError,
        parser.Parse)

    # Test date filtering.
    query = 'date >= \'2015-11-18\''
    self.RunPlasoTest(evt, query, True)

    query = 'date < \'2015-11-19\''
    self.RunPlasoTest(evt, query, True)

    # 2015-11-18T01:15:43
    query = ('date < \'2015-11-18T01:15:44.341\' and '
             'date > \'2015-11-18 01:15:42\'')
    self.RunPlasoTest(evt, query, True)

    query = 'date > \'2015-11-19\''
    self.RunPlasoTest(evt, query, False)

    # Perform few attribute tests.
    query = 'filename not contains \'sometext\''
    self.RunPlasoTest(evt, query, True)

    query = ('timestamp_desc CONTAINS \'written\' AND date > \'2015-11-18\' '
             'AND date < \'2015-11-25 12:56:21\' AND (source_short contains '
             '\'LOG\' or source_short CONTAINS \'REG\')')
    self.RunPlasoTest(evt, query, True)

    query = 'parser is not \'Made\''
    self.RunPlasoTest(evt, query, True)

    query = 'parser is not \'Weirdo\''
    self.RunPlasoTest(evt, query, False)

    query = 'mydict.value is 123'
    self.RunPlasoTest(evt, query, False)

    query = 'mydict.akeywithstuff contains "ere"'
    self.RunPlasoTest(evt, query, True)

    query = 'mydict.value is 134'
    self.RunPlasoTest(evt, query, True)

    query = 'mydict.value < 200'
    self.RunPlasoTest(evt, query, True)

    query = 'mydict.another contains "val"'
    self.RunPlasoTest(evt, query, True)

    query = 'mydict.notthere is 123'
    self.RunPlasoTest(evt, query, False)

    # Test atttributes stored in the container.
    query = 'source_long not contains \'Fake\''
    self.RunPlasoTest(evt, query, False)

    query = 'source is \'REG\''
    self.RunPlasoTest(evt, query, True)

    query = 'source is not \'FILE\''
    self.RunPlasoTest(evt, query, True)

    # Multiple attributes.
    query = ('source_long is \'Fake Parsing Source\' AND description_long '
             'regexp \'bad, bad thing [\sa-zA-Z\.]+ evil\'')
    self.RunPlasoTest(evt, query, False)

    query = ('source_long is \'Fake Parsing Source\' AND text iregexp '
             '\'bad, bad thing [\sa-zA-Z\.]+ evil\'')
    self.RunPlasoTest(evt, query, True)

  def RunPlasoTest(self, obj, query, result):
    """Run a simple test against an event object."""
    parser = pfilter.PlasoParser(query).Parse()
    matcher = parser.Compile(
        pfilter.PlasoAttributeFilterImplementation)

    self.assertEqual(result, matcher.Matches(obj))

  def testParserFilter(self):
    query = (
        'source is "REG" AND message CONTAINS "is" and parser contains '
        '"Pfilter"')
    parsers = putils.FindAllParsers(self._pre, query)['all']

    self.assertEquals(len(parsers), 3)

    query = (
        'source is "REG" and parser is not "PfilterFakeParser" and parser '
        'contains "Pfilter"')
    parsers = putils.FindAllParsers(self._pre, query)['all']
    self.assertEquals(len(parsers), 2)

    query = 'parser contains "fake" and date > 0'
    parsers = putils.FindAllParsers(self._pre, query)['all']
    self.assertEquals(len(parsers), 1)

    query = ('date > 0 AND message regexp "\sW\sW" AND parser '
             'is not "PfilterFakeParser" and parser contains "PFilter"')
    parsers = putils.FindAllParsers(self._pre, query)['all']
    self.assertEquals(len(parsers), 2)

    query = ('(parser contains "pfilter" or date < "2015-06-12") AND '
             'message CONTAINS "weird"')
    parsers = putils.FindAllParsers(self._pre, query)['all']

    query = ('parser contains "pfilter" and (parser contains "pfilter" or '
             'date < "2015-06-12") AND '
             'metadata.author CONTAINS "weird"')
    parsers = putils.FindAllParsers(self._pre, query)['all']
    self.assertEquals(len(parsers), 3)


if __name__ == "__main__":
  unittest.main()
