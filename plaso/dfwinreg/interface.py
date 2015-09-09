# -*- coding: utf-8 -*-
"""The interface for Windows Registry related objects."""

import abc


class WinRegistryKey(object):
  """Class to represent the Windows Registry key interface."""

  PATH_SEPARATOR = u'\\'

  def __init__(self, key_path=u''):
    """Initializes a Windows Registry key object.

    Args:
      key_path: the Windows Registry key path.
    """
    super(WinRegistryKey, self).__init__()

    if not key_path:
      key_path = self.PATH_SEPARATOR
    elif not key_path.startswith(self.PATH_SEPARATOR):
      key_path = u'{0:s}{1:s}'.format(self.PATH_SEPARATOR, key_path)
    self._key_path = key_path

  @abc.abstractproperty
  def last_written_timestamp(self):
    """The last written time of the key represented as a timestamp."""

  @abc.abstractproperty
  def name(self):
    """The name of the key."""

  @abc.abstractproperty
  def number_of_subkeys(self):
    """The number of subkeys within the key."""

  @abc.abstractproperty
  def number_of_values(self):
    """The number of values within the key."""

  @abc.abstractproperty
  def offset(self):
    """The offset of the key within the Windows Registry file."""

  @property
  def path(self):
    """The Windows Registry key path."""
    return self._key_path

  @abc.abstractmethod
  def GetSubkeyByName(self, name):
    """Retrieves a subkey by name.

    Args:
      name: The name of the subkey.

    Returns:
      The Windows Registry subkey (instances of WinRegistryKey) or
      None if not found.
    """

  @abc.abstractmethod
  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      Windows Registry key objects (instances of WinRegistryKey) that represent
      the subkeys stored within the key.
    """

  @abc.abstractmethod
  def GetValueByName(self, name):
    """Retrieves a value by name.

    Args:
      name: the name of the value or an empty string for the default value.

    Returns:
      An instance of a Windows Registry value object (instance of
      WinRegistryValue) if a corresponding value was found or None if not.
    """

  @abc.abstractmethod
  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      Windows Registry value objects (instances of WinRegistryValue) that
      represent the values stored within the key.
    """

  # TODO: implement.
  def JoinKeyPath(self, path_segments):

  def RecurseKeys(self):
    """Recurses the Windows Registry keys starting with the root key.

    Yields:
      A Windows Registry key (instance of WinRegistryKey).
    """
    for subkey in self.GetSubkeys():
      for key in subkey.RecurseKeys():
        yield key


class WinRegistryValue(object):
  """Class to represent the Windows Registry value interface."""

  # TODO: move to definitions, currently kept for backwards compatibility.
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

  # TODO: move to definitions, currently kept for backwards compatibility.
  _DATA_TYPE_STRINGS = {
      0: u'REG_NONE',
      1: u'REG_SZ',
      2: u'REG_EXPAND_SZ',
      3: u'REG_BINARY',
      4: u'REG_DWORD_LE',
      5: u'REG_DWORD_BE',
      6: u'REG_LINK',
      7: u'REG_MULTI_SZ',
      8: u'REG_RESOURCE_LIST',
      9: u'REG_FULL_RESOURCE_DESCRIPTOR',
      10: u'REG_RESOURCE_REQUIREMENT_LIST',
      11: u'REG_QWORD'
  }

  def __init__(self):
    """Default constructor for the Windows Registry value."""
    self._data = u''

  @abc.abstractproperty
  def name(self):
    """The name of the value."""

  @abc.abstractproperty
  def offset(self):
    """The offset of the value within the Windows Registry file."""

  @abc.abstractproperty
  def data_type(self):
    """Numeric value that contains the data type."""

  @property
  def data_type_string(self):
    """String representation of the data type."""
    return self._DATA_TYPE_STRINGS.get(self.data_type, u'UNKNOWN')

  @abc.abstractproperty
  def raw_data(self):
    """The value data as a byte string."""

  @abc.abstractproperty
  def data(self):
    """The value data as a native Python object."""

  def DataIsInteger(self):
    """Determines, based on the data type, if the data is an integer.

    The data types considered strings are: REG_DWORD (REG_DWORD_LITTLE_ENDIAN),
    REG_DWORD_BIG_ENDIAN and REG_QWORD.

    Returns:
      True if the data is an integer, false otherwise.
    """
    return self.data_type in [
        self.REG_DWORD, self.REG_DWORD_BIG_ENDIAN, self.REG_QWORD]

  def DataIsString(self):
    """Determines, based on the data type, if the data is a string.

    The data types considered strings are: REG_SZ and REG_EXPAND_SZ.

    Returns:
      True if the data is a string, false otherwise.
    """
    return self.data_type in [self.REG_SZ, self.REG_EXPAND_SZ]

  def DataIsMultiString(self):
    """Determines, based on the data type, if the data is a multi string.

    The data types considered multi strings are: REG_MULTI_SZ.

    Returns:
      True if the data is a multi string, false otherwise.
    """
    return self.data_type == self.REG_MULTI_SZ

  def DataIsBinaryData(self):
    """Determines, based on the data type, if the data is binary data.

    The data types considered binary data are: REG_BINARY.

    Returns:
      True if the data is a multi string, false otherwise.
    """
    return self.data_type == self.REG_BINARY


class WinRegistryFile(object):
  """Class that defines a Windows Registry file."""

  def __init__(self, ascii_codepage=u'cp1252'):
    """Initializes the Windows Registry file.

    Args:
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).
    """
    super(WinRegistryFile, self).__init__()
    self._ascii_codepage = ascii_codepage

  @abc.abstractmethod
  def Close(self):
    """Closes the Windows Registry file."""

  @abc.abstractmethod
  def GetKeyByPath(self, key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path: the Windows Registry key path.

    Returns:
      A Windows Registry key (instance of WinRegistryKey) or None if
      not available.
    """

  @abc.abstractmethod
  def GetRootKey(self, key_path_prefix=u''):
    """Retrieves the root key.

    Args:
      key_path_prefix: optional Windows Registry key path prefix.

    Returns:
      The Windows Registry root key (instance of WinRegistryKey) or
      None if not available.
    """

  @abc.abstractmethod
  def Open(self, file_object):
    """Opens the Windows Registry file using a file-like object.

    Args:
      file_object: the file-like object.

    Returns:
      A boolean containing True if successful or False if not.
    """

  def RecurseKeys(self, key_path_prefix=u''):
    """Recurses the Windows Registry keys starting with the root key.

    Args:
      key_path_prefix: optional Windows Registry key path prefix.

    Yields:
      A Windows Registry key (instance of WinRegistryKey).
    """
    root_key = self.GetRootKey(key_path_prefix=key_path_prefix)
    if root_key:
      for registry_key in root_key.RecurseKeys():
        yield registry_key


class WinRegistryFileReader(object):
  """Class to represent the Windows Registry file reader interface."""

  @abc.abstractmethod
  def Open(self, path, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specificed by the path.

    Args:
      path: the path of the Windows Registry file.
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
