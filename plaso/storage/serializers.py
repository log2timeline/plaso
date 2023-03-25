# -*- coding: utf-8 -*-
"""This file contains the attribute container store serializers."""

import json

from acstore import interface as acstore_interface

from dfdatetime import serializer as dfdatetime_serializer

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as dfvfs_path_spec_factory


class JSONDateTimeAttributeSerializer(acstore_interface.AttributeSerializer):
  """JSON date time values attribute serializer."""

  def DeserializeValue(self, value):
    """Deserializes a value.

    Args:
      value (str): serialized value.

    Returns:
      dfdatetime.DateTimeValues: runtime value.
    """
    json_dict = json.loads(value)

    return dfdatetime_serializer.Serializer.ConvertDictToDateTimeValues(
        json_dict)

  def SerializeValue(self, value):
    """Serializes a value.

    Args:
      value (dfdatetime.DateTimeValues): runtime value.

    Returns:
      list[str]: serialized value.
    """
    json_dict = dfdatetime_serializer.Serializer.ConvertDateTimeValuesToDict(
        value)

    return json.dumps(json_dict)


class JSONPathSpecAttributeSerializer(acstore_interface.AttributeSerializer):
  """JSON path specification attribute serializer."""

  def DeserializeValue(self, value):
    """Deserializes a value.

    Args:
      value (str): serialized value.

    Returns:
      dfvfs.PathSpec: runtime value.
    """
    json_dict = json.loads(value)

    type_indicator = json_dict.get('type_indicator', None)
    if type_indicator:
      del json_dict['type_indicator']

    if 'parent' in json_dict:
      json_dict['parent'] = self.DeserializeValue(json_dict['parent'])

    # Remove the class type from the JSON dictionary since we cannot pass it.
    del json_dict['__type__']

    path_spec = dfvfs_path_spec_factory.Factory.NewPathSpec(
        type_indicator, **json_dict)

    if type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
      # dfvfs.OSPathSpec() will change the location to an absolute path
      # here we want to preserve the original location.
      path_spec.location = json_dict.get('location', None)

    return path_spec

  def SerializeValue(self, value):
    """Serializes a value.

    Args:
      value (dfvfs.PathSpec): runtime value.

    Returns:
      str: serialized value.
    """
    json_dict = {'__type__': 'PathSpec'}
    for property_name in dfvfs_path_spec_factory.Factory.PROPERTY_NAMES:
      property_value = getattr(value, property_name, None)
      if property_value is not None:
        json_dict[property_name] = property_value

    if value.HasParent():
      json_dict['parent'] = self.SerializeValue(value.parent)

    json_dict['type_indicator'] = value.type_indicator
    location = getattr(value, 'location', None)
    if location:
      json_dict['location'] = location

    return json.dumps(json_dict)


class JSONStringsListAttributeSerializer(acstore_interface.AttributeSerializer):
  """JSON strings list attribute serializer."""

  def DeserializeValue(self, value):
    """Deserializes a value.

    Args:
      value (str): serialized value.

    Returns:
      list[str]: runtime value.
    """
    return json.loads(value)

  def SerializeValue(self, value):
    """Serializes a value.

    Args:
      value (str): runtime value.

    Returns:
      list[str]: serialized value.
    """
    return json.dumps(value)
