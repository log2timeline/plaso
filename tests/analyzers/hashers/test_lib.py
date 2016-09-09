# -*- coding: utf-8 -*-
"""Hashing related functions and classes for testing."""

import os

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from tests import test_lib as shared_test_lib


class HasherTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a hasher."""

  _DEFAULT_READ_SIZE = 512

  def _AssertFileEntryBinaryDigestMatch(
      self, hasher, file_entry, expected_digest):
    """Test that a hasher returns a given result when it hashes a file.

    Args:
      hasher (BaseHasher): hasher to test.
      file_entry (dfvfs.file_entry): file entry whose default data stream will
          be hashed.
      expected_digest (bytes): digest expected to be returned by hasher.
    """
    file_object = file_entry.GetFileObject()
    # Make sure we are starting from the beginning of the file.
    file_object.seek(0, os.SEEK_SET)

    data = file_object.read(self._DEFAULT_READ_SIZE)
    while data:
      hasher.Update(data)
      data = file_object.read(self._DEFAULT_READ_SIZE)
    file_object.close()
    self.assertEqual(hasher.GetBinaryDigest(), expected_digest)

  def _AssertFileEntryStringDigestMatch(
      self, hasher, file_entry, expected_digest):
    """Test that a hasher returns a given result when it hashes a file.

    Args:
      hasher (BaseHasher): hasher to test.
      file_entry (dfvfs.file_entry): file entry whose default data stream will
          be hashed.
      expected_digest (bytes): digest expected to be returned by hasher.
    """
    file_object = file_entry.GetFileObject()

    # Make sure we are starting from the beginning of the file.
    file_object.seek(0, os.SEEK_SET)

    data = file_object.read(self._DEFAULT_READ_SIZE)
    while data:
      hasher.Update(data)
      data = file_object.read(self._DEFAULT_READ_SIZE)
    file_object.close()
    self.assertEqual(hasher.GetStringDigest(), expected_digest)

  def _AssertTestPathBinaryDigestMatch(self, hasher, path_segments, digest):
    """Check if a hasher returns a given result when it hashes a test file.

    Args:
      hasher (BaseHasher): hasher to test.
      path_segments (list[str]): components of a path to a test file, relative
          to the test_data directory.
      digest (bytes): digest the hasher should return.
    """
    file_entry = self._GetTestFileEntry(path_segments)
    self._AssertFileEntryBinaryDigestMatch(hasher, file_entry, digest)

  def _AssertTestPathStringDigestMatch(self, hasher, path_segments, digest):
    """Check if a hasher returns a given result when it hashes a test file.

    Args:
      hasher (Class): hasher class to test.
      path_segments (list[str]): components of a path to a test file, relative
          to the test_data directory.
      digest (str): digest the hasher should return.
    """
    file_entry = self._GetTestFileEntry(path_segments)
    self._AssertFileEntryStringDigestMatch(hasher, file_entry, digest)

  def _GetTestFileEntry(self, path_segments):
    """Creates a file_entry that references a file in the test dir.

    Args:
      path_segments (list[str]): components of a path to a test file, relative
          to the test_data directory.

    Returns:
      A file_entry object (instance of dfvfs.FileEntry).
    """
    path = self._GetTestFilePath(path_segments)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    return path_spec_resolver.Resolver.OpenFileEntry(path_spec)
