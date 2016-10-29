# -*- coding: utf-8 -*-
"""Tests for the SHA-256 hasher implementation."""

import unittest

from plaso.analyzers.hashers import sha256

from tests import test_lib as shared_test_lib
from tests.analyzers.hashers import test_lib


class SHA256Test(test_lib.HasherTestCase):
  """Tests the SHA-256 hasher."""

  @shared_test_lib.skipUnlessHasTestFile([u'empty_file'])
  def testFileHashMatchesEmptyFile(self):
    """Tests that hasher matches the hash of an empty file."""
    expected_sha256 = (
        u'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

    hasher = sha256.SHA256Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, [u'empty_file'], expected_sha256)

    hasher = sha256.SHA256Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'empty_file'], expected_sha256.decode(u'hex'))

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testFileHashMatchesKnownFile(self):
    """Tests that hasher matches the hash of a known file."""
    expected_sha256 = (
        u'a9c0220b1dadd1812fc4bbe137f495d2c3b88c7b33b5a4de545d201fd31b3bc0')

    hasher = sha256.SHA256Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, [u'ímynd.dd'], expected_sha256)

    hasher = sha256.SHA256Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'ímynd.dd'], expected_sha256.decode(u'hex'))


if __name__ == '__main__':
  unittest.main()
