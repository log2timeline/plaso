# -*- coding: utf-8 -*-
"""Preprocess plug-in related functions and classes for testing."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.resolver import context
from dfvfs.vfs import fake_file_system


class PreprocessPluginTest(unittest.TestCase):
  """The unit test case for a preprocess plug-in object."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), 'test_data')

  def _BuildSingleFileFakeFileSystem(self, path, file_data):
    """Builds a single file fake file system.

    Args:
      path: The path of the file.
      file_data: The data of the file.

    Returns:
      The fake file system (instance of dvfvs.FakeFileSystem).
    """
    resolver_context = context.Context()
    file_system = fake_file_system.FakeFileSystem(
        resolver_context)

    file_system.AddFileEntry(
        u'/', file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY)

    path_segments = path.split(u'/')
    for segment_index in range(2, len(path_segments)):
      path_segment = u'{0:s}'.format(
          u'/'.join(path_segments[:segment_index]))
      file_system.AddFileEntry(
          path_segment,
          file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY)

    file_system.AddFileEntry(path, file_data=file_data)

    return file_system

  def _BuildSingleLinkFakeFileSystem(self, path, linked_path):
    """Builds a single link fake file system.

    Args:
      path: The path of the link.
      linked_path: The path that is linked.

    Returns:
      The fake file system (instance of dvfvs.FakeFileSystem).
    """
    resolver_context = context.Context()
    file_system = fake_file_system.FakeFileSystem(
        resolver_context)

    file_system.AddFileEntry(
        u'/', file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY)

    path_segments = path.split(u'/')
    for segment_index in range(2, len(path_segments)):
      path_segment = u'{0:s}'.format(
          u'/'.join(path_segments[:segment_index]))
      file_system.AddFileEntry(
          path_segment,
          file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_DIRECTORY)

    file_system.AddFileEntry(
        path, file_entry_type=dfvfs_definitions.FILE_ENTRY_TYPE_LINK,
        link_data=linked_path)

    return file_system

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file relative to the test data directory.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)

  def _ReadTestFile(self, path_segments):
    """Reads the data from a test file.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      Binary string containing the data of the test file or None.
    """
    path = self._GetTestFilePath(path_segments)

    file_object = open(path, 'rb')
    try:
      file_data = file_object.read()
    except IOError:
      return None
    finally:
      file_object.close()

    return file_data
