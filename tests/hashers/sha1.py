# -*- coding: utf-8 -*-
"""Tests for the SHA-1 hasher implementation."""

import unittest

from plaso.hashers import sha1

from tests.hashers import test_lib


class SHA1Test(test_lib.HasherTestCase):
  """Tests the SHA-1 hasher."""

  def testFileHashMatches(self):
    """Tests that a few known files match the expected hashes."""
    empty_file_sha1 = u'da39a3ee5e6b4b0d3255bfef95601890afd80709'
    hasher = sha1.SHA1Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, [u'empty_file'], empty_file_sha1)
    hasher = sha1.SHA1Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'empty_file'], empty_file_sha1.decode('hex'))

    unicode_file_sha1 = u'd9f264323004fd9518c0474967f80421e60e9813'
    hasher = sha1.SHA1Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, [u'ímynd.dd'], unicode_file_sha1)
    hasher = sha1.SHA1Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'ímynd.dd'], unicode_file_sha1.decode('hex'))


if __name__ == '__main__':
  unittest.main()
