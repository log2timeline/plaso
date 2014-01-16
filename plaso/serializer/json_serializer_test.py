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
"""Tests for the serializer object implementation using json."""

import re
import unittest

from plaso.lib import event
from plaso.serializer import json_serializer

# TODO: add tests for the non implemented serializer objects when implemented.


class JsonEventObjectSerializerTest(unittest.TestCase):
  """Tests for the json event object serializer object."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._json_string = """{
        "zero_integer": 0,
        "my_dict": {
            "a": "not b",
            "c": 34,
            "list": ["sf", 234], "an": [234, 32]},
        "uuid": "5a78777006de4ddb8d7bbe12ab92ccf8",
        "timestamp_desc": "Written",
        "a_tuple": [
            "some item",
            [234, 52, 15],
            {"a": "not a", "b": "not b"},
            35],
        "timestamp": 1234124,
        "my_list": ["asf", 4234, 2, 54, "asf"],
        "empty_string": "",
        "data_type": "test:event2",
        "null_value": null,
        "unicode_string": "And I'm a unicorn.",
        "integer": 34,
        "string": "Normal string"}"""

    # Collaps multiple spaces and new lines into a single space.
    expression = re.compile(r'[ \n]+')
    self._json_string = expression.sub(' ', self._json_string)
    # Remove spaces after { and [ characters.
    expression = re.compile(r'([{[])[ ]+')
    self._json_string = expression.sub('\\1', self._json_string)
    # Remove spaces before } and ] characters.
    expression = re.compile(r'[ ]+([}\]])')
    self._json_string = expression.sub('\\1', self._json_string)

  def testReadSerialized(self):
    """Test the read serialized functionality."""
    serializer = json_serializer.JsonEventObjectSerializer
    event_object = serializer.ReadSerialized(self._json_string)

    # An integer value containing 0 should get stored.
    self.assertTrue(hasattr(event_object, 'zero_integer'))

    attribute_value = getattr(event_object, 'integer', 0)
    self.assertEquals(attribute_value, 34)

    attribute_value = getattr(event_object, 'my_list', [])
    self.assertEquals(len(attribute_value), 5)

    attribute_value = getattr(event_object, 'string', '')
    self.assertEquals(attribute_value, 'Normal string')

    attribute_value = getattr(event_object, 'unicode_string', u'')
    self.assertEquals(attribute_value, u'And I\'m a unicorn.')

    attribute_value = getattr(event_object, 'a_tuple', ())
    self.assertEquals(len(attribute_value), 4)

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
    event_object.unicode_string = u'And I\'m a unicorn.'
    event_object.my_list = ['asf', 4234, 2, 54, 'asf']
    event_object.my_dict = {
        'a': 'not b', 'c': 34, 'list': ['sf', 234], 'an': [234, 32]}
    event_object.a_tuple = (
        'some item', [234, 52, 15], {'a': 'not a', 'b': 'not b'}, 35)
    event_object.null_value = None

    serializer = json_serializer.JsonEventObjectSerializer
    json_string = serializer.WriteSerialized(event_object)
    self.assertEquals(json_string, self._json_string)

    event_object = serializer.ReadSerialized(json_string)

    # TODO: fix this.
    # An empty string should not get stored.
    # self.assertFalse(hasattr(event_object, 'empty_string'))

    # A None (or Null) value should not get stored.
    # self.assertFalse(hasattr(event_object, 'null_value'))


if __name__ == '__main__':
  unittest.main()
