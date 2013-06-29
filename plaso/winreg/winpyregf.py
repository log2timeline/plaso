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
"""Pyregf specific implementation for the Plaso Windows Registry File access."""
import logging

from plaso.lib import errors
from plaso.lib import timelib
from plaso.winreg import interface

import pyregf


class WinPyregKey(interface.WinRegKey):
  """Implementation of a Windows Registry Key using pyregf."""

  def __init__(self, pyregf_key, parent_path=u''):
    """Initializes a Windows Registry Key object.

    Args:
      pyregf_key: An instance of a pyregf.key object.
      parent_path: The path of the parent key.
    """
    super(WinPyregKey, self).__init__()
    self._pyregf_key = pyregf_key
    self._path = self.PATH_SEPARATOR.join([parent_path, self._pyregf_key.name])

  @property
  def path(self):
    """The path of the key."""
    return self._path

  @property
  def name(self):
    """The name of the key."""
    return self._pyregf_key.name

  @property
  def offset(self):
    """The offset of the key within the Registry File."""
    return self._pyregf_key.offset

  @property
  def timestamp(self):
    """The last written time of the key represented as a timestamp."""
    return timelib.Timestamp.FromFiletime(
        self._pyregf_key.get_last_written_time_as_integer())

  def GetValueCount(self):
    """Retrieves the number of values within the key."""
    return self._pyregf_key.number_of_values

  def GetValue(self, name):
    """Retrieves a value by name.

    Args:
      name: Name of the value or an empty string for the default value.

    Returns:
      An instance of a Windows Registry Value object (WinRegValue) if
      a corresponding value was found or None if not.
    """
    # Value names are not unique and pyregf provides first match for
    # the value. If this becomes problematic this method needs to
    # be changed into a generator, iterating through all returned value
    # for a given name.
    pyregf_value = self._pyregf_key.get_value_by_name(name)
    if pyregf_value:
      return WinPyregValue(pyregf_value)
    return None

  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      Instances of Windows Registry Value objects (WinRegValue) that represent
      the values stored within the key.
    """
    for pyregf_value in self._pyregf_key.values:
      yield WinPyregValue(pyregf_value)

  def GetSubkeyCount(self):
    """Retrieves the number of subkeys within the key."""
    return self._pyregf_key.number_of_sub_keys

  def HasSubkeys(self):
    """Determines if the key has subkeys."""
    return self._pyregf_key.number_of_sub_keys != 0

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      Instances of Windows Registry Key objects (WinRegKey) that represent
      the subkeys stored within the key.
    """
    for pyregf_key in self._pyregf_key.sub_keys:
      yield WinPyregKey(pyregf_key, self.path)


class WinPyregValue(interface.WinRegValue):
  """Implementation of a Windows Registry Value using pyregf."""

  def __init__(self, pyregf_value):
    """Initializes a Windows Registry Value object.

    Args:
      pyregf_value: An instance of a pyregf.value object.
    """
    super(WinPyregValue, self).__init__()
    self._pyregf_value = pyregf_value
    self._type_str = ''

  @property
  def name(self):
    """The name of the value."""
    return self._pyregf_value.name

  @property
  def offset(self):
    """The offset of the value within the Registry File."""
    return self._pyregf_value.offset

  @property
  def data_type(self):
    """Numeric value that contains the data type."""
    return self._pyregf_value.type

  @property
  def data(self):
    """The value data as a native Python object."""
    # TODO: add support for REG_LINK to pyregf.
    if self._pyregf_value.type in [self.REG_SZ, self.REG_EXPAND_SZ]:
      try:
        return self._pyregf_value.data_as_string
      except IOError:
        pass

    elif self._pyregf_value.type in [
        self.REG_DWORD, self.REG_DWORD_BIG_ENDIAN, self.REG_QWORD]:
      try:
        return self._pyregf_value.data_as_integer
      except IOError:
        pass
      except AttributeError:
        import pdb
        pdb.post_mortem()

    # TODO: add support for REG_MULTI_SZ to pyregf.
    elif self._pyregf_value.type in [self.REG_LINK, self.REG_MULTI_SZ]:
      return interface.WinRegValue.CopyDataToObject(
          self._pyregf_value.data, self._pyregf_value.type)

    return self._pyregf_value.data

  def GetRawData(self):
    """Return the raw value data of the key."""
    try:
      return self._pyregf_value.data
    except IOError:
      raise errors.WinRegistryValueError(
          'Unable to read raw data from value: %s' % self._pyregf_value.name)

  def GetStringData(self):
    """Return a string value from the data, if it is a string type."""
    if not self._type_str:
      self._type_str = self.GetTypeStr()
    if self._type_str == 'SZ' or self._type_str == 'EXPAND_SZ':
      try:
        ret = self._pyregf_value.data_as_string
      except IOError:
        ret = interface.GetRegistryStringValue(
            self.GetRawData(), self._type_str)

      return ret

    return interface.GetRegistryStringValue(
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
    self._pyregf_file = pyregf.file()
    self._pyregf_file.open_file_object(hive)
    try:
      # TODO: Add a more elegant error handling to this issue. There are some
      # code pages that are not supported by the parent library. However we
      # need to properly set the codepage so the library can properly interpret
      # values in the registry.
      self._pyregf_file.set_ascii_codepage(codepage)
    except (TypeError, IOError):
      logging.error(
          u'Unable to set the registry codepage to: {}. Not setting it'.format(
              codepage))
    # Keeping a copy of the volume due to limitation of the python bindings
    # for VSS.
    self._fh = hive

  def GetRoot(self):
    """Return the root key of the registry hive."""
    return WinPyregKey(self._pyregf_file.get_root_key())

  def GetKey(self, key):
    """Return a registry key as a WinPyregKey object."""
    if not key:
      return None

    my_key = self._pyregf_file.get_key_by_path(key)
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

  def GetAllSubkeys(self, key):
    """Generator that returns all sub keys of any given registry key.

    Args:
      key: A Windows Registry key string or a WinPyregKey object.

    Yields:
      A WinPyregKey for each registry key underneath the input key.
    """
    if not hasattr(key, 'GetSubkeys'):
      key = self.GetKey(key)

    for subkey in key.GetSubkeys():
      yield subkey
      if subkey.HasSubkeys():
        for s in self.GetAllSubkeys(subkey):
          yield s

  def __iter__(self):
    """Default iterator, returns all subkeys of the registry hive."""
    root = self.GetRoot()
    for key in self.GetAllSubkeys(root):
      yield key


def GetLibraryVersion():
  """Return the pyregf and libregf version."""
  return pyregf.get_version()
