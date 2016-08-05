# -*- coding: utf-8 -*-
"""Tests for the SHA-1 hasher implementation."""

import unittest

from plaso.analyzers.hashers import sha1

from tests import test_lib as shared_test_lib
from tests.analyzers.hashers import test_lib


class SHA1Test(test_lib.HasherTestCase):
  """Tests the SHA-1 hasher."""

  @shared_test_lib.skipUnlessHasTestFile([u'empty_file'])
  def testFileHashMatchesEmptyFile(self):
    """Tests that hasher matches the hash of an empty file."""
    expected_sha1 = u'da39a3ee5e6b4b0d3255bfef95601890afd80709'

    hasher = sha1.SHA1Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, [u'empty_file'], expected_sha1)

    hasher = sha1.SHA1Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'empty_file'], expected_sha1.decode(u'hex'))

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testFileHashMatchesKnownFile(self):
    """Tests that hasher matches the hash of an empty file."""
    expected_sha1 = u'd9f264323004fd9518c0474967f80421e60e9813'

    hasher = sha1.SHA1Hasher()
    self._AssertTestPathStringDigestMatch(hasher, [u'ímynd.dd'], expected_sha1)

    hasher = sha1.SHA1Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'ímynd.dd'], expected_sha1.decode(u'hex'))


if __name__ == '__main__':
  unittest.main()
