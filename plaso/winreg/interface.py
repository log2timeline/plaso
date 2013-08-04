#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
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
"""The interface for Windows Registry related objects."""
import abc
import logging
import struct


class WinRegKey(object):
  """Abstract class to represent the Windows Registry Key interface."""

  PATH_SEPARATOR = u'\\'

  @abc.abstractproperty
  def path(self):
    """The path of the key."""

  @abc.abstractproperty
  def name(self):
    """The name of the key."""

  @abc.abstractproperty
  def offset(self):
    """The offset of the key within the Registry File."""

  @abc.abstractproperty
  def last_written_timestamp(self):
    """The last written time of the key represented as a timestamp."""

  @abc.abstractproperty
  def number_of_values(self):
    """The number of values within the key."""

  @abc.abstractmethod
  def GetValue(self, name):
    """Retrieves a value by name.

    Args:
      name: Name of the value or an empty string for the default value.

    Returns:
      An instance of a Windows Registry Value object (WinRegValue) if
      a corresponding value was found or None if not.
    """

  @abc.abstractmethod
  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      Instances of Windows Registry Value objects (WinRegValue) that represent
      the values stored within the key.
    """

  @abc.abstractproperty
  def number_of_subkeys(self):
    """The number of subkeys within the key."""

  @abc.abstractmethod
  def GetSubkey(self, name):
    """Retrive a subkey by name.

    Args:
      name: The relative path of the current key to the desired one.

    Returns:
      The subkey with the relative path of name or None if not found.
    """

  @abc.abstractmethod
  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      Instances of Windows Registry Key objects (WinRegKey) that represent
      the subkeys stored within the key.
    """


class WinRegValue(object):
  """Abstract class to represent the Windows Registry Value interface."""

  REG_NONE = 0
  REG_SZ = 1
  REG_EXPAND_SZ = 2
  REG_BINARY = 3
  REG_DWORD = 4
  REG_DWORD_LITTLE_ENDIAN = 4
  REG_DWORD_BIG_ENDIAN = 5
  REG_LINK = 6
  REG_MULTI_SZ = 7
  REG_RESOURCE_LIST = 8
  REG_FULL_RESOURCE_DESCRIPTOR = 9
  REG_RESOURCE_REQUIREMENT_LIST = 10
  REG_QWORD = 11

  # TODO: refactor the string representations, if no longer needed remove
  # otherwise change to a frozenset of a list of strings.
  TYPES = {
      0: 'NONE',
      1: 'SZ',
      2: 'EXPAND_SZ',
      3: 'BINARY',
      4: 'DWORD_LE',
      5: 'DWORD_BE',
      6: 'LINK',
      7: 'MULTI_SZ',
      8: 'RESOURCE_LIST',
      9: 'FULL_RESOURCE_DESCRIPTOR',
      10: 'RESOURCE_REQUIREMENT_LIST',
      11: 'QWORD'
  }

  def __init__(self):
    """Default constructor for the registry value."""
    self._data = u''

  @abc.abstractproperty
  def name(self):
    """The name of the value."""

  @abc.abstractproperty
  def offset(self):
    """The offset of the value within the Registry File."""

  @abc.abstractproperty
  def data_type(self):
    """Numeric value that contains the data type."""

  @property
  @abc.abstractproperty
  def data(self):
    """The value data as a native Python object."""

  def DataIsInteger(self):
    """Determines, based on the data type, if the data is an integer.

    The data types considered strings are: REG_DWORD (REG_DWORD_LITTLE_ENDIAN),
    REG_DWORD_BIG_ENDIAN and REG_QWORD.

    Returns:
      True if the data is a string, false otherwise.
    """
    return self.data_type in [
        self.REG_DWORD, self.REG_DWORD_BIG_ENDIAN, self.REG_QWORD]

  def DataIsString(self):
    """Determines, based on the data type, if the data is a string.

    The data types considered strings are: REG_SZ, REG_EXPAND_SZ and REG_LINK.

    Returns:
      True if the data is a string, false otherwise.
    """
    return self.data_type in [self.REG_SZ, self.REG_EXPAND_SZ, self.REG_LINK]

  # TODO: temporary solution as the data fallback functionality
  # refactor this function away.
  @classmethod
  def CopyDataToObject(cls, data, data_type):
    """Creates a Python object representation based on the data and data type.

    Where:
      REG_NONE, REG_BINARY, REG_RESOURCE_LIST, REG_FULL_RESOURCE_DESCRIPTOR
      and RESOURCE_REQUIREMENT_LIST are represented as a byte string.

      REG_SZ, REG_EXPAND_SZ and REG_LINK are represented as an Unicode string.

      REG_DWORD, REG_DWORD_BIG_ENDIAN and REG_QWORD as an integer.

      REG_MULTI_SZ as a list of Unicode strings.

      Any data that mismatches data type and size constraits is represented as
      a byte string.

    Note that function is intended to contain the generic conversion behavior.
    A back-end can choose to use this function or provide its own conversion
    functionality.

    Args:
      data: The value data.
      data_type: The numeric value data type.

    Returns:
      A Python object representation of the data.
    """
    if not data:
      return

    if data_type in [cls.REG_SZ, cls.REG_EXPAND_SZ, cls.REG_LINK]:
      try:
        return unicode(data.decode('utf-16-le'))
      except UnicodeError:
        pass

    elif data_type == cls.REG_DWORD and len(data) == 4:
      return struct.unpack('<i', data)[0]

    elif data_type == cls.REG_DWORD_BIG_ENDIAN and len(data) == 4:
      return struct.unpack('>i', data)[0]

    elif data_type == cls.REG_QWORD and len(data) == 8:
      return struct.unpack('<q', data)[0]

    elif data_type == cls.REG_MULTI_SZ:
      try:
        utf16_string = unicode(data.decode('utf-16-le'))
        return filter(None, utf16_string.split('\x00'))
      except UnicodeError:
        pass

    return data

  def GetTypeStr(self):
    """Returns the registry value type."""
    return self.TYPES.get(self.data_type, 'NONE')

  # TODO: refactor this to a data property.
  def GetData(self, data_type=None):
    """Return a Python interpreted data from the value.

    This method interprets the data depending on the type, eg.
    if the type is SZ or EXPAND_SZ it will return a string value,
    if MULTI_SZ a list of strings, etc.

    Args:
      data_type: If the data should be returned as a specific data type
      instead of the default behavior of returning it as proper data type
      depending on the registry type.

    Raises:
      TypeError: If the data type is improperly defined.

    Returns:
      A value that depends on the value type.
    """
    data = self.data

    if not data_type:
      return data

    # TODO: Add a more complete solution, now it's only unicode
    # and only partial for that matter.
    if data_type == unicode:
      if type(data) == list:
        try:
          return u' '.join(data)
        except UnicodeDecodeError:
          return u' '.decode('utf_16_le', 'ignore').join(data)

      try:
        data = unicode(data)
      except UnicodeDecodeError:
        data = GetRegistryStringValue(data, self.GetTypeStr())
    return data

  # TODO: refactor this to a raw_data property.
  @abc.abstractmethod
  def GetRawData(self):
    """Return the raw value data of the key."""


def GetRegistryStringValue(raw_string, key_type='SZ'):
  """Return a string value stored in UTF-16 le.

  This method takes a raw value from a key and it's type
  and returns a Unicode string value from it, based on the type
  of the registry value.

  Args:
    raw_string: The raw string value that may not be properly encoded.
    key_type: The type of registry value (SZ, BINARY, etc.)

  Returns:
    An unicode string.
  """
  # TODO: refactor this function away.
  if key_type == 'BINARY':
    try:
      str_ret = raw_string.decode('utf_16_le')
    except UnicodeDecodeError:
      logging.warning('Error while decoding unicode (UTF_16_LE) %s', key_type)
      str_ret = raw_string.decode('utf_16_le', 'ignore')

    return str_ret

  if key_type == 'MULTI_SZ':
    if type(raw_string) == list:
      return u' '.join(raw_string)

  return raw_string


# TODO: refactor add a registry file interface.
