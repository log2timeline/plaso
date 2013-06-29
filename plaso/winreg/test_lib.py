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
"""Implementation of Windows Registry related objects for testing."""
from plaso.winreg import interface


class TestRegKey(interface.WinRegKey):
  """Implementation of the Registry key interface for testing."""

  def __init__(self, path, timestamp, values, offset=0, subkeys=None):
    """An abstract object for a Windows registry key.

    This implementation is more a manual one, so it can be used for
    testing the registry plugins without requiring a full blown
    registry file to extract key values.

    Args:
      path: The full key name and path.
      timestamp: An integer, indicating the last written timestamp of
      the registry key.
      values: A list of TestRegValue values this key holds.
      offset: A byte offset into the registry file where the entry lies.
      subkeys: A list of subkeys this key has.
    """
    super(TestRegKey, self).__init__()
    self._path = path
    self._timestamp = timestamp
    self._values = values
    self._offset = offset
    self._subkeys = subkeys

  @property
  def path(self):
    """The path of the key."""
    return self._path

  @property
  def name(self):
    """The name of the key."""
    if not self._name and self._path:
      self._name = self._path.split(self.PATH_SEPARATOR)[-1];
    return self._name

  @property
  def offset(self):
    """The offset of the key within the Registry File."""
    return self._offset

  @property
  def timestamp(self):
    """The last written time of the key represented as a timestamp."""
    return self._timestamp

  def GetValueCount(self):
    """Return the number of values stored."""
    return len(self._values)

  def GetValue(self, name):
    """Return a WinRegValue object for a specific registry key path."""
    for value in self._values:
      if value.name == name:
        return value

  def GetValues(self):
    """Return a list of all values from the registry key."""
    return self._values

  def GetSubkeyCount(self):
    """Returns the number of sub keys for this particular registry key."""
    return len(self._subkeys)

  def HasSubkeys(self):
    """Return a boolean value indicating whether or not the key has subkeys."""
    return bool(self._subkeys)

  def GetSubkeys(self):
    """Return a list of all subkeys."""
    return self._subkeys


class TestRegValue(interface.WinRegValue):
  """Implementation of the Registry value interface for testing."""

  def __init__(self, name, data, data_type, offset=0):
    """Set up the test reg value object."""
    super(TestRegValue, self).__init__()
    self._name = name
    self._data = data
    self._data_type = data_type
    self._offset = offset
    self._type_str = ''

  @property
  def name(self):
    """The name of the value."""
    return self._name

  @property
  def offset(self):
    """The offset of the value within the Registry File."""
    return self._offset

  @property
  def data_type(self):
    """Numeric value that contains the data type."""
    return self._data_type

  @property
  def data(self):
    """The value data as a native Python object."""
    return interface.WinRegValue.CopyDataToObject(
        self._data, self._data_type)

  def GetRawData(self):
    """Return the raw value data of the key."""
    return self._data

  def GetStringData(self):
    """Return a string data."""
    if self._data_type in [self.REG_SZ, self.REG_EXPAND_SZ]:
      return self._data.decode('utf_16_le', 'ignore')
    return u''
