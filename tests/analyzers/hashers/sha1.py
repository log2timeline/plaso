#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SHA-1 hasher implementation."""

import unittest

from plaso.analyzers.hashers import sha1

from tests.analyzers.hashers import test_lib


class SHA1Test(test_lib.HasherTestCase):
  """Tests the SHA-1 hasher."""

  def testFileHashMatchesEmptyFile(self):
    """Tests that hasher matches the hash of an empty file."""
    hasher = sha1.SHA1Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, ['empty_file'], 'da39a3ee5e6b4b0d3255bfef95601890afd80709')

  def testFileHashMatchesKnownFile(self):
    """Tests that hasher matches the hash of an empty file."""
    hasher = sha1.SHA1Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, ['ímynd.dd'], 'd9f264323004fd9518c0474967f80421e60e9813')


if __name__ == '__main__':
  unittest.main()
