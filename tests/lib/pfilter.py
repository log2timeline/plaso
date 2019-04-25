#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the filters."""

from __future__ import unicode_literals

import unittest

from plaso.containers import events
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import pfilter
from plaso.lib import timelib


class PfilterFakeFormatter(formatters_interface.EventFormatter):
  """A formatter for this fake class."""
  DATA_TYPE = 'Weirdo:Made up Source:Last Written'

  FORMAT_STRING = '{text}'
  FORMAT_STRING_SHORT = '{text_short}'

  SOURCE_LONG = 'Fake Parsing Source'
  SOURCE_SHORT = 'REG'


formatters_manager.FormattersManager.RegisterFormatter(PfilterFakeFormatter)


class PFilterTest(unittest.TestCase):
  """Simple plaso specific tests to the pfilter implementation."""

  def _RunPlasoTest(self, event, query, result):
    """Run a simple test against an event object."""
    my_parser = pfilter.BaseParser(query).Parse()
    matcher = my_parser.Compile(
        pfilter.PlasoAttributeFilterImplementation)

    self.assertEqual(
        result, matcher.Matches(event),
        'query {0:s} failed with event {1!s}'.format(query, event.CopyToDict()))

  def testPlasoEvents(self):
    """Test plaso EventObjects, both Python and Protobuf version.

    These are more plaso specific tests than the more generic object filter
    ones. It will create an event object that stores some attributes. These
    objects will then be serialized and all tests run against both the Python
    objects as well as the serialized ones.
    """
    event = events.EventObject()
    event.data_type = 'Weirdo:Made up Source:Last Written'
    event.timestamp = timelib.Timestamp.CopyFromString(
        '2015-11-18 01:15:43')
    event.timestamp_desc = 'Last Written'
    event.text_short = (
        'This description is different than the long one.')
    event.text = (
        'User did a very bad thing, bad, bad thing that awoke Dr. Evil.')
    event.filename = (
        '/My Documents/goodfella/Documents/Hideout/myfile.txt')
    event.hostname = 'Agrabah'
    event.parser = 'Weirdo'
    event.inode = 1245
    event.mydict = {
        'value': 134, 'another': 'value', 'A Key (with stuff)': 'Here'}
    event.display_name = 'unknown:{0:s}'.format(event.filename)

    event.tag = events.EventTag(comment='comment')
    event.tag.AddLabel('browser_search')

    # Series of tests.
    query = 'filename contains \'GoodFella\''
    self._RunPlasoTest(event, query, True)

    # Double negative matching -> should be the same
    # as a positive one.
    query = 'filename not not contains \'GoodFella\''
    my_parser = pfilter.BaseParser(query)
    self.assertRaises(errors.ParseError, my_parser.Parse)

    # Test date filtering.
    query = 'date >= \'2015-11-18\''
    self._RunPlasoTest(event, query, True)

    query = 'date < \'2015-11-19\''
    self._RunPlasoTest(event, query, True)

    # 2015-11-18T01:15:43
    query = (
        'date < \'2015-11-18T01:15:44.341\' and '
        'date > \'2015-11-18 01:15:42\'')
    self._RunPlasoTest(event, query, True)

    query = 'date > \'2015-11-19\''
    self._RunPlasoTest(event, query, False)

    # Perform few attribute tests.
    query = 'filename not contains \'sometext\''
    self._RunPlasoTest(event, query, True)

    query = (
        'timestamp_desc CONTAINS \'written\' AND date > \'2015-11-18\' AND '
        'date < \'2015-11-25 12:56:21\' AND (source_short contains \'LOG\' or '
        'source_short CONTAINS \'REG\')')
    self._RunPlasoTest(event, query, True)

    query = 'parser is not \'Made\''
    self._RunPlasoTest(event, query, True)

    query = 'parser is not \'Weirdo\''
    self._RunPlasoTest(event, query, False)

    query = 'mydict.value is 123'
    self._RunPlasoTest(event, query, False)

    query = 'mydict.akeywithstuff contains "ere"'
    self._RunPlasoTest(event, query, True)

    query = 'mydict.value is 134'
    self._RunPlasoTest(event, query, True)

    query = 'mydict.value < 200'
    self._RunPlasoTest(event, query, True)

    query = 'mydict.another contains "val"'
    self._RunPlasoTest(event, query, True)

    query = 'mydict.notthere is 123'
    self._RunPlasoTest(event, query, False)

    query = 'source_long not contains \'Fake\''
    self._RunPlasoTest(event, query, False)

    query = 'source is \'REG\''
    self._RunPlasoTest(event, query, True)

    query = 'source is not \'FILE\''
    self._RunPlasoTest(event, query, True)

    query = 'tag contains \'browser_search\''
    self._RunPlasoTest(event, query, True)

    # Multiple attributes.
    query = (
        'source_long is \'Fake Parsing Source\' AND description_long '
        'regexp \'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self._RunPlasoTest(event, query, False)

    query = (
        'source_long is \'Fake Parsing Source\' AND text iregexp '
        '\'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self._RunPlasoTest(event, query, True)


if __name__ == "__main__":
  unittest.main()
