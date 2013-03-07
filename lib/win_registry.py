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
"""This file contains a basic library used by plaso for registry handling.

This library serves as a basis for reading and parsing registry files in Plaso.
It should provide a read interface to the registry irrelevant of the underlying
registry library that is used to parse the actual registry file.
"""
from plaso.lib import win_registry_interface
import pyregf


class WinPyregKey(win_registry_interface.WinRegKey):
  """An implementation of WinRegKey using pyregf."""

  def __init__(self, key, parent_path=''):
    """An implementation of WinRegKey using pyregf library.

    Args:
      key: The pyregf.key object.
      parent_path: A string, full path of the parent key.
    """
    super(WinPyregKey, self).__init__()
    self._key = key
    self.name = key.name
    self.path = '%s\\%s' % (parent_path, self.name)
    # Timestamp as FILETIME
    filetime = self._key.get_last_written_time_as_integer()
    # TODO: Add a helper function for this since this conversion
    # will take place in several places and could potentially
    # be made less lossy.
    self.timestamp = filetime / 10 - 11644473600000000
    self.offset = self._key.get_offset()

  def GetValues(self):
    """Returns a generator that returns all values found inside the key.

    The method should yield all WinRegValue objects inside the registry
    key.

    Yields:
      A winPyregValue object for each value in the registry key.
    """
    for value in self._key.values:
      yield WinPyregValue(value)

  def GetValue(self, name):
    """Return a WinRegValue object for a specific registry key path."""
    # Value names are not unique and pyregf provides first match for
    # the value. If this becomes problematic this method needs to
    # be changed into a generator, iterating through all returned value
    # for a given name.
    value = self._key.get_value_by_name(name)
    if not value:
      return None

    return WinPyregValue(value)

  def GetSubKeys(self):
    """Returns all subkeys of the registry key."""
    for key in self._key.sub_keys:
      yield WinPyregKey(key, self.path)

  def GetSubkeyCount(self):
    """Returns the number of sub keys for this particular registry key."""
    return self._key.get_number_of_sub_keys()

  def HasSubkeys(self):
    """Return a boolean value indicating whether or not the key has subkeys."""
    if self.GetSubkeyCount():
      return True

    return False

  def GetValueCount(self):
    """Return the number of values this registry key stores."""
    return self._key.get_number_of_values()


class WinPyregValue(win_registry_interface.WinRegValue):
  """An implementation of the WinRegValue based on pyregf."""

  def __init__(self, value):
    """Initializes the Windows Registry value object."""
    super(WinPyregValue, self).__init__()
    self._value = value
    self.offset = value.get_offset()
    self.name = value.name
    self._type = value.type
    self._type_str = self.GetTypeStr()
    self._raw_value = self._value.data

  def GetStringData(self):
    """Return a string value from the data, if it is a string type."""
    if self._type_str == 'SZ' or self._type_str == 'EXPAND_SZ':
      try:
        ret = self._value.data_as_string
      except IOError:
        ret = win_registry_interface.GetRegistryStringValue(
            self.GetRawData(), self._type_str)

      return ret

    return win_registry_interface.GetRegistryStringValue(
        self.GetRawData(), self._type_str)


class WinRegistry(object):
  """Provides access to the Windows registry file."""

  def __init__(self, hive, codepage='cp1252'):
    """Constructor for the registry object.

    Args:
      hive: A file-like object, most likely a PFile object for the registry.
      codepage: The codepage of the registry hive, used for string
                representation.
    """
    self._hive = pyregf.file()
    self._hive.open_file_object(hive)
    self._hive.set_ascii_codepage(codepage)
    # Keeping a copy of the volume due to limitation of the python bindings
    # for VSS.
    self._fh = hive

  def GetRoot(self):
    """Return the root key of the registry hive."""
    ret = WinPyregKey(self._hive.get_root_key())
    ret.path = ''
    return ret

  def GetKey(self, key):
    """Return a registry key as a WinPyregKey object."""
    if not key:
      return None

    my_key = self._hive.get_key_by_path(key)
    if not my_key:
      return None

    path, _, _ = key.rpartition('\\')

    return WinPyregKey(my_key, path)

  def __contains__(self, key):
    """Check if a certain registry key exists within the hive."""
    try:
      return bool(self.GetKey(key))
    except KeyError:
      return False

  def GetAllSubKeys(self, key):
    """Generator that returns all sub keys of any given registry key.

    Args:
      key: The key that should be recursively searched.

    Yields:
      A WinPyregKey for each registry key underneath the input key.
    """
    for subkey in key.GetSubKeys():
      yield subkey
      if subkey.HasSubkeys():
        for s in self.GetAllSubKeys(subkey):
          yield s

  def __iter__(self):
    """Default iterator, returns all subkeys of the registry hive."""
    root = self.GetRoot()
    for key in self.GetAllSubKeys(root):
      yield key


def GetLibraryVersion():
  """Return the library version number of pyregf."""
  return pyregf.get_version()
