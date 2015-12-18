# -*- coding: utf-8 -*-
"""Shared functions and classes for testing."""

import os
import shutil
import tempfile

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context
from dfvfs.vfs import fake_file_system


# TODO: move majority of this class to dfvfs helpers.
class FakeFileSystemBuilder(object):
  """Class that implements a fake file system builder.

  Attributes:
    file_system: the fake file system (instance of dvfvs.FakeFileSystem).
  """

  _TEST_DATA_PATH = os.path.join(os.getcwd(), u'test_data')

  def __init__(self):
    """Initializes the fake file system builder object."""
    super(FakeFileSystemBuilder, self).__init__()
    resolver_context = context.Context()
    self._file_system = fake_file_system.FakeFileSystem(
        resolver_context)

  @property
  def file_system(self):
    """The file system."""
    return self._file_system

  def _AddParentDirectories(self, path):
    """Adds the parent directories of a path to the fake file system.

    Args:
      path: a string containing the path of the file within the fake
            file system.
    """
    path_segments = self._file_system.SplitPath(path)
    for segment_index in range(len(path_segments)):
      parent_path = self._file_system.JoinPath(path_segments[:segment_index])
      if not self._file_system.FileEntryExistsByPath(parent_path):
        self._file_system.AddFileEntry(
            parent_path,
            file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY)

  def _FileEntryExistsByPath(self, path):
    """Determines if a file entry for a path exists.

    Args:
      path: the path of the file entry.

    Returns:
      Boolean indicating if the file entry exists.
    """
    return path and path in self._file_system.GetPaths()

  def _ReadTestFile(self, path_segments):
    """Reads the data from a test file.

    Args:
      path_segments: a list of strings containing the path segments
                     inside the test data directory.

    Returns:
      Binary string containing the data of the test file or None.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    path = os.path.join(self._TEST_DATA_PATH, *path_segments)

    file_object = open(path, 'rb')
    try:
      file_data = file_object.read()
    except IOError:
      return None
    finally:
      file_object.close()

    return file_data

  def AddFile(self, path, file_data):
    """Adds a "regular" file to the fake file system.

    Args:
      path: a string containing the path of the file within the fake
            file system.
      file_data: a binary string containing the data of the file.

    Raises:
      ValueError: if the path is already set.
    """
    if self._file_system.FileEntryExistsByPath(path):
      raise ValueError(u'Path: {0:s} already set.'.format(path))

    self._AddParentDirectories(path)
    self._file_system.AddFileEntry(path, file_data=file_data)

  def AddSymbolicLink(self, path, linked_path):
    """Adds a symbolic link to the fake file system.

    Args:
      path: a string containing the path of the symbolic link within the fake
            file system.
      linked_path: a string containing the path that is linked.

    Raises:
      ValueError: if the path is already set.
    """
    if self._file_system.FileEntryExistsByPath(path):
      raise ValueError(u'Path: {0:s} already set.'.format(path))

    self._AddParentDirectories(path)
    self._file_system.AddFileEntry(
        path, file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_LINK,
        link_data=linked_path)

  def AddTestFile(self, path, path_segments):
    """Adds a "regular" file from the test data to the fake file system.

    Args:
      path: a string containing the path of the file within the fake
            file system.
      path_segments: a list of strings containing the path segments
                     inside the test data directory.
    """
    file_data = self._ReadTestFile(path_segments)
    self.AddFile(path, file_data)


class TempDirectory(object):
  """Class that implements a temporary directory."""

  def __init__(self):
    """Initializes the temporary directory."""
    super(TempDirectory, self).__init__()
    self.name = u''

  def __enter__(self):
    """Make this work with the 'with' statement."""
    self.name = tempfile.mkdtemp()
    return self.name

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make this work with the 'with' statement."""
    shutil.rmtree(self.name, True)
