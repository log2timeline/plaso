#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""Windows Registry related functions and classes for testing."""

import construct
import os
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.winreg import interface


class TestRegKey(interface.WinRegKey):
  """Implementation of the Registry key interface for testing."""

  def __init__(self, path, last_written_timestamp, values, offset=0,
               subkeys=None):
    """An abstract object for a Windows Registry key.

       This implementation is more a manual one, so it can be used for
       testing the Registry plugins without requiring a full blown
       Windows Registry file to extract key values.

    Args:
      path: The full key name and path.
      last_written_timestamp: An integer containing the the last written
                              timestamp of the Registry key.
      values: A list of TestRegValue values this key holds.
      offset: A byte offset into the Windows Registry file where the entry lies.
      subkeys: A list of subkeys this key has.
    """
    super(TestRegKey, self).__init__()
    self._name = None
    self._path = path
    self._last_written_timestamp = last_written_timestamp
    self._values = values
    self._offset = offset
    if subkeys is None:
      self._subkeys = []
    else:
      self._subkeys = subkeys

  @property
  def path(self):
    """The path of the key."""
    return self._path

  @property
  def name(self):
    """The name of the key."""
    if not self._name and self._path:
      self._name = self._path.split(self.PATH_SEPARATOR)[-1]
    return self._name

  @property
  def offset(self):
    """The offset of the key within the Windows Registry file."""
    return self._offset

  @property
  def last_written_timestamp(self):
    """The last written time of the key represented as a timestamp."""
    return self._last_written_timestamp

  def number_of_values(self):
    """The number of values within the key."""
    return len(self._values)

  def GetValue(self, name):
    """Return a WinRegValue object for a specific Registry key path."""
    for value in self._values:
      if value.name == name:
        return value

  def GetValues(self):
    """Return a list of all values from the Registry key."""
    return self._values

  def number_of_subkeys(self):
    """The number of subkeys within the key."""
    return len(self._subkeys)

  def GetSubkey(self, name):
    """Retrieve a subkey by name.

    Args:
      name: The relative path of the current key to the desired one.

    Returns:
      The subkey with the relative path of name or None if not found.
    """
    for subkey in self._subkeys:
      if subkey.name == name:
        return subkey
    return

  def GetSubkeys(self):
    """Return a list of all subkeys."""
    return self._subkeys


class TestRegValue(interface.WinRegValue):
  """Implementation of the Registry value interface for testing."""

  _INT32_BIG_ENDIAN = construct.SBInt32('value')
  _INT32_LITTLE_ENDIAN = construct.SLInt32('value')
  _INT64_LITTLE_ENDIAN = construct.SLInt64('value')

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
    """The offset of the value within the Windows Registry file."""
    return self._offset

  @property
  def data_type(self):
    """Numeric value that contains the data type."""
    return self._data_type

  @property
  def raw_data(self):
    """The value data as a byte string."""
    return self._data

  @property
  def data(self):
    """The value data as a native Python object."""
    if not self._data:
      return None

    if self._data_type in [self.REG_SZ, self.REG_EXPAND_SZ, self.REG_LINK]:
      try:
        return unicode(self._data.decode('utf-16-le'))
      except UnicodeError:
        pass

    elif self._data_type == self.REG_DWORD and len(self._data) == 4:
      return self._INT32_LITTLE_ENDIAN.parse(self._data)

    elif self._data_type == self.REG_DWORD_BIG_ENDIAN and len(self._data) == 4:
      return self._INT32_BIG_ENDIAN.parse(self._data)

    elif self._data_type == self.REG_QWORD and len(self._data) == 8:
      return self._INT64_LITTLE_ENDIAN.parse(self._data)

    elif self._data_type == self.REG_MULTI_SZ:
      try:
        utf16_string = unicode(self._data.decode('utf-16-le'))
        return filter(None, utf16_string.split('\x00'))
      except UnicodeError:
        pass

    return self._data


class WinRegTestCase(unittest.TestCase):
  """The unit test case for winreg."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), 'test_data')

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file relative to the test data directory.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)

  def _GetTestFileEntry(self, path):
    """Retrieves the test file entry.

    Args:
      path: the path of the test file.

    Returns:
      The test file entry (instance of dfvfs.FileEntry).
    """
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    return path_spec_resolver.Resolver.OpenFileEntry(path_spec)
