# -*- coding: utf-8 -*-
"""REGF Windows Registry objects implementation using pyregf."""

import pyregf

from plaso import dependencies
from plaso.dfwinreg import definitions
from plaso.dfwinreg import errors
from plaso.dfwinreg import interface


dependencies.CheckModuleVersion(u'pyregf')


class REGFWinRegistryKey(interface.WinRegistryKey):
  """Implementation of a Windows Registry key using pyregf."""

  def __init__(self, pyregf_key, key_path=u''):
    """Initializes a Windows Registry key object.

    Args:
      pyregf_key: a pyreg key object (instance of a pyregf.key).
      key_path: optional Windows Registry key path.
    """
    super(REGFWinRegistryKey, self).__init__(key_path=key_path)
    self._pyregf_key = pyregf_key

  @property
  def last_written_time(self):
    """The last written time of the key (contains a FILETIME timestamp)."""
    return self._pyregf_key.get_last_written_time_as_integer()

  @property
  def name(self):
    """The name of the key."""
    return self._pyregf_key.name

  @property
  def number_of_subkeys(self):
    """The number of subkeys within the key."""
    return self._pyregf_key.number_of_sub_keys

  @property
  def number_of_values(self):
    """The number of values within the key."""
    return self._pyregf_key.number_of_values

  @property
  def offset(self):
    """The offset of the key within the Windows Registry file."""
    return self._pyregf_key.offset

  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name: The name of the subkey.

    Returns:
      The Windows Registry subkey (instances of WinRegistryKey) or
      None if not found.
    """
    pyregf_key = self._pyregf_key.get_sub_key_by_name(name)
    if not pyregf_key:
      return

    key_path = self._JoinKeyPath([self._key_path, pyregf_key.name])
    return REGFWinRegistryKey(pyregf_key, key_path=key_path)

  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      Windows Registry key objects (instances of WinRegistryKey) that represent
      the subkeys stored within the key.
    """
    for pyregf_key in self._pyregf_key.sub_keys:
      key_path = self._JoinKeyPath([self._key_path, pyregf_key.name])
      yield REGFWinRegistryKey(pyregf_key, key_path=key_path)

  def GetValueByName(self, name):
    """Retrieves a value by name.

    Value names are not unique and pyregf provides first match for
    the value.

    Args:
      name: Name of the value or an empty string for the default value.

    Returns:
      A Windows Registry value object (instance of WinRegistryValue) if
      a corresponding value was found or None if not.
    """
    pyregf_value = self._pyregf_key.get_value_by_name(name)
    if not pyregf_value:
      return

    return REGFWinRegistryValue(pyregf_value)

  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      Windows Registry value objects (instances of WinRegistryValue) that
      represent the values stored within the key.
    """
    for pyregf_value in self._pyregf_key.values:
      yield REGFWinRegistryValue(pyregf_value)


class REGFWinRegistryValue(interface.WinRegistryValue):
  """Implementation of a Windows Registry value using pyregf."""

  def __init__(self, pyregf_value):
    """Initializes a Windows Registry value object.

    Args:
      pyregf_value: An instance of a pyregf.value object.
    """
    super(REGFWinRegistryValue, self).__init__()
    self._pyregf_value = pyregf_value

  @property
  def data(self):
    """The value data as a native Python object.

    Raises:
      WinRegistryValueError: if the value data cannot be read.
    """
    if self._pyregf_value.type in self._STRING_VALUE_TYPES:
      try:
        return self._pyregf_value.get_data_as_string()
      except IOError as exception:
        raise errors.WinRegistryValueError(
            u'Unable to read data from value: {0:s} with error: {1:s}'.format(
                self._pyregf_value.name, exception))

    elif self._pyregf_value.type in self._INTEGER_VALUE_TYPES:
      try:
        return self._pyregf_value.get_data_as_integer()
      except (IOError, OverflowError):
        raise errors.WinRegistryValueError(
            u'Unable to read data from value: {0:s} with error: {1:s}'.format(
                self._pyregf_value.name, exception))

    # TODO: Add support for REG_MULTI_SZ to pyregf.
    elif self._pyregf_value.type == definitions.REG_MULTI_SZ:
      if self._pyregf_value.data is None:
        return []

      try:
        utf16_string = self._pyregf_value.data.decode(u'utf-16-le')
        return filter(None, utf16_string.split(u'\x00'))

      except (IOError, UnicodeError) as exception:
        raise errors.WinRegistryValueError(
            u'Unable to read data from value: {0:s} with error: {1:s}'.format(
                self._pyregf_value.name, exception))

    return self._pyregf_value.data

  @property
  def data_type(self):
    """Numeric value that contains the data type."""
    return self._pyregf_value.type

  @property
  def name(self):
    """The name of the value."""
    return self._pyregf_value.name

  @property
  def offset(self):
    """The offset of the value within the Windows Registry file."""
    return self._pyregf_value.offset

  @property
  def raw_data(self):
    """The value data as a byte string.

    Raises:
      WinRegistryValueError: if the value data cannot be read.
    """
    try:
      return self._pyregf_value.data
    except IOError as exception:
      raise errors.WinRegistryValueError(
          u'Unable to read data from value: {0:s} with error: {1:s}'.format(
              self._pyregf_value.name, exception))


class REGFWinRegistryFile(interface.WinRegistryFile):
  """Implementation of a Windows Registry file using pyregf."""

  def __init__(self, ascii_codepage=u'cp1252', key_path_prefix=u''):
    """Initializes the Windows Registry file.

    Args:
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).
      key_path_prefix: optional Windows Registry key path prefix.
    """
    super(REGFWinRegistryFile, self).__init__(
        ascii_codepage=ascii_codepage, key_path_prefix=key_path_prefix)
    self._file_object = None
    self._regf_file = pyregf.file()
    self._regf_file.set_ascii_codepage(ascii_codepage)

  def Close(self):
    """Closes the Windows Registry file."""
    self._regf_file.close()
    self._file_object.close()
    self._file_object = None

  def GetKeyByPath(self, key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path: the Windows Registry key path.

    Returns:
      A Registry key (instance of WinRegistryKey) or None if not available.
    """
    key_path_upper = key_path.upper()
    if key_path_upper.startswith(self._key_path_prefix_upper):
      relative_key_path = key_path[self._key_path_prefix_length:]
    elif key_path.startswith(self._KEY_PATH_SEPARATOR):
      relative_key_path = key_path
      key_path = u''.join([self._key_path_prefix, key_path])
    else:
      return

    try:
      regf_key = self._regf_file.get_key_by_path(relative_key_path)
    except IOError:
      regf_key = None
    if not regf_key:
      return

    return REGFWinRegistryKey(regf_key, key_path=key_path)

  def GetRootKey(self):
    """Retrieves the root key.

    Returns:
      The Windows Registry root key (instance of WinRegistryKey) or
      None if not available.
    """
    regf_key = self._regf_file.get_root_key()
    if not regf_key:
      return

    return REGFWinRegistryKey(regf_key, key_path=self._key_path_prefix)

  def Open(self, file_object):
    """Opens the Windows Registry file using a file-like object.

    Args:
      file_object: the file-like object.

    Returns:
      A boolean containing True if successful or False if not.
    """
    self._file_object = file_object
    self._regf_file.open_file_object(self._file_object)
    return True
