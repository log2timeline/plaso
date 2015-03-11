# -*- coding: utf-8 -*-
"""Tests for the SHA-256 hasher implementation."""

import unittest

from plaso.hashers import sha256
from plaso.hashers import test_lib

class SHA256Test(test_lib.HasherTestCase):
  """Tests the SHA-256 hasher."""

  def testFileHashMatches(self):
    """Tests that a few known files match the expected hashes."""
    empty_file_sha256 = u'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca49' \
                        u'5991b7852b855'
    hasher = sha256.SHA256Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, [u'empty_file'], empty_file_sha256)
    hasher = sha256.SHA256Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'empty_file'], empty_file_sha256.decode('hex'))

    unicode_file_sha256 = u'a9c0220b1dadd1812fc4bbe137f495d2c3b88c7b33b5a4de5' \
                          u'45d201fd31b3bc0'
    hasher = sha256.SHA256Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, [u'ímynd.dd'], unicode_file_sha256)
    hasher = sha256.SHA256Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'ímynd.dd'], unicode_file_sha256.decode('hex'))

if __name__ == '__main__':
  unittest.main()
