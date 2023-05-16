#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the serializers."""

from dfdatetime import time_elements as dfdatetime_time_elements

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as dfvfs_path_spec_factory

from plaso.storage import serializers
from tests.storage import test_lib


class SerializersTest(test_lib.StorageTestCase):
  """Tests for the serializers."""

  def testJSONDateTimeAttributeSerializer(self):
    """Tests the JSON date time values attribute serializer."""
    serializer = serializers.JSONDateTimeAttributeSerializer()

    datetime_value = dfdatetime_time_elements.TimeElementsInMicroseconds(
        is_delta=True, time_elements_tuple=(2016, 1, 1, 12, 0, 0, 30))

    serialized_value = serializer.SerializeValue(datetime_value)
    deserialized_value = serializer.DeserializeValue(serialized_value)

    self.assertEqual(deserialized_value, datetime_value)

  def testJSONPathSpecAttributeSerializer(self):
    """Tests the JSON path specification attribute serializer."""
    serializer = serializers.JSONPathSpecAttributeSerializer()

    parent_path_spec = dfvfs_path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location='/compressed.gz')

    path_spec = dfvfs_path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=parent_path_spec)

    serialized_value = serializer.SerializeValue(path_spec)

    deserialized_value = serializer.DeserializeValue(serialized_value)

    self.assertEqual(deserialized_value.comparable, path_spec.comparable)

  def testJSONStringsListAttributeSerializer(self):
    """Tests the JSON strings list attribute serializer."""
    serializer = serializers.JSONStringsListAttributeSerializer()

    serialized_value = serializer.SerializeValue(['a', 'b', 'c'])
    deserialized_value = serializer.DeserializeValue(serialized_value)

    self.assertEqual(deserialized_value, ['a', 'b', 'c'])
