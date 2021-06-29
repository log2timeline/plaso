# -*- coding: utf-8 -*-
"""Hashing related functions and classes for testing."""

import os

from tests import test_lib as shared_test_lib


class HasherTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a hasher."""

  _DEFAULT_READ_SIZE = 512

  def _AssertFileEntryStringDigestMatch(
      self, hasher, file_entry, expected_digest):
    """Checks that a hasher returns a given result when it hashes a file.

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

    self.assertEqual(hasher.GetStringDigest(), expected_digest)

  def _AssertTestPathStringDigestMatch(self, hasher, path_segments, digest):
    """Checks if a hasher returns a given result when it hashes a test file.

    Args:
      hasher (Class): hasher class to test.
      path_segments (list[str]): components of a path to a test file, relative
          to the test_data directory.
      digest (str): digest the hasher should return.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    file_entry = self._GetTestFileEntry(path_segments)
    self._AssertFileEntryStringDigestMatch(hasher, file_entry, digest)
