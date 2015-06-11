# -*- coding: utf-8 -*-
"""Pyregf specific implementation for the Windows Registry file access."""

import logging

from plaso import dependencies
from plaso.lib import errors
from plaso.lib import timelib
from plaso.winreg import interface

import pyregf


dependencies.CheckModuleVersion(u'pyregf')


class WinPyregfKey(interface.WinRegKey):
  """Implementation of a Windows Registry key using pyregf."""

  def __init__(self, pyregf_key, parent_path=u'', root=False):
    """Initializes a Windows Registry key object.

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
      self._path = self.PATH_SEPARATOR.join([
          parent_path, self._pyregf_key.name])

  # pylint: disable=method-hidden
  @property
  def path(self):
    """The path of the key."""
    return self._path

  # pylint: disable=function-redefined,arguments-differ,method-hidden
  @path.setter
  def path(self, value):
    """Set the value of the path explicitly."""
    self._path = value

  @property
  def name(self):
    """The name of the key."""
    return self._pyregf_key.name

  @property
  def offset(self):
    """The offset of the key within the Windows Registry file."""
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
      A Windows Registry value object (instance of WinRegValue) if
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
      Windows Registry value objects (instances of WinRegValue) that represent
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
      # Split all the path segments based on the path (segment) separator.
      path_segments = self.path.split(self.PATH_SEPARATOR)
      path_segments.extend(name.split(self.PATH_SEPARATOR))

      # Flatten the sublists into one list.
      path_segments = [
          element for sublist in path_segments for element in sublist]

      # Remove empty path segments.
      path_segments = filter(None, path_segments)

      path = u'{0:s}{1:s}'.format(
          self.PATH_SEPARATOR, self.PATH_SEPARATOR.join(path_segments))

      return WinPyregfKey(path_subkey, path)

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      Windows Registry key objects (instances of WinRegKey) that represent
      the subkeys stored within the key.
    """
    for pyregf_key in self._pyregf_key.sub_keys:
      yield WinPyregfKey(pyregf_key, self.path)


class WinPyregfValue(interface.WinRegValue):
  """Implementation of a Windows Registry value using pyregf."""

  def __init__(self, pyregf_value):
    """Initializes a Windows Registry value object.

    Args:
      pyregf_value: An instance of a pyregf.value object.
    """
    super(WinPyregfValue, self).__init__()
    self._pyregf_value = pyregf_value
    self._type_str = u''

  @property
  def name(self):
    """The name of the value."""
    return self._pyregf_value.name

  @property
  def offset(self):
    """The offset of the value within the Windows Registry file."""
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
          u'Unable to read data from value: {0:s}'.format(
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
        utf16_string = unicode(self._pyregf_value.data.decode(u'utf-16-le'))
        return filter(None, utf16_string.split(b'\x00'))
      except UnicodeError:
        pass

    return self._pyregf_value.data


class WinPyregfFile(interface.WinRegFile):
  """Implementation of a Windows Registry file pyregf.

  Attributes:
    name: the name of the Windows Registry file.
  """

  def __init__(self):
    """Initializes a Windows Registry key object."""
    super(WinPyregfFile, self).__init__()
    self._base_key = None
    self._file_object = None
    self._pyregf_file = pyregf.file()

    self.name = u''

  def Close(self):
    """Closes the Windows Registry file."""
    self._base_key = None

    if self._file_object:
      self._pyregf_file.close()
      self._file_object.close()
      self._file_object = None

  def GetKeyByPath(self, path):
    """Retrieves a specific key defined by the Registry path.

    Args:
      path: the Registry path.

    Returns:
      The key (instance of WinRegKey) if available or None otherwise.
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

  def Open(self, file_entry, codepage=u'cp1252'):
    """Opens the Windows Registry file.

    Args:
      file_entry: The file entry object (instance of dfvfs.FileEntry).
      name: The name of the file.
      codepage: Optional codepage for ASCII strings, default is cp1252.

    Raises:
      IOError: if there is an error opening or reading the Registry file.
    """
    # TODO: Add a more elegant error handling to this issue. There are some
    # code pages that are not supported by the parent library. However we
    # need to properly set the codepage so the library can properly interpret
    # values in the Registry.
    try:
      self._pyregf_file.set_ascii_codepage(codepage)

    except (TypeError, IOError):
      logging.error((
          u'Unable to set the Windows Registry file codepage: {0:s}. '
          u'Ignoring provided value.').format(codepage))

    file_object = file_entry.GetFileObject()
    try:
      self._pyregf_file.open_file_object(file_object)

      self._base_key = self._pyregf_file.get_root_key()

      # TODO: move to a dfVFS like Registry sub-system.
      self.name = file_entry.name
      self._file_object = file_object

    except IOError:
      file_object.close()
      raise
