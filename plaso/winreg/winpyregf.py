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


if pyregf.get_version() < '20130716':
  raise ImportWarning('WinPyregf requires at least pyregf 20130716.')


class WinPyregfKey(interface.WinRegKey):
  """Implementation of a Windows Registry Key using pyregf."""

  def __init__(self, pyregf_key, parent_path=u'', root=False):
    """Initializes a Windows Registry Key object.

    Args:
      pyregf_key: An instance of a pyregf.key object.
      parent_path: The path of the parent key.
      root: A boolean key indicating we are dealing with a root key.
    """
    super(WinPyregfKey, self).__init__()
    self._pyregf_key = pyregf_key
    # Adding few checks to make sure the root key is not
    # invalid in plugin checks (root key is equal to the
    # path separator).
    if parent_path == self.PATH_SEPARATOR:
      parent_path = u''
    if root:
      self._path = self.PATH_SEPARATOR
    else:
      self._path = self.PATH_SEPARATOR.join(
          [parent_path, self._pyregf_key.name])

  @property
  def path(self):   # pylint: disable-msg=E0202
    """The path of the key."""
    return self._path

  @path.setter
  def path(self, value):    # pylint: disable-msg=E0102,W0221,E0202
    """Set the value of the path explicitly."""
    self._path = value

  @property
  def name(self):
    """The name of the key."""
    return self._pyregf_key.name

  @property
  def offset(self):
    """The offset of the key within the Registry File."""
    return self._pyregf_key.offset

  @property
  def last_written_timestamp(self):
    """The last written time of the key represented as a timestamp."""
    return timelib.Timestamp.FromFiletime(
        self._pyregf_key.get_last_written_time_as_integer())

  @property
  def number_of_values(self):
    """The number of values within the key."""
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
      return WinPyregfValue(pyregf_value)
    return None

  @property
  def number_of_subkeys(self):
    """The number of subkeys within the key."""
    return self._pyregf_key.number_of_sub_keys

  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      Instances of Windows Registry Value objects (WinRegValue) that represent
      the values stored within the key.
    """
    for pyregf_value in self._pyregf_key.values:
      yield WinPyregfValue(pyregf_value)

  def GetSubkey(self, name):
    """Retrive a subkey by name.

    Args:
      name: The relative path of the current key to the desired one.

    Returns:
      The subkey with the relative path of name or None if not found.
    """
    subkey = self._pyregf_key.get_sub_key_by_name(name)

    if subkey:
      return WinPyregfKey(subkey, self.path)

    path_subkey = self._pyregf_key.get_sub_key_by_path(name)
    if path_subkey:
      path, _, _ = name.rpartition('\\')
      return WinPyregfKey(path_subkey, self.path + u'\\%s' % path)

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      Instances of Windows Registry Key objects (WinRegKey) that represent
      the subkeys stored within the key.
    """
    for pyregf_key in self._pyregf_key.sub_keys:
      yield WinPyregfKey(pyregf_key, self.path)


class WinPyregfValue(interface.WinRegValue):
  """Implementation of a Windows Registry Value using pyregf."""

  def __init__(self, pyregf_value):
    """Initializes a Windows Registry Value object.

    Args:
      pyregf_value: An instance of a pyregf.value object.
    """
    super(WinPyregfValue, self).__init__()
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
  def raw_data(self):
    """The value data as a byte string."""
    try:
      return self._pyregf_value.data
    except IOError:
      raise errors.WinRegistryValueError(
          'Unable to read data from value: {0:s}'.format(
          self._pyregf_value.name))

  @property
  def data(self):
    """The value data as a native Python object."""
    if self._pyregf_value.type in [
        self.REG_SZ, self.REG_EXPAND_SZ, self.REG_LINK]:
      try:
        return self._pyregf_value.data_as_string
      except IOError:
        pass

    elif self._pyregf_value.type in [
        self.REG_DWORD, self.REG_DWORD_BIG_ENDIAN, self.REG_QWORD]:
      try:
        return self._pyregf_value.data_as_integer
      except (IOError, OverflowError):
        # TODO: Rethink this approach. The value is not -1, but we cannot
        # return the raw data, since the calling plugin expects an integer
        # here.
        return -1

    # TODO: Add support for REG_MULTI_SZ to pyregf.
    elif self._pyregf_value.type == self.REG_MULTI_SZ:
      if self._pyregf_value.data is None:
        return u''

      try:
        utf16_string = unicode(self._pyregf_value.data.decode('utf-16-le'))
        return filter(None, utf16_string.split('\x00'))
      except UnicodeError:
        pass

    return self._pyregf_value.data


class WinPyregfFile(interface.WinRegFile):
  """Implementation of a Windows Registry File using pyregf."""

  def __init__(self):
    """Initializes a Windows Registry Key object."""
    super(WinPyregfFile, self).__init__()
    self._pyregf_file = pyregf.file()
    self.name = ''
    self.file_object = None
    self._base_key = None

  def Open(self, file_object, codepage='cp1252'):
    """Opens the Registry file.

    Args:
      file_object: The file-like object of the Registry file.
      codepage: Optional codepage for ASCII strings, default is cp1252.
    """
    # TODO: Add a more elegant error handling to this issue. There are some
    # code pages that are not supported by the parent library. However we
    # need to properly set the codepage so the library can properly interpret
    # values in the registry.
    try:
      self._pyregf_file.set_ascii_codepage(codepage)

    except (TypeError, IOError):
      logging.error((
          u'Unable to set the Registry file codepage: {0:s}. '
          u'Ignoring provided value.').format(codepage))

    # Keeping a copy of the original file object in case attributes from
    # it are needed (preg uses it for instance to get the pathspec attribute
    # directly from the file object).
    self.file_object = file_object

    self._pyregf_file.open_file_object(file_object)
    self.name = getattr(file_object, 'name', '')
    self._base_key = self._pyregf_file.get_root_key()

  def Close(self):
    """Closes the Registry file."""
    self._pyregf_file.close()
    self.file_object = None

  def GetKeyByPath(self, path):
    """Retrieves a specific key defined by the Registry path.

    Args:
      path: the Registry path.

    Returns:
      The key (an instance of WinRegKey) if available or None otherwise.
    """
    if not path:
      return None

    if not self._base_key:
      return None

    pyregf_key = self._base_key.get_sub_key_by_path(path)

    if not pyregf_key:
      return None

    if pyregf_key.name == self._base_key.name:
      root = True
    else:
      root = False

    parent_path, _, _ = path.rpartition(interface.WinRegKey.PATH_SEPARATOR)
    return WinPyregfKey(pyregf_key, parent_path, root)


class WinRegistry(object):
  """Provides access to the Windows registry file."""
  # TODO: deprecate this class.

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
    key = WinPyregfKey(self._pyregf_file.get_root_key())
    # Change root key name to avoid key based plugins failing.
    key.path = ''
    return key

  def GetKey(self, key):
    """Return a registry key as a WinPyregfKey object."""
    if not key:
      return None

    my_key = self._pyregf_file.get_key_by_path(key)
    if not my_key:
      return None

    path, _, _ = key.rpartition('\\')

    return WinPyregfKey(my_key, path)

  def __contains__(self, key):
    """Check if a certain registry key exists within the hive."""
    try:
      return bool(self.GetKey(key))
    except KeyError:
      return False

  def GetAllSubkeys(self, key):
    """Generator that returns all sub keys of any given registry key.

    Args:
      key: A Windows Registry key string or a WinPyregfKey object.

    Yields:
      A WinPyregfKey for each registry key underneath the input key.
    """
    # TODO: refactor this function.
    # TODO: remove the hasattr check.
    if not hasattr(key, 'GetSubkeys'):
      key = self.GetKey(key)

    for subkey in key.GetSubkeys():
      yield subkey
      if subkey.number_of_subkeys != 0:
        for s in self.GetAllSubkeys(subkey):
          yield s

  def __iter__(self):
    """Default iterator, returns all subkeys of the Registry file."""
    root = self.GetRoot()
    for key in self.GetAllSubkeys(root):
      yield key


def GetLibraryVersion():
  """Return the pyregf and libregf version."""
  return pyregf.get_version()
