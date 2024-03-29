# -*- coding: utf-8 -*-
"""This file contains the attribute container store serializers."""

from acstore import interface as acstore_interface

from dfdatetime import serializer as dfdatetime_serializer

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as dfvfs_path_spec_factory


class JSONDateTimeAttributeSerializer(acstore_interface.AttributeSerializer):
  """JSON date time values attribute serializer."""

  def DeserializeValue(self, value):
    """Deserializes a value.

    Args:
      value (dict[str, object]): serialized value.

    Returns:
      dfdatetime.DateTimeValues: runtime value.
    """
    return dfdatetime_serializer.Serializer.ConvertDictToDateTimeValues(value)

  def SerializeValue(self, value):
    """Serializes a value.

    Args:
      value (dfdatetime.DateTimeValues): runtime value.

    Returns:
      dict[str, object]: serialized value.
    """
    return dfdatetime_serializer.Serializer.ConvertDateTimeValuesToDict(value)


class JSONPathSpecAttributeSerializer(acstore_interface.AttributeSerializer):
  """JSON path specification attribute serializer."""

  def DeserializeValue(self, value):
    """Deserializes a value.

    Args:
      value (dict[str, object]): serialized value.

    Returns:
      dfvfs.PathSpec: runtime value.
    """
    type_indicator = value.get('type_indicator', None)
    if type_indicator:
      del value['type_indicator']

    if 'parent' in value:
      value['parent'] = self.DeserializeValue(value['parent'])

    # Remove the class type from the JSON dictionary since we cannot pass it.
    del value['__type__']

    path_spec = dfvfs_path_spec_factory.Factory.NewPathSpec(
        type_indicator, **value)

    if type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
      # dfvfs.OSPathSpec() will change the location to an absolute path
      # here we want to preserve the original location.
      path_spec.location = value.get('location', None)

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

    return json_dict


class JSONValueListAttributeSerializer(acstore_interface.AttributeSerializer):
  """JSON value list attribute serializer."""

  def DeserializeValue(self, value):
    """Deserializes a value.

    Args:
      value (list[int|str]): serialized value.

    Returns:
      list[int|str]: runtime value.
    """
    return value

  def SerializeValue(self, value):
    """Serializes a value.

    Args:
      value (list[int|str]): runtime value.

    Returns:
      list[int|str]: serialized value.
    """
    return value
