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
"""This file contains basic interface for registry handling within Plaso.

This library serves a basis for defining interfaces for registry keys, values
and other items that may need defining.

This is provided as a separate file to make it easier to inherit in other
projects that may want to use the registry plugin system in Plaso.
"""
import abc
import logging
import struct


class WinRegKey(object):
  """WinRegKey abstracts the registry key so it can be used in the plugins."""

  def __init__(self):
    """An abstract object for a Windows registry key.

    A WinRegKey abstracts the registry key to make it easy to both implement
    a new library for the underlying mechanism of parsing a registry file,
    without the need to rewrite all of the plugins.

    It also adds the ability to use the plugins in another tool, that may not
    be able to use the same collection and processing mechanism as Plaso does.
    """
    self.path = '\\'
    self.timestamp = 0
    self.offset = 0
    self.name = ''

  @abc.abstractmethod
  def GetValues(self):
    """Returns a generator that returns all values found inside the key.

    The method should yield all WinRegValue objects inside the registry
    key.
    """

  @abc.abstractmethod
  def GetValue(self, path):
    """Return a WinRegValue object for a specific registry key path."""

  @abc.abstractmethod
  def GetSubkeys(self):
    """Generator that returns all subkeys of the key."""

  @abc.abstractmethod
  def HasSubkeys(self):
    """Return a boolean value indicating whether or not the key has subkeys."""
    return False

  @abc.abstractmethod
  def GetSubkeyCount(self):
    """Returns the number of sub keys for this particular registry key."""

  @abc.abstractmethod
  def GetValueCount(self):
    """Returns the number of values this key has."""


class WinRegValue(object):
  """WinRegValue is an object describing a registry value."""

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
    self.offset = 0
    self.name = u''
    self._type = 0
    self._raw_value = u''

  def GetType(self):
    """Return the type of data this value returns."""
    return type(self.GetData())

  def GetTypeStr(self):
    """Returns the registry value type."""
    return self.TYPES.get(self._type, 'NONE')

  def GetRawData(self):
    """Return the raw value data of the key."""
    return self._raw_value

  def GetStringData(self):
    """Return a string value from the value."""
    return self._raw_value

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
    if data_type and not type(data_type) == type:
      raise TypeError('Need to define a proper type')

    val_type = self.GetTypeStr()
    ret = None
    if val_type == 'SZ' or val_type == 'EXPAND_SZ':
      ret = self.GetStringData()
    elif val_type == 'BINARY':
      ret = self.GetRawData()
    elif val_type == 'DWORD_LE':
      try:
        ret = struct.unpack('<i', self.GetRawData()[:4])[0]
      except struct.error as e:
        logging.error('Unable to unpack: {}'.format(e))
        return self.GetRawData()
    elif val_type == 'DWORD_BE':
      try:
        ret = struct.unpack('>i', self.GetRawData()[:4])[0]
      except struct.error as e:
        logging.error('Unable to unpack: {}'.format(e))
        return self.GetRawData()
    elif val_type == 'LINK':
      # TODO: Should we rather fetch the key that is linked
      # to here or simply return the value and let the end user
      # of this library decide what to do with this value?
      ret = GetRegistryStringValue(self.GetRawData(), val_type)
    elif val_type == 'MULTI_SZ':
      raw_data = self.GetRawData()
      if not raw_data:
        return u''
      raw_string = raw_data.decode('utf_16_le', 'ignore')
      ret_list = raw_string.split('\x00')
      ret = filter(None, ret_list)
    elif val_type == 'RESOURCE_LIST':
      # TODO: Return a better format here.
      ret = self.GetRawData()
    elif val_type == 'FULL_RESOURCE_DESCRIPTOR':
      # TODO: Return a better format here.
      ret = self.GetRawData()
    elif val_type == 'QWORD':
      try:
        raw = self.GetRawData()
        if len(raw) >= 8:
          ret = struct.unpack('<q', raw[:8])[0]
        else:
          logging.error(
              u'Unable to unpack value %s, data not long enough for a QWORD',
              self.name)
          ret = raw
      except struct.error as e:
        logging.error('Unable to unpack: {}'.format(e))
        return self.GetRawData()

    if not data_type:
      return ret

    # TODO: Add a more complete solution, now it's only unicode
    # and only partial for that matter.
    if data_type == unicode:
      if type(ret) == list:
        try:
          return u' '.join(ret)
        except UnicodeDecodeError:
          return u' '.decode('utf_16_le', 'ignore').join(ret)

      try:
        ret = unicode(ret)
      except UnicodeDecodeError:
        ret = GetRegistryStringValue(ret, val_type)

    return ret


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
