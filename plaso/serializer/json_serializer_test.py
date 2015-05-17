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
    self._json_dict = {
        u'__type__': u'EventObject',
        u'a_tuple': [
            u'some item', [234, 52, 15], {u'a': u'not a', u'b': u'not b'}, 35],
        u'data_type': u'test:event2',
        u'empty_string': u'',
        u'integer': 34,
        u'my_dict': {
            u'a': u'not b',
            u'an': [234, 32],
            u'c': 34,
            u'list': [u'sf', 234]
        },
        u'my_list': [u'asf', 4234, 2, 54, u'asf'],
        u'string': u'Normal string',
        u'timestamp_desc': u'Written',
        u'timestamp': 1234124,
        u'uuid': u'5a78777006de4ddb8d7bbe12ab92ccf8',
        u'unicode_string': u'And I am a unicorn.',
        u'zero_integer': 0
    }

  def testReadSerialized(self):
    """Test the read serialized functionality."""
    # We use json.dumps to make sure the dict does not serialize into
    # an invalid JSON string e.g. one that contains string prefixes
    # like b'' or u''.
    json_string = json.dumps(self._json_dict)
    event_object = json_serializer.JsonEventObjectSerializer.ReadSerialized(
        json_string)

    # An integer value containing 0 should get stored.
    self.assertTrue(hasattr(event_object, u'zero_integer'))

    attribute_value = getattr(event_object, u'integer', 0)
    self.assertEqual(attribute_value, 34)

    attribute_value = getattr(event_object, u'my_list', [])
    self.assertEqual(len(attribute_value), 5)

    attribute_value = getattr(event_object, u'string', u'')
    self.assertEqual(attribute_value, u'Normal string')

    attribute_value = getattr(event_object, u'unicode_string', u'')
    self.assertEqual(attribute_value, u'And I am a unicorn.')

    attribute_value = getattr(event_object, u'a_tuple', ())
    self.assertEqual(len(attribute_value), 4)

  def testWriteSerialized(self):
    """Test the write serialized functionality."""
    event_object = event.EventObject()

    event_object.data_type = 'test:event2'
    event_object.timestamp = 1234124
    event_object.timestamp_desc = 'Written'
    # Prevent the event object for generating its own UUID.
    event_object.uuid = u'5a78777006de4ddb8d7bbe12ab92ccf8'

    event_object.empty_string = u''
    event_object.zero_integer = 0
    event_object.integer = 34
    event_object.string = u'Normal string'
    event_object.unicode_string = u'And I am a unicorn.'
    event_object.my_list = [u'asf', 4234, 2, 54, u'asf']
    event_object.my_dict = {
        u'a': u'not b', u'c': 34, u'list': [u'sf', 234], u'an': [234, 32]}
    event_object.a_tuple = (
        u'some item', [234, 52, 15], {u'a': u'not a', u'b': u'not b'}, 35)
    event_object.null_value = None

    json_string = json_serializer.JsonEventObjectSerializer.WriteSerialized(
        event_object)

    # We use json.loads here to compare dicts since we cannot pre-determine
    # the actual order of values in the JSON string.
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
    self._json_dict = {
        u'__COUNTERS__': {
            u'foobar': {
                u'stuff': 1245
            }
        },
        u'foo': u'bar',
        u'foo2': u'randombar'
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
    # We use json.dumps to make sure the dict does not serialize into
    # an invalid JSON string e.g. one that contains string prefixes
    # like b'' or u''.
    json_string = json.dumps(self._json_dict)
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

    # We use json.loads here to compare dicts since we cannot pre-determine
    # the actual order of values in the JSON string.
    json_dict = json.loads(json_string)
    self.assertEqual(json_dict, self._json_dict)


if __name__ == '__main__':
  unittest.main()
