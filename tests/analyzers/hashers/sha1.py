#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SHA-1 hasher implementation."""

from __future__ import unicode_literals

import unittest

from plaso.analyzers.hashers import sha1

from tests import test_lib as shared_test_lib
from tests.analyzers.hashers import test_lib


class SHA1Test(test_lib.HasherTestCase):
  """Tests the SHA-1 hasher."""

  @shared_test_lib.skipUnlessHasTestFile(['empty_file'])
  def testFileHashMatchesEmptyFile(self):
    """Tests that hasher matches the hash of an empty file."""
    expected_sha1 = 'da39a3ee5e6b4b0d3255bfef95601890afd80709'

    hasher = sha1.SHA1Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, ['empty_file'], expected_sha1)

  @shared_test_lib.skipUnlessHasTestFile(['ímynd.dd'])
  def testFileHashMatchesKnownFile(self):
    """Tests that hasher matches the hash of an empty file."""
    expected_sha1 = 'd9f264323004fd9518c0474967f80421e60e9813'

    hasher = sha1.SHA1Hasher()
    self._AssertTestPathStringDigestMatch(hasher, ['ímynd.dd'], expected_sha1)


if __name__ == '__main__':
  unittest.main()
