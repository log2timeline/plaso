# -*- coding: utf-8 -*-
"""The interface for Windows Registry related objects."""

import abc


class WinRegKey(object):
  """Abstract class to represent the Windows Registry key interface."""

  PATH_SEPARATOR = u'\\'

  @abc.abstractproperty
  def path(self):
    """The path of the key."""

  @abc.abstractproperty
  def name(self):
    """The name of the key."""

  @abc.abstractproperty
  def offset(self):
    """The offset of the key within the Windows Registry file."""

  @abc.abstractproperty
  def last_written_timestamp(self):
    """The last written time of the key represented as a timestamp."""

  @abc.abstractproperty
  def number_of_values(self):
    """The number of values within the key."""

  @abc.abstractmethod
  def GetValue(self, name):
    """Retrieves a value by name.

    Args:
      name: Name of the value or an empty string for the default value.

    Returns:
      An instance of a Windows Registry value object (WinRegValue) if
      a corresponding value was found or None if not.
    """

  @abc.abstractmethod
  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      Windows Registry value objects (instances of WinRegValue) that represent
      the values stored within the key.
    """

  @abc.abstractproperty
  def number_of_subkeys(self):
    """The number of subkeys within the key."""

  @abc.abstractmethod
  def GetSubkey(self, name):
    """Retrive a subkey by name.

    Args:
      name: The relative path of the current key to the desired one.

    Returns:
      The subkey with the relative path of name or None if not found.
    """

  @abc.abstractmethod
  def GetSubkeys(self):
    """Retrieves all subkeys within the key.

    Yields:
      Windows Registry key objects (instances of WinRegKey) that represent
      the subkeys stored within the key.
    """


class WinRegValue(object):
  """Abstract class to represent the Windows Registry value interface."""

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


class WinRegFile(object):
  """Abstract class to represent the Windows Registry file interface."""

  def __init__(self):
    """Default constructor for the Windows Registry file."""
    self._mounted_key_path = u''

  @abc.abstractmethod
  def Open(self, file_object, codepage='cp1252'):
    """Opens the Windows Registry file.

    Args:
      file_object: The file-like object of the Windows Registry file.
      codepage: Optional codepage for ASCII strings, default is cp1252.
    """

  @abc.abstractmethod
  def Close(self):
    """Closes the Windows Registry file."""

  @abc.abstractmethod
  def GetKeyByPath(self, registry_path):
    """Retrieves a specific key defined by the Registry path.

    Args:
      path: the Registry path.

    Returns:
      The key (instance of WinRegKey) if available or None otherwise.
    """
