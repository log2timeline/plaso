# -*- coding: utf-8 -*-
"""Classes for Windows Registry access."""

import logging

from dfvfs.helpers import file_system_searcher

from plaso.dfwinreg import definitions
from plaso.dfwinreg import interface
from plaso.dfwinreg import path_expander
from plaso.dfwinreg import regf


class WinRegistryFileMapping(object):
  """Class that defines a Windows Registry file mapping.

  Attributes:
    key_path_prefix: the Windows Registry key path prefix.
    windows_path: the Windows path to the Windows Registry file.
  """

  def __init__(self, key_path_prefix, windows_path):
    """Initializes the Windows Registry file mapping.

    Args:
      key_path_prefix: the Windows Registry key path prefix.
      windows_path: the Windows path to the Windows Registry file.
    """
    super(WinRegistryFileMapping, self).__init__()
    self.key_path_prefix = key_path_prefix.upper()
    self.windows_path = windows_path


class WinRegistry(object):
  """Class to provide a uniform way to access the Windows Registry."""

  _KEY_PATHS_PER_REGISTRY_TYPE = {
      definitions.REGISTRY_FILE_TYPE_NTUSER: frozenset([
          u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer']),
      definitions.REGISTRY_FILE_TYPE_SAM: frozenset([
          u'\\SAM\\Domains\\Account\\Users']),
      definitions.REGISTRY_FILE_TYPE_SECURITY: frozenset([
          u'\\Policy\\PolAdtEv']),
      definitions.REGISTRY_FILE_TYPE_SOFTWARE: frozenset([
          u'\\Microsoft\\Windows\\CurrentVersion\\App Paths']),
      definitions.REGISTRY_FILE_TYPE_SYSTEM: frozenset([
          u'\\Select']),
      definitions.REGISTRY_FILE_TYPE_USRCLASS: frozenset([
          u'\\Local Settings\\Software\\Microsoft\\Windows\\CurrentVersion']),
  }

  _PATH_SEPARATOR = u'\\'

  # TODO: refactor to use %SystemRoot% and %UserProfile% instead.
  # TODO: refactor to use Windows paths.

  _REGISTRY_FILE_MAPPINGS_9X = [
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE',
          u'{systemroot}/SYSTEM.DAT'),
      WinRegistryFileMapping(
          u'HKEY_USERS',
          u'{systemroot}/USER.DAT'),
  ]

  _REGISTRY_FILE_MAPPINGS_NT = [
      WinRegistryFileMapping(
          u'HKEY_CURRENT_USER',
          u'{userprofile}/NTUSER.DAT'),
      WinRegistryFileMapping(
          u'HKEY_CURRENT_USER\\Software\\Classes',
          u'{userprofile}/AppData/Local/Microsoft/Windows/UsrClass.dat'),
      WinRegistryFileMapping(
          u'HKEY_CURRENT_USER\\Software\\Classes',
          (u'{userprofile}/Local Settings/Application Data/Microsoft/'
           u'Windows/UsrClass.dat')),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\SAM',
          u'{systemroot}/System32/config/SAM'),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\Security',
          u'{systemroot}/System32/config/SECURITY'),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\Software',
          u'{systemroot}/System32/config/SOFTWARE'),
      WinRegistryFileMapping(
          u'HKEY_LOCAL_MACHINE\\System',
          u'{systemroot}/System32/config/SYSTEM'),
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
    for key_path_prefix, registry_file in iter(self._registry_files.items()):
      self._registry_files[key_path_prefix] = None
      if registry_file:
        registry_file.Close()

  def _GetCachedFileByPath(self, safe_key_path):
    """Retrieves a cached Windows Registry file for a specific path.

    Args:
      safe_key_path: the Windows Registry key path, in upper case with
                     a resolved root key alias.

    Returns:
      A tuple of the key path prefix and the corresponding Windows Registry
      file object (instance of WinRegistryFile) or None if not available.
    """
    longest_key_path_prefix = u''
    longest_key_path_prefix_length = len(longest_key_path_prefix)
    for key_path_prefix in self._registry_files.iterkeys():
      if safe_key_path.startswith(key_path_prefix):
        key_path_prefix_length = len(key_path_prefix)
        if key_path_prefix_length > longest_key_path_prefix_length:
          longest_key_path_prefix = key_path_prefix
          longest_key_path_prefix_length = key_path_prefix_length

    if not longest_key_path_prefix:
      return None, None

    registry_file = self._registry_files.get(longest_key_path_prefix, None)
    return longest_key_path_prefix, registry_file

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

  def _GetFileByPath(self, safe_key_path):
    """Retrieves a Windows Registry file for a specific path.

    Args:
      safe_key_path: the Windows Registry key path, in upper case with
                     a resolved root key alias.

    Returns:
      A tuple of the key path prefix and the corresponding Windows Registry
      file object (instance of WinRegistryFile) or None if not available.
    """
    if not self._registry_file_reader:
      return None, None

    # TODO: handle HKEY_USERS in both 9X and NT.

    key_path_prefix, registry_file = self._GetCachedFileByPath(safe_key_path)
    if not registry_file:
      for mapping in self._GetFileMappingsByPath(safe_key_path):
        registry_file = self.OpenFile(mapping.windows_path)
        if registry_file:
          if not key_path_prefix:
            key_path_prefix = mapping.key_path_prefix

          # Note make sure the key path prefix is stored in upper case.
          self._registry_files[key_path_prefix] = registry_file
          break

    return key_path_prefix, registry_file

  def _GetFileMappingsByPath(self, safe_key_path):
    """Retrieves the Windows Registry file mappings for a specific path.

    Args:
      safe_key_path: the Windows Registry key path, in upper case with
                     a resolved root key alias.

    Yields:
      Registry file mapping objects (instances of WinRegistryFileMapping).
    """
    candidate_mappings = []
    for mapping in self._REGISTRY_FILE_MAPPINGS_NT:
      if safe_key_path.startswith(mapping.key_path_prefix):
        candidate_mappings.append(mapping)

    # Sort the candidate mappings by longest (most specific) match first.
    candidate_mappings.sort(
        key=lambda mapping: len(mapping.key_path_prefix), reverse=True)
    for mapping in candidate_mappings:
      yield mapping

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
    root_key_path = self._ROOT_KEY_ALIASES.get(root_key_path, root_key_path)

    if root_key_path not in self._ROOT_KEYS:
      raise RuntimeError(u'Unsupported root key: {0:s}'.format(root_key_path))

    key_path = self._PATH_SEPARATOR.join([root_key_path, key_path])
    safe_key_path = key_path.upper()

    key_path_prefix, registry_file = self._GetFileByPath(safe_key_path)
    if not registry_file:
      return

    if not safe_key_path.startswith(key_path_prefix):
      raise RuntimeError(u'Key path prefix mismatch.')

    for virtual_key_path, virtual_key_callback in self._VIRTUAL_KEYS:
      if key_path.startswith(virtual_key_path):
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

    key_path = key_path[len(key_path_prefix):]
    # TODO: wrap key to hide implementation specifics.
    return registry_file.GetKeyByPath(key_path)

  def GetRegistryFileType(self, registry_file):
    """Determines the Windows Registry type based on keys present in the file.

    Args:
      registry_file: the Windows Registry file object (instance of
                     WinRegistyFile).

    Returns:
      The Windows Registry file type, e.g. NTUSER, SOFTWARE.
    """
    registry_file_type = definitions.REGISTRY_FILE_TYPE_UNKNOWN
    for registry_file_type, key_paths in iter(
        self._KEY_PATHS_PER_REGISTRY_TYPE.items()):

      # If all key paths are found we consider the file to match a certain
      # Registry type.
      match = True
      for key_path in key_paths:
        if not registry_file.GetKeyByPath(key_path):
          match = False

      if match:
        break

    return registry_file_type

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


class SearcherWinRegistryFileReader(interface.WinRegistryFileReader):
  """A file system searcher-based Windows Registry file reader."""

  def __init__(self, searcher, pre_obj=None):
    """Initializes a Windows Registry file reader object.

    Args:
      searcher: the file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      pre_obj: optional preprocess object that contains stored values from
               the image.
    """
    super(SearcherWinRegistryFileReader, self).__init__()
    self._file_path_expander = path_expander.WinRegistryKeyPathExpander()
    self._pre_obj = pre_obj
    self._searcher = searcher

  def _FindPathSpec(self, path):
    """Searches for a path specification.

    Args:
      path: the path of the Windows Registry file.

    Returns:
      A path specification (instance of dfvfs.PathSpec) of
      the Windows Registry file.

    Raises:
      IOError: If the Windows Registry file cannot be found.
    """
    path, _, filename = path.rpartition(u'/')

    # TODO: determine why this first find is used add comment or remove.
    # It does not appear to help with making sure path segment separate
    # is correct.
    find_spec = file_system_searcher.FindSpec(
        location=path, case_sensitive=False)
    path_specs = list(self._searcher.Find(find_specs=[find_spec]))

    if not path_specs or len(path_specs) != 1:
      raise IOError(
          u'Unable to find directory: {0:s}'.format(path))

    relative_path = self._searcher.GetRelativePath(path_specs[0])
    if not relative_path:
      raise IOError(u'Unable to determine relative path of: {0:s}'.format(path))

    # The path is split in segments to make it path segement separator
    # independent (and thus platform independent).
    path_segments = self._searcher.SplitPath(relative_path)
    path_segments.append(filename)

    find_spec = file_system_searcher.FindSpec(
        location=path_segments, case_sensitive=False)
    path_specs = list(self._searcher.Find(find_specs=[find_spec]))

    if not path_specs:
      raise IOError(
          u'Unable to find file: {0:s} in directory: {1:s}'.format(
              filename, relative_path))

    if len(path_specs) != 1:
      raise IOError((
          u'Find for file: {0:s} in directory: {1:s} returned {2:d} '
          u'results.').format(filename, relative_path, len(path_specs)))

    if not relative_path:
      raise IOError(
          u'Missing file: {0:s} in directory: {1:s}'.format(
              filename, relative_path))

    return path_specs[0]

  def Open(self, path, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specificed by the path.

    Args:
      path: the path of the Windows Registry file.
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    try:
      # TODO: do not pass the full pre_obj here but just
      # the necessary values.
      expanded_path = self._file_path_expander.ExpandPath(
          path, pre_obj=self._pre_obj)

    except KeyError as exception:
      logging.warning(
          u'Unable to expand path: {0:s} with error: {1:s}'.format(
              path, exception))
      expanded_path = path

    path_spec = self._FindPathSpec(expanded_path)
    if not path_spec:
      return

    file_entry = self._searcher.GetFileEntryByPathSpec(path_spec)
    if file_entry is None:
      return

    file_object = file_entry.GetFileObject()
    if file_object is None:
      return

    registry_file = regf.REGFWinRegistryFile(ascii_codepage=ascii_codepage)
    try:
      registry_file.Open(file_object)
    except IOError as exception:
      logging.warning((
          u'Unable to open Windows Registry file: {0:s} with error: '
          u'{1:s}').format(path, exception))
      file_object.close()
      return

    return registry_file


class SingleWinRegistryFileReader(interface.WinRegistryFileReader):
  """A single file Windows Registry file reader."""

  def __init__(self, file_object):
    """Initializes a Windows Registry file reader object.

    Args:
      file_object: the Windows Registry file-like object.
    """
    super(SingleWinRegistryFileReader, self).__init__()
    self._file_object = file_object

  def Open(self, unused_path, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specificed by the path.

    Args:
      path: the path of the Windows Registry file.
      ascii_codepage: optional ASCII string codepage. The default is cp1252
                      (or windows-1252).

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    registry_file = regf.REGFWinRegistryFile(ascii_codepage=ascii_codepage)
    try:
      registry_file.Open(self._file_object)
    except IOError as exception:
      logging.warning(
          u'Unable to open Windows Registry file with error: {0:s}'.format(
              exception))
      return

    return registry_file
