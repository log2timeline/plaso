# -*- coding: utf-8 -*-
"""Classes for Windows Registry access."""

import logging

from dfvfs.helpers import windows_path_resolver
from dfvfs.resolver import resolver

from plaso.dfwinreg import interface
from plaso.dfwinreg import regf


class WinRegistryFileMapping(object):
  """Class that defines a Windows Registry file mapping.

  Attributes:
    key_path_prefix: the Windows Registry key path prefix.
    unique_key_paths: list of key paths unique to the Windows Registry file.
    windows_path: the Windows path to the Windows Registry file. E.g.
                  C:\\Windows\\System32\\config\\SYSTEM
  """

  def __init__(self, key_path_prefix, windows_path, unique_key_paths):
    """Initializes the Windows Registry file mapping.

    Args:
      key_path_prefix: the Windows Registry key path prefix.
      windows_path: the Windows path to the Windows Registry file. E.g.
                    C:\\Windows\\System32\\config\\SYSTEM
      unique_key_paths: list of key paths unique to the Windows Registry file.
    """
    super(WinRegistryFileMapping, self).__init__()
    self.key_path_prefix = key_path_prefix
    self.unique_key_paths = unique_key_paths
    self.windows_path = windows_path


class WinRegistry(object):
  """Class to provide a uniform way to access the Windows Registry."""

  _PATH_SEPARATOR = u'\\'

  _REGISTRY_FILE_MAPPINGS_9X = [
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE',
          u'%SystemRoot%\\SYSTEM.DAT',
          []),
      WinRegistryFileMapping(
          u'HKEY_USERS',
          u'%SystemRoot%\\USER.DAT',
          []),
  ]

  _REGISTRY_FILE_MAPPINGS_NT = [
      WinRegistryFileMapping(
          u'HKEY_CURRENT_USER',
          u'%UserProfile%\\NTUSER.DAT',
          [u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer']),
      WinRegistryFileMapping(
          u'HKEY_CURRENT_USER\\Software\\Classes',
          u'%UserProfile%\\AppData\\Local\\Microsoft\\Windows\\UsrClass.dat',
          [u'\\Local Settings\\Software\\Microsoft\\Windows\\CurrentVersion']),
      WinRegistryFileMapping(
          u'HKEY_CURRENT_USER\\Software\\Classes',
          (u'%UserProfile%\\Local Settings\\Application Data\\Microsoft\\'
           u'Windows\\UsrClass.dat'),
          []),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\SAM',
          u'%SystemRoot%\\System32\\config\\SAM',
          [u'\\SAM\\Domains\\Account\\Users']),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\Security',
          u'%SystemRoot%\\System32\\config\\SECURITY',
          [u'\\Policy\\PolAdtEv']),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\Software',
          u'%SystemRoot%\\System32\\config\\SOFTWARE',
          [u'\\Microsoft\\Windows\\CurrentVersion\\App Paths']),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\System',
          u'%SystemRoot%\\System32\\config\\SYSTEM',
          [u'\\Select'])
  ]

  _ROOT_KEY_ALIASES = {
      u'HKCC': u'HKEY_CURRENT_CONFIG',
      u'HKCR': u'HKEY_CLASSES_ROOT',
      u'HKCU': u'HKEY_CURRENT_USER',
      u'HKLM': u'HKEY_LOCAL_MACHINE',
      u'HKU': u'HKEY_USERS',
  }

  _ROOT_KEYS = frozenset([
      u'HKEY_CLASSES_ROOT',
      u'HKEY_CURRENT_CONFIG',
      u'HKEY_CURRENT_USER',
      u'HKEY_DYN_DATA',
      u'HKEY_LOCAL_MACHINE',
      u'HKEY_PERFORMANCE_DATA',
      u'HKEY_USERS',
  ])

  # TODO: add support for HKEY_USERS.
  _VIRTUAL_KEYS = [
      (u'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet',
       u'_GetCurrentControlSet')]

  # TODO: remove. This definition is a left over from previous times
  # where on instantiation the backend was defined. This has been superseded
  # by the registry_file_reader.
  BACKEND_PYREGF = 1

  # TODO: replace backend by registry_file_reader.
  def __init__(
      self, ascii_codepage=u'cp1252', backend=1, registry_file_reader=None):
    """Initializes the Windows Registry.

    Args:
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).
      backend: The back-end to use to read the Windows Registry structures, the
               default is 1 (pyregf).
      registry_file_reader: optional Windows Registry file reader (instance of
                            WinRegistryFileReader). The default is None.
    """
    super(WinRegistry, self).__init__()
    self._ascii_codepage = ascii_codepage
    self._backend = backend
    self._registry_file_reader = registry_file_reader
    self._registry_files = {}

  def __del__(self):
    """Cleans up the Windows Registry object."""
    for key_path_prefix_upper, registry_file in iter(
        self._registry_files.items()):
      self._registry_files[key_path_prefix_upper] = None
      if registry_file:
        registry_file.Close()

  def _GetCachedFileByPath(self, key_path_upper):
    """Retrieves a cached Windows Registry file for a specific path.

    Args:
      key_path_upper: the Windows Registry key path, in upper case with
                      a resolved root key alias.

    Returns:
      A tuple of the key path prefix and the corresponding Windows Registry
      file object (instance of WinRegistryFile) or None if not available.
    """
    longest_key_path_prefix_upper = u''
    longest_key_path_prefix_length = len(longest_key_path_prefix_upper)
    for key_path_prefix_upper in iter(self._registry_files.keys()):
      if key_path_upper.startswith(key_path_prefix_upper):
        key_path_prefix_length = len(key_path_prefix_upper)
        if key_path_prefix_length > longest_key_path_prefix_length:
          longest_key_path_prefix_upper = key_path_prefix_upper
          longest_key_path_prefix_length = key_path_prefix_length

    if not longest_key_path_prefix_upper:
      return None, None

    registry_file = self._registry_files.get(
        longest_key_path_prefix_upper, None)
    return longest_key_path_prefix_upper, registry_file

  def _GetCurrentControlSet(self):
    """Virtual key callback to determine the current control set.

    Returns:
      The resolved key path for the current control set key or
      None if unable to resolve.
    """
    select_key_path = u'HKEY_LOCAL_MACHINE\\System\\Select'
    select_key = self.GetKeyByPath(select_key_path)
    if not select_key:
      return

    # To determine the current control set check:
    # 1. The "Current" value.
    # 2. The "Default" value.
    # 3. The "LastKnownGood" value.
    control_set = None
    for value_name in [u'Current', u'Default', u'LastKnownGood']:
      value = select_key.GetValueByName(value_name)
      if not value or not value.DataIsInteger():
        continue

      control_set = value.data
      # If the control set is 0 then we need to check the other values.
      if control_set > 0 or control_set <= 999:
        break

    if not control_set or control_set <= 0 or control_set > 999:
      return

    return u'HKEY_LOCAL_MACHINE\\System\\ControlSet{0:03d}'.format(control_set)

  def _GetFileByPath(self, key_path_upper):
    """Retrieves a Windows Registry file for a specific path.

    Args:
      key_path_upper: the Windows Registry key path, in upper case with
                      a resolved root key alias.

    Returns:
      A tuple of the upper case key path prefix and the corresponding
      Windows Registry file object (instance of WinRegistryFile) or
      None if not available.
    """
    if not self._registry_file_reader:
      return None, None

    # TODO: handle HKEY_USERS in both 9X and NT.

    key_path_prefix, registry_file = self._GetCachedFileByPath(key_path_upper)
    if not registry_file:
      for mapping in self._GetFileMappingsByPath(key_path_upper):
        registry_file = self.OpenFile(mapping.windows_path)
        if not registry_file:
          continue

        if not key_path_prefix:
          key_path_prefix = mapping.key_path_prefix

        self._MapFile(key_path_prefix, registry_file)
        key_path_prefix = key_path_prefix.upper()
        break

    return key_path_prefix, registry_file

  def _GetFileMappingsByPath(self, key_path_upper):
    """Retrieves the Windows Registry file mappings for a specific path.

    Args:
      key_path_upper: the Windows Registry key path, in upper case with
                      a resolved root key alias.

    Yields:
      Registry file mapping objects (instances of WinRegistryFileMapping).
    """
    candidate_mappings = []
    for mapping in self._REGISTRY_FILE_MAPPINGS_NT:
      if key_path_upper.startswith(mapping.key_path_prefix.upper()):
        candidate_mappings.append(mapping)

    # Sort the candidate mappings by longest (most specific) match first.
    candidate_mappings.sort(
        key=lambda mapping: len(mapping.key_path_prefix), reverse=True)
    for mapping in candidate_mappings:
      yield mapping

  def _MapFile(self, key_path_prefix, registry_file):
    """Maps the Windows Registry file to a specific key path prefix.

    Args:
      key_path_prefix: the key path prefix.
      registry_file: a Windows Registry file (instance of
                     dfwinreg.WinRegistryFile).
    """
    self._registry_files[key_path_prefix.upper()] = registry_file
    registry_file.SetKeyPathPrefix(key_path_prefix)

  # TODO: still needed?
  def ExpandKeyPath(self, key_path, path_attributes):
    """Expand a Windows Registry key path based on path attributes.

     A Windows Registry key path may contain path attributes. A path
     attribute is defined as anything within a curly bracket, e.g.
     "\\System\\{my_attribute}\\Path\\Keyname".

     If the path attribute my_attribute is defined it's value will be replaced
     with the attribute name, e.g. "\\System\\MyValue\\Path\\Keyname".

     If the Windows Registry key path needs to have curly brackets in the path
     then they need to be escaped with another curly bracket, e.g.
     "\\System\\{my_attribute}\\{{123-AF25-E523}}\\KeyName". In this
     case the {{123-AF25-E523}} will be replaced with "{123-AF25-E523}".

    Args:
      key_path: the Windows Registry key path before being expanded.
      path_attributes: a dictionary containing the path attributes.

    Returns:
      A Windows Registry key path that's expanded based on attribute values.

    Raises:
      KeyError: If an attribute name is in the key path not set in
                the preprocessing object a KeyError will be raised.
    """
    try:
      expanded_key_path = key_path.format(**path_attributes)
    except KeyError as exception:
      raise KeyError(u'Unable to expand key path with error: {0:s}'.format(
          exception))

    if not expanded_key_path:
      raise KeyError(u'Unable to expand key path.')

    return expanded_key_path

  def GetKeyByPath(self, key_path):
    """Retrieves the key for a specific path.

    Args:
      key_path: the Windows Registry key path.

    Returns:
      A Windows Registry key (instance of WinRegistryKey) or None if
      not available.

    Raises:
      RuntimeError: if the root key is not supported.
    """
    root_key_path, _, key_path = key_path.partition(self._PATH_SEPARATOR)

    # Resolve a root key alias.
    root_key_path = root_key_path.upper()
    root_key_path = self._ROOT_KEY_ALIASES.get(root_key_path, root_key_path)

    if root_key_path not in self._ROOT_KEYS:
      raise RuntimeError(u'Unsupported root key: {0:s}'.format(root_key_path))

    key_path = self._PATH_SEPARATOR.join([root_key_path, key_path])
    key_path_upper = key_path.upper()

    key_path_prefix_upper, registry_file = self._GetFileByPath(key_path_upper)
    if not registry_file:
      return

    if not key_path_upper.startswith(key_path_prefix_upper):
      raise RuntimeError(u'Key path prefix mismatch.')

    for virtual_key_path, virtual_key_callback in self._VIRTUAL_KEYS:
      if key_path_upper.startswith(virtual_key_path.upper()):
        callback_function = getattr(self, virtual_key_callback)
        resolved_key_path = callback_function()
        if not resolved_key_path:
          raise RuntimeError(u'Unable to resolve virtual key: {0:s}.'.format(
              virtual_key_path))

        virtual_key_path_length = len(virtual_key_path)
        if key_path[virtual_key_path_length] == self._PATH_SEPARATOR:
          virtual_key_path_length += 1

        key_path = self._PATH_SEPARATOR.join([
            resolved_key_path, key_path[virtual_key_path_length:]])

    key_path = key_path[len(key_path_prefix_upper):]
    return registry_file.GetKeyByPath(key_path)

  def GetRegistryFileMapping(self, registry_file):
    """Determines the Registry file mapping based on the content fo the file.

    Args:
      registry_file: the Windows Registry file object (instance of
                     WinRegistyFile).

    Returns:
      The key path prefix or an empty string.

    Raises:
      RuntimeError: if there are multiple matching mappings and
                    the correct mapping cannot be resolved.
    """
    candidate_mappings = []
    for mapping in self._REGISTRY_FILE_MAPPINGS_NT:
      if not mapping.unique_key_paths:
        continue

      # If all unique key paths are found consider the file to match.
      match = True
      for key_path in mapping.unique_key_paths:
        registry_key = registry_file.GetKeyByPath(key_path)
        if not registry_key:
          match = False

      if match:
        candidate_mappings.append(mapping)

    if not candidate_mappings:
      return u''

    if len(candidate_mappings) == 1:
      return candidate_mappings[0].key_path_prefix

    key_path_prefixes = frozenset([
        mapping.key_path_prefix for mapping in candidate_mappings])

    expected_key_path_prefixes = frozenset([
        u'HKEY_CURRENT_USER',
        u'HKEY_CURRENT_USER\\Software\\Classes'])

    if key_path_prefixes == expected_key_path_prefixes:
      return u'HKEY_CURRENT_USER'

    raise RuntimeError(u'Unable to resolve Windows Registry file mapping.')

  # TODO: deprecate direct usage of this method.
  def OpenFile(self, path):
    """Opens a Windows Registry file.

    Args:
      path: the Windows Registry file path.

    Returns:
      A corresponding Windows Registry file object (instance of
      WinRegistryFile) or None if not available.
    """
    return self._registry_file_reader.Open(
        path, ascii_codepage=self._ascii_codepage)

  # TODO: deprecate usage of this method.
  def OpenFileEntry(self, file_entry):
    """Opens a Windows Registry file entry.

    Args:
      file_entry: the file entry (instance of dfvfs.FileEntry).

    Returns:
      A corresponding Windows Registry file object (instance of
      WinRegistryFile) or None if not available.
    """
    registry_file = regf.REGFWinRegistryFile()
    file_object = file_entry.GetFileObject()

    try:
      registry_file.Open(file_object)
    except IOError:
      file_object.close()
      registry_file = None

    return registry_file


class PathSpecWinRegistryFileReader(interface.WinRegistryFileReader):
  """A single path specification Windows Registry file reader."""

  def __init__(self, path_spec):
    """Initializes a Windows Registry file reader object.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec).
    """
    super(PathSpecWinRegistryFileReader, self).__init__()
    self._path_spec = path_spec

  def _OpenPathSpec(self, path_spec, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specified by the path specification.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec).
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    if not path_spec:
      return

    file_entry = resolver.Resolver.OpenFileEntry(path_spec)
    if file_entry is None:
      return

    file_object = file_entry.GetFileObject()
    if file_object is None:
      return

    registry_file = regf.REGFWinRegistryFile(ascii_codepage=ascii_codepage)
    try:
      registry_file.Open(file_object)
    except IOError as exception:
      logging.warning(
          u'Unable to open Windows Registry file with error: {0:s}'.format(
              exception))
      file_object.close()
      return

    return registry_file

  def Open(self, path, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path: the path of the Windows Registry file.
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    return self._OpenPathSpec(self._path_spec)


class SearcherWinRegistryFileReader(interface.WinRegistryFileReader):
  """A file system searcher-based Windows Registry file reader."""

  def __init__(self, file_system, mount_point, path_attributes=None):
    """Initializes a Windows Registry file reader object.

    Args:
      file_system: the file system object (instance of vfs.FileSystem).
      mount_point: the mount point path specification (instance of
                   path.PathSpec).
      path_attributes: optional dictionary of path attributes.
    """
    super(SearcherWinRegistryFileReader, self).__init__()
    self._path_resolver = windows_path_resolver.WindowsPathResolver(
        file_system, mount_point)

    if path_attributes:
      for attribute_name, attribute_value in iter(path_attributes.items()):
        # TODO: fix the call to this class and make sure only relevant
        # values are passed.
        if attribute_name == u'systemroot':
          self._path_resolver.SetEnvironmentVariable(
              u'SystemRoot', attribute_value)

  def _OpenPathSpec(self, path_spec, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specified by the path specification.

    Args:
      path_spec: a path specification (instance of dfvfs.PathSpec).
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    if not path_spec:
      return

    file_object = resolver.Resolver.OpenFileObject(path_spec)
    if file_object is None:
      return

    # TODO: fix empty file object.
    registry_file = regf.REGFWinRegistryFile(ascii_codepage=ascii_codepage)
    try:
      registry_file.Open(file_object)
    except IOError as exception:
      logging.warning(
          u'Unable to open Windows Registry file with error: {0:s}'.format(
              exception))
      file_object.close()
      return

    return registry_file

  def Open(self, path, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path: the path of the Windows Registry file.
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    path_spec = self._path_resolver.ResolvePath(path)
    if path_spec is None:
      return

    return self._OpenPathSpec(path_spec)


class FileObjectWinRegistryFileReader(interface.WinRegistryFileReader):
  """A single file-like object Windows Registry file reader."""

  def Open(self, file_object, ascii_codepage=u'cp1252'):
    """Opens a Windows Registry file-like object.

    Args:
      file_object: the Windows Registry file-like object.
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    registry_file = regf.REGFWinRegistryFile(ascii_codepage=ascii_codepage)
    try:
      registry_file.Open(file_object)
    except IOError as exception:
      logging.warning(
          u'Unable to open Windows Registry file with error: {0:s}'.format(
              exception))
      return

    return registry_file
