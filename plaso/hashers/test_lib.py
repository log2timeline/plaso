# -*- coding: utf-8 -*-
"""Hashing related functions and classes for testing."""

import os
import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver


class HasherTestCase(unittest.TestCase):
  """The unit test case for a hasher."""

  _TEST_DATA_PATH = os.path.join(os.getcwd(), 'test_data')
  _DEFAULT_READ_SIZE = 512

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

  def _GetTestFileEntry(self, path_segments):
    """Creates a dfVFS file_entry that references a file in the test dir.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A dfVFS file_entry object.
    """
    path = self._GetTestFilePath(path_segments)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    return file_entry

  def _AssertFileEntryStringDigestMatch(self, hasher, file_entry, digest):
    """Test that a hasher returns a given result when it hashes a file.

    Args:
      hasher: The hasher (subclass of BaseHasher) to test.
      file_entry: The dfVFS file entry to hash.
      digest: The digest the hasher should return.
    """
    file_object = file_entry.GetFileObject()
    data = file_object.read(self._DEFAULT_READ_SIZE)
    while data:
      hasher.Update(data)
      data = file_object.read(self._DEFAULT_READ_SIZE)
    file_object.close()
    self.assertEquals(hasher.GetStringDigest(), digest)

  def _AssertTestPathStringDigestMatch(self, hasher, path_segments, digest):
    """Check if a hasher returns a given result when it hashes a test file.

    Args:
      hasher: The hasher (subclass of BaseHasher) to test.
      file_entry: The dfVFS file entry to hash.
      hash: The digest the hasher should return.
    """
    file_entry = self._GetTestFileEntry(path_segments)
    self._AssertFileEntryStringDigestMatch(hasher, file_entry, digest)

  def _AssertFileEntryBinaryDigestMatch(self, hasher, file_entry, digest):
    """Test that a hasher returns a given result when it hashes a file.

    Args:
      hasher: The hasher (subclass of BaseHasher) to test.
      file_entry: The dfVFS file entry to hash.
      hash: The digest the hasher should return.
    """
    file_object = file_entry.GetFileObject()
    data = file_object.read(self._DEFAULT_READ_SIZE)
    while data:
      hasher.Update(data)
      data = file_object.read(self._DEFAULT_READ_SIZE)
    file_object.close()
    self.assertEquals(hasher.GetBinaryDigest(), digest)

  def _AssertTestPathBinaryDigestMatch(self, hasher, path_segments, digest):
    """Check if a hasher returns a given result when it hashes a test file.

    Args:
      hasher: The hasher (subclass of BaseHasher) to test.
      file_entry: The dfVFS file entry to hash.
      hash: The hash the hasher should return.
    """
    file_entry = self._GetTestFileEntry(path_segments)
    self._AssertFileEntryBinaryDigestMatch(hasher, file_entry, digest)
