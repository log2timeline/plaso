#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains a simple abstraction of registry keys for testing."""
from plaso.lib import eventdata
from plaso.lib import win_registry_interface
from plaso.formatters import winreg


class TestRegKey(win_registry_interface.WinRegKey):
  """A simple implementation of a registry key to use in testing."""

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
    self.path = path
    self.timestamp = timestamp
    self.offset = offset
    self._values = values
    self.name = path.split('\\')[-1]
    self._subkeys = subkeys

  def GetValues(self):
    """Return a list of all values from the registry key."""
    return self._values

  def GetValue(self, name):
    """Return a WinRegValue object for a specific registry key path."""
    for value in self._values:
      if value.name == name:
        return value

  def GetSubKeys(self):
    """Return a list of all subkeys."""
    return self._subkeys

  def HasSubkeys(self):
    """Return a boolean value indicating whether or not the key has subkeys."""
    return bool(self._subkeys)

  def GetSubkeyCount(self):
    """Returns the number of sub keys for this particular registry key."""
    return len(self._subkeys)

  def GetValueCount(self):
    """Return the number of values stored."""
    return len(self._values)


class TestRegValue(win_registry_interface.WinRegValue):
  """WinRegValue is an object describing a registry value."""

  def __init__(self, name, value, value_type=1, offset=0):
    """Set up the test reg value object."""
    super(TestRegValue, self).__init__()
    self.offset = offset
    self.name = name
    self._raw_value = value
    self._type = value_type
    self._type_str = self.GetTypeStr()

  def GetStringData(self):
    """Return a string data."""
    if self._type_str == 'SZ' or self._type_str == 'EXPAND_SZ':
      return self._raw_value.decode('utf_16_le', 'ignore')

    return u''
