# -*- coding: utf-8 -*-
"""Classes for Windows Registry access."""

import logging

from dfvfs.helpers import file_system_searcher

from plaso.winreg import path_expander
from plaso.winreg import winpyregf


class WinRegistry(object):
  """Class to provided a uniform way to access the Windows Registry."""

  BACKEND_PYREGF = 1

  # TODO: replace backend by registry_file_reader.
  def __init__(self, backend=1, registry_file_reader=None):
    """Initializes the Windows Registry.

    Args:
      backend: The back-end to use to read the Registry structures, the
               default is 1 (pyregf).
      registry_file_reader: optional Registry file reader (instance of
                            RegistryFileReader). The default is None.
    """
    super(WinRegistry, self).__init__()
    self._backend = backend
    self._registry_file_reader = registry_file_reader
    self._registry_files = {}

  def _OpenFileWithCache(self, file_entry, registry_type, codepage=u'cp1252'):
    """Opens a Registry file and creates an object cache.

    Args:
      file_entry: The file entry object (instance of dfvfs.FileEntry).
      registry_type: The Registry type, eg. "SYSTEM", "NTUSER".
      codepage: Optional codepage for ASCII strings, default is cp1252.

    Raises:
      ValueError: if the back-end is not supported.
    """
    if self._backend != self.BACKEND_PYREGF:
      raise ValueError(u'Unsupported back-end')

    winreg_file = winpyregf.WinPyregfFile()
    winreg_file.OpenWithCache(file_entry, registry_type, codepage=codepage)
    return winreg_file

  def OpenFile(self, file_entry, codepage=u'cp1252'):
    """Opens a Registry file.

    Args:
      file_entry: The file entry object (instance of dfvfs.FileEntry).
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Returns:
      The a Windows Registry file (instance of WinRegFile) if successful
      or None otherwise.

    Raises:
      ValueError: if the back-end is not supported.
    """
    if self._backend != self.BACKEND_PYREGF:
      raise ValueError(u'Unsupported back-end')

    winreg_file = winpyregf.WinPyregfFile()
    winreg_file.Open(file_entry, codepage=codepage)
    return winreg_file

  def OpenFileCached(self, path, filename, registry_type, codepage=u'cp1252'):
    """Opens a Registry file and caches it in the Registry.

    The cached version is returned if the file was opened previously.

    Args:
      path: the path of the Registry file.
      filename: the name of the Registry file.
      registry_type: The Registry type, eg. "SYSTEM", "NTUSER".
      codepage: Optional codepage for ASCII strings, default is cp1252.

    Returns:
      The a Windows Registry file (instance of WinRegFile) if successful
      or None otherwise.

    Raises:
      ValueError: if the Registry file reader is missing.
    """
    if not self._registry_file_reader:
      raise ValueError(u'Missing Registry file reader.')

    filename = filename.upper()
    if filename not in self._registry_files:
      file_entry = self._registry_file_reader.Open(path, filename)
      winreg_file = self._OpenFileWithCache(
          file_entry, registry_type, codepage=codepage)
      self._registry_files[filename] = winreg_file

    return self._registry_files[filename]


class WinRegistryFileReader(object):
  """Class to read a Windows Registry file."""

  def __init__(self, searcher, pre_obj=None):
    """Initializes the Windows Registry file reader.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      pre_obj: Optional preprocess object that contains stored values from
               the image.
    """
    super(WinRegistryFileReader, self).__init__()
    self._file_path_expander = path_expander.WinRegistryKeyPathExpander()
    self._pre_obj = pre_obj
    self._searcher = searcher

  def _FindPathSpec(self, path, filename):
    """Searches for a path specification of the path.

    Args:
      path: the path of the Registry file.
      filename: the name of the Registry file.

    Returns:
      A path specification (instance of dfvfs.PathSpec) of the Registry file.

    Raises:
      IOError: If the preprocessing failed.
    """
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

  def Open(self, path, filename):
    """Opens the Registry file specificed by the path.

    Args:
      path: the path of the Registry file.
      filename: the name of the Registry file.

    Returns:
      The file entry (instance of dfvfs.FileEntry) or None.
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

    path_spec = self._FindPathSpec(expanded_path, filename)
    if not path_spec:
      return

    return self._searcher.GetFileEntryByPathSpec(path_spec)
