#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the filters."""

import unittest

from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import event
from plaso.lib import objectfilter
from plaso.lib import pfilter
from plaso.lib import timelib_test

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


formatters_manager.FormattersManager.RegisterFormatter(PfilterFakeFormatter)


class PFilterTest(unittest.TestCase):
  """Simple plaso specific tests to the pfilter implementation."""

  def _RunPlasoTest(self, event_object, query, result):
    """Run a simple test against an event object."""
    my_parser = pfilter.BaseParser(query).Parse()
    matcher = my_parser.Compile(
        pfilter.PlasoAttributeFilterImplementation)

    self.assertEqual(result, matcher.Matches(event_object))

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
    self._RunPlasoTest(event_object, query, True)

    # Double negative matching -> should be the same
    # as a positive one.
    query = 'filename not not contains \'GoodFella\''
    my_parser = pfilter.BaseParser(query)
    self.assertRaises(
        objectfilter.ParseError,
        my_parser.Parse)

    # Test date filtering.
    query = 'date >= \'2015-11-18\''
    self._RunPlasoTest(event_object, query, True)

    query = 'date < \'2015-11-19\''
    self._RunPlasoTest(event_object, query, True)

    # 2015-11-18T01:15:43
    query = (
        'date < \'2015-11-18T01:15:44.341\' and date > \'2015-11-18 01:15:42\'')
    self._RunPlasoTest(event_object, query, True)

    query = 'date > \'2015-11-19\''
    self._RunPlasoTest(event_object, query, False)

    # Perform few attribute tests.
    query = 'filename not contains \'sometext\''
    self._RunPlasoTest(event_object, query, True)

    query = (
        'timestamp_desc CONTAINS \'written\' AND date > \'2015-11-18\' AND '
        'date < \'2015-11-25 12:56:21\' AND (source_short contains \'LOG\' or '
        'source_short CONTAINS \'REG\')')
    self._RunPlasoTest(event_object, query, True)

    query = 'parser is not \'Made\''
    self._RunPlasoTest(event_object, query, True)

    query = 'parser is not \'Weirdo\''
    self._RunPlasoTest(event_object, query, False)

    query = 'mydict.value is 123'
    self._RunPlasoTest(event_object, query, False)

    query = 'mydict.akeywithstuff contains "ere"'
    self._RunPlasoTest(event_object, query, True)

    query = 'mydict.value is 134'
    self._RunPlasoTest(event_object, query, True)

    query = 'mydict.value < 200'
    self._RunPlasoTest(event_object, query, True)

    query = 'mydict.another contains "val"'
    self._RunPlasoTest(event_object, query, True)

    query = 'mydict.notthere is 123'
    self._RunPlasoTest(event_object, query, False)

    query = 'source_long not contains \'Fake\''
    self._RunPlasoTest(event_object, query, False)

    query = 'source is \'REG\''
    self._RunPlasoTest(event_object, query, True)

    query = 'source is not \'FILE\''
    self._RunPlasoTest(event_object, query, True)

    # Multiple attributes.
    query = (
        'source_long is \'Fake Parsing Source\' AND description_long '
        'regexp \'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self._RunPlasoTest(event_object, query, False)

    query = (
        'source_long is \'Fake Parsing Source\' AND text iregexp '
        '\'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self._RunPlasoTest(event_object, query, True)


if __name__ == "__main__":
  unittest.main()
