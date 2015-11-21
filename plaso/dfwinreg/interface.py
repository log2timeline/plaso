# -*- coding: utf-8 -*-
"""The interface for Windows Registry objects."""

import abc

from plaso.dfwinreg import definitions


class WinRegistryFile(object):
  """Class that defines a Windows Registry file."""

  _KEY_PATH_SEPARATOR = u'\\'

  def __init__(self, ascii_codepage=u'cp1252', key_path_prefix=u''):
    """Initializes the Windows Registry file.

    Args:
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).
      key_path_prefix: optional Windows Registry key path prefix.
    """
    super(WinRegistryFile, self).__init__()
    self._ascii_codepage = ascii_codepage
    self._key_path_prefix = key_path_prefix
    self._key_path_prefix_length = len(key_path_prefix)
    self._key_path_prefix_upper = key_path_prefix.upper()

  def _SplitKeyPath(self, path):
    """Splits the key path into path segments.

    Args:
      path: a string containing the path.

    Returns:
      A list of path segements without the root path segment, which is an
      empty string.
    """
    # Split the path with the path separator and remove empty path segments.
    return filter(None, path.split(self._KEY_PATH_SEPARATOR))

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
  def GetRootKey(self):
    """Retrieves the root key.

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

  def RecurseKeys(self):
    """Recurses the Windows Registry keys starting with the root key.

    Yields:
      A Windows Registry key (instance of WinRegistryKey).
    """
    root_key = self.GetRootKey()
    if root_key:
      for registry_key in root_key.RecurseKeys():
        yield registry_key

  def SetKeyPathPrefix(self, key_path_prefix):
    """Sets the Window Registry key path prefix.

    Args:
      key_path_prefix: the Windows Registry key path prefix.
    """
    self._key_path_prefix = key_path_prefix
    self._key_path_prefix_length = len(key_path_prefix)
    self._key_path_prefix_upper = key_path_prefix.upper()


class WinRegistryFileReader(object):
  """Class to represent the Windows Registry file reader interface."""

  @abc.abstractmethod
  def Open(self, path, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path: string containing the path of the Windows Registry file. The path
            is a Windows path relative to the root of the file system that
            contains the specfic Windows Registry file. E.g.
            C:\\Windows\\System32\\config\\SYSTEM
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """


class WinRegistryKey(object):
  """Class to represent the Windows Registry key interface."""

  _PATH_SEPARATOR = u'\\'

  def __init__(self, key_path=u''):
    """Initializes a Windows Registry key object.

    Args:
      key_path: optional Windows Registry key path.
    """
    super(WinRegistryKey, self).__init__()
    self._key_path = self._JoinKeyPath([key_path])

  @abc.abstractproperty
  def last_written_time(self):
    """The last written time of the key (contains a FILETIME timestamp)."""

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

  def _JoinKeyPath(self, path_segments):
    """Joins the path segments into key path.

    Args:
      path_segment: list of Windows Registry key path segments.
    """
    # This is an optimized way to combine the path segments into a single path
    # and combine multiple successive path separators to one.

    # Split all the path segments based on the path (segment) separator.
    path_segments = [
        segment.split(self._PATH_SEPARATOR) for segment in path_segments]

    # Flatten the sublists into one list.
    path_segments = [
        element for sublist in path_segments for element in sublist]

    # Remove empty path segments.
    path_segments = filter(None, path_segments)

    key_path = self._PATH_SEPARATOR.join(path_segments)
    if not key_path.startswith(u'HKEY_'):
      key_path = u'{0:s}{1:s}'.format(self._PATH_SEPARATOR, key_path)
    return key_path

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
      A Windows Registry value object (instance of WinRegistryValue) if
      a corresponding value was found or None if not.
    """

  @abc.abstractmethod
  def GetValues(self):
    """Retrieves all values within the key.

    Yields:
      Windows Registry value objects (instances of WinRegistryValue) that
      represent the values stored within the key.
    """

  def RecurseKeys(self):
    """Recurses the subkeys starting with the key.

    Yields:
      A Windows Registry key (instance of WinRegistryKey).
    """
    yield self
    for subkey in self.GetSubkeys():
      for key in subkey.RecurseKeys():
        yield key


class WinRegistryValue(object):
  """Class to represent the Windows Registry value interface."""

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

  _INTEGER_VALUE_TYPES = frozenset([
      definitions.REG_DWORD, definitions.REG_DWORD_BIG_ENDIAN,
      definitions.REG_QWORD])

  _STRING_VALUE_TYPES = frozenset([
      definitions.REG_SZ, definitions.REG_EXPAND_SZ, definitions.REG_LINK])

  @abc.abstractproperty
  def data(self):
    """The value data as a byte string."""

  @abc.abstractproperty
  def data_type(self):
    """Numeric value that contains the data type."""

  @property
  def data_type_string(self):
    """String representation of the data type."""
    return self._DATA_TYPE_STRINGS.get(self.data_type, u'UNKNOWN')

  @abc.abstractproperty
  def name(self):
    """The name of the value."""

  @abc.abstractproperty
  def offset(self):
    """The offset of the value within the Windows Registry file."""

  def DataIsInteger(self):
    """Determines, based on the data type, if the data is an integer.

    The data types considered strings are: REG_DWORD (REG_DWORD_LITTLE_ENDIAN),
    REG_DWORD_BIG_ENDIAN and REG_QWORD.

    Returns:
      True if the data is an integer, false otherwise.
    """
    return self.data_type in [
        definitions.REG_DWORD, definitions.REG_DWORD_BIG_ENDIAN,
        definitions.REG_QWORD]

  def DataIsBinaryData(self):
    """Determines, based on the data type, if the data is binary data.

    The data types considered binary data are: REG_BINARY.

    Returns:
      True if the data is a multi string, false otherwise.
    """
    return self.data_type == definitions.REG_BINARY

  def DataIsMultiString(self):
    """Determines, based on the data type, if the data is a multi string.

    The data types considered multi strings are: REG_MULTI_SZ.

    Returns:
      True if the data is a multi string, false otherwise.
    """
    return self.data_type == definitions.REG_MULTI_SZ

  def DataIsString(self):
    """Determines, based on the data type, if the data is a string.

    The data types considered strings are: REG_SZ and REG_EXPAND_SZ.

    Returns:
      True if the data is a string, false otherwise.
    """
    return self.data_type in [definitions.REG_SZ, definitions.REG_EXPAND_SZ]

  @abc.abstractmethod
  def GetData(self):
    """Retrieves the data.

    Returns:
      The data as a Python type.
    """
