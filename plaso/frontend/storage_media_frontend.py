# -*- coding: utf-8 -*-
"""The storage media front-end."""

import os

from dfvfs.helpers import source_scanner
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.resolver import context

from plaso.frontend import frontend
from plaso.lib import errors


class StorageMediaFrontend(frontend.Frontend):
  """Class that implements a front-end with storage media support."""

  def __init__(self):
    """Initializes the front-end object."""
    super(StorageMediaFrontend, self).__init__()
    self._resolver_context = context.Context()
    self._scan_context = source_scanner.SourceScannerContext()
    self._source_scanner = source_scanner.SourceScanner()

  # TODO: remove this when support to handle multiple partitions is added.
  def GetSourcePathSpec(self):
    """Retrieves the source path specification.

    Returns:
      The source path specification (instance of dfvfs.PathSpec) or None.
    """
    if self._scan_context and self._scan_context.last_scan_node:
      return self._scan_context.last_scan_node.path_spec

  def ScanSource(self, source_path):
    """Scans the source path for volume and file systems.

    Args:
      source_path: the path of the source device, directory or file.

    Returns:
      The scan context (instance of dfvfs.ScanContext).

    Raises:
      SourceScannerError: if the format of or within the source is
                           not supported or the source does not exist.
    """
    if (not source_path.startswith(u'\\\\.\\') and
        not os.path.exists(source_path)):
      raise errors.SourceScannerError(
          u'No such device, file or directory: {0:s}.'.format(source_path))

    # Use the dfVFS source scanner to do the actual scanning.
    self._scan_context.OpenSourcePath(source_path)

    try:
      self._source_scanner.Scan(self._scan_context)
    except dfvfs_errors.BackEndError as exception:
      raise errors.SourceScannerError(
          u'Unable to scan source, with error: {0:s}'.format(exception))

    return self._scan_context

  def SourceIsDirectory(self):
    """Determines if the source is a directory.

    Returns:
      True if the source is a directory, False if not.
    """
    return self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_DIRECTORY]

  def SourceIsFile(self):
    """Determines if the source is a file.

    Returns:
      True if the source is a file, False if not.
    """
    return self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_FILE]

  def SourceIsStorageMediaImage(self):
    """Determines if the source is a storage media image.

    Returns:
      True if the source is a storage media image, False if not.
    """
    return self._scan_context.source_type in [
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_DEVICE,
        self._scan_context.SOURCE_TYPE_STORAGE_MEDIA_IMAGE]
