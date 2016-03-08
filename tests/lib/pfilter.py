#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the filters."""

import unittest

from plaso.containers import events
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import pfilter
from plaso.lib import timelib

import pytz


class Empty(object):
  """An empty object."""


class PfilterFakeFormatter(formatters_interface.EventFormatter):
  """A formatter for this fake class."""
  DATA_TYPE = 'Weirdo:Made up Source:Last Written'

  FORMAT_STRING = u'{text}'
  FORMAT_STRING_SHORT = u'{text_short}'

  SOURCE_LONG = u'Fake Parsing Source'
  SOURCE_SHORT = u'REG'


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
    """Makes preparations before running an individual test."""
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
    event_object = events.EventObject()
    event_object.data_type = 'Weirdo:Made up Source:Last Written'
    event_object.timestamp = timelib.Timestamp.CopyFromString(
        u'2015-11-18 01:15:43')
    event_object.timestamp_desc = u'Last Written'
    event_object.text_short = (
        u'This description is different than the long one.')
    event_object.text = (
        u'User did a very bad thing, bad, bad thing that awoke Dr. Evil.')
    event_object.filename = (
        u'/My Documents/goodfella/Documents/Hideout/myfile.txt')
    event_object.hostname = u'Agrabah'
    event_object.parser = u'Weirdo'
    event_object.inode = 1245
    event_object.mydict = {
        u'value': 134, u'another': u'value', u'A Key (with stuff)': u'Here'}
    event_object.display_name = u'unknown:{0:s}'.format(event_object.filename)

    # Series of tests.
    query = u'filename contains \'GoodFella\''
    self._RunPlasoTest(event_object, query, True)

    # Double negative matching -> should be the same
    # as a positive one.
    query = u'filename not not contains \'GoodFella\''
    my_parser = pfilter.BaseParser(query)
    self.assertRaises(errors.ParseError, my_parser.Parse)

    # Test date filtering.
    query = u'date >= \'2015-11-18\''
    self._RunPlasoTest(event_object, query, True)

    query = u'date < \'2015-11-19\''
    self._RunPlasoTest(event_object, query, True)

    # 2015-11-18T01:15:43
    query = (
        u'date < \'2015-11-18T01:15:44.341\' and '
        u'date > \'2015-11-18 01:15:42\'')
    self._RunPlasoTest(event_object, query, True)

    query = u'date > \'2015-11-19\''
    self._RunPlasoTest(event_object, query, False)

    # Perform few attribute tests.
    query = u'filename not contains \'sometext\''
    self._RunPlasoTest(event_object, query, True)

    query = (
        u'timestamp_desc CONTAINS \'written\' AND date > \'2015-11-18\' AND '
        u'date < \'2015-11-25 12:56:21\' AND (source_short contains \'LOG\' or '
        u'source_short CONTAINS \'REG\')')
    self._RunPlasoTest(event_object, query, True)

    query = u'parser is not \'Made\''
    self._RunPlasoTest(event_object, query, True)

    query = u'parser is not \'Weirdo\''
    self._RunPlasoTest(event_object, query, False)

    query = u'mydict.value is 123'
    self._RunPlasoTest(event_object, query, False)

    query = u'mydict.akeywithstuff contains "ere"'
    self._RunPlasoTest(event_object, query, True)

    query = u'mydict.value is 134'
    self._RunPlasoTest(event_object, query, True)

    query = u'mydict.value < 200'
    self._RunPlasoTest(event_object, query, True)

    query = u'mydict.another contains "val"'
    self._RunPlasoTest(event_object, query, True)

    query = u'mydict.notthere is 123'
    self._RunPlasoTest(event_object, query, False)

    query = u'source_long not contains \'Fake\''
    self._RunPlasoTest(event_object, query, False)

    query = u'source is \'REG\''
    self._RunPlasoTest(event_object, query, True)

    query = u'source is not \'FILE\''
    self._RunPlasoTest(event_object, query, True)

    # Multiple attributes.
    query = (
        u'source_long is \'Fake Parsing Source\' AND description_long '
        u'regexp \'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self._RunPlasoTest(event_object, query, False)

    query = (
        u'source_long is \'Fake Parsing Source\' AND text iregexp '
        u'\'bad, bad thing [\\sa-zA-Z\\.]+ evil\'')
    self._RunPlasoTest(event_object, query, True)


if __name__ == "__main__":
  unittest.main()
