#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the serializer object implementation using json."""

import json
import unittest

from plaso.lib import event
from plaso.serializer import json_serializer
from plaso.storage import collection

# TODO: add tests for the non implemented serializer objects when implemented.


class JsonEventObjectSerializerTest(unittest.TestCase):
  """Tests for the json event object serializer object."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    # Do not use u'' or b'' we need native string objects here
    # otherwise the strings will be formatted with a prefix and
    # are not a valid JSON string.
    self._json_dict = {
        '__type__': 'EventObject',
        'a_tuple': [
            'some item', [234, 52, 15], {'a': 'not a', 'b': 'not b'}, 35],
        'data_type': 'test:event2',
        'empty_string': '',
        'integer': 34,
        'my_dict': {
            'a': 'not b',
            'an': [234, 32],
            'c': 34,
            'list': ['sf', 234]
        },
        'my_list': ['asf', 4234, 2, 54, 'asf'],
        'string': 'Normal string',
        'timestamp_desc': 'Written',
        'timestamp': 1234124,
        'uuid': '5a78777006de4ddb8d7bbe12ab92ccf8',
        'unicode_string': 'And I am a unicorn.',
        'zero_integer': 0
    }

  def testReadSerialized(self):
    """Test the read serialized functionality."""
    serializer = json_serializer.JsonEventObjectSerializer
    json_string = u'{0!s}'.format(self._json_dict).replace(u'\'', u'"')
    event_object = serializer.ReadSerialized(json_string)

    # An integer value containing 0 should get stored.
    self.assertTrue(hasattr(event_object, 'zero_integer'))

    attribute_value = getattr(event_object, 'integer', 0)
    self.assertEqual(attribute_value, 34)

    attribute_value = getattr(event_object, 'my_list', [])
    self.assertEqual(len(attribute_value), 5)

    attribute_value = getattr(event_object, 'string', '')
    self.assertEqual(attribute_value, 'Normal string')

    attribute_value = getattr(event_object, 'unicode_string', u'')
    self.assertEqual(attribute_value, u'And I am a unicorn.')

    attribute_value = getattr(event_object, 'a_tuple', ())
    self.assertEqual(len(attribute_value), 4)

  def testWriteSerialized(self):
    """Test the write serialized functionality."""
    event_object = event.EventObject()

    event_object.data_type = 'test:event2'
    event_object.timestamp = 1234124
    event_object.timestamp_desc = 'Written'
    # Prevent the event object for generating its own UUID.
    event_object.uuid = '5a78777006de4ddb8d7bbe12ab92ccf8'

    event_object.empty_string = u''
    event_object.zero_integer = 0
    event_object.integer = 34
    event_object.string = 'Normal string'
    event_object.unicode_string = u'And I am a unicorn.'
    event_object.my_list = ['asf', 4234, 2, 54, 'asf']
    event_object.my_dict = {
        'a': 'not b', 'c': 34, 'list': ['sf', 234], 'an': [234, 32]}
    event_object.a_tuple = (
        'some item', [234, 52, 15], {'a': 'not a', 'b': 'not b'}, 35)
    event_object.null_value = None

    json_string = json_serializer.JsonEventObjectSerializer.WriteSerialized(
        event_object)

    # We need to compare dicts since we cannot determine the order
    # of values in the string.
    json_dict = json.loads(json_string)
    self.assertEqual(json_dict, self._json_dict)

    event_object = json_serializer.JsonEventObjectSerializer.ReadSerialized(
        json_string)

    # TODO: fix this.
    # An empty string should not get stored.
    # self.assertFalse(hasattr(event_object, 'empty_string'))

    # A None (or Null) value should not get stored.
    # self.assertFalse(hasattr(event_object, 'null_value'))


class JsonCollectionInformationSerializerTest(unittest.TestCase):
  """Tests serialization of the collection information object."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def setUp(self):
    """Set up the necessary objects."""
    # Do not use u'' or b'' we need native string objects here
    # otherwise the strings will be formatted with a prefix and
    # are not a valid JSON string.
    self._json_dict = {
        '__COUNTERS__': {
            'foobar': {
                'stuff': 1245
            }
        },
        'foo': 'bar',
        'foo2': 'randombar'
    }

    self._collection_information_object = collection.CollectionInformation()
    self._collection_information_object.AddCounter(u'foobar')
    self._collection_information_object.IncrementCounter(
        u'foobar', u'stuff', value=1245)
    self._collection_information_object.SetValue(u'foo', u'bar')
    self._collection_information_object.SetValue(u'foo2', u'randombar')
    self._serializer = json_serializer.JsonCollectionInformationObjectSerializer

  def testReadSerialized(self):
    """Test the read serialized functionality."""
    json_string = u'{0!s}'.format(self._json_dict).replace(u'\'', u'"')
    collection_object = self._serializer.ReadSerialized(json_string)

    for key, value in collection_object.GetValueDict().iteritems():
      self.assertEqual(
          value, self._collection_information_object.GetValue(key))

    for identifier, counter in collection_object.GetCounters():
      compare_counter = self._collection_information_object.GetCounter(
          identifier)

      for key, value in counter.iteritems():
        self.assertEqual(value, compare_counter[key])

  def testWriteSerialized(self):
    """Test the write serialized functionality."""
    json_string = self._serializer.WriteSerialized(
        self._collection_information_object)

    # We need to compare dicts since we cannot determine the order
    # of values in the string.
    json_dict = json.loads(json_string)
    self.assertEqual(json_dict, self._json_dict)


if __name__ == '__main__':
  unittest.main()
