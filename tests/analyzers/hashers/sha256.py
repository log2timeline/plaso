#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the SHA-256 hasher implementation."""

from __future__ import unicode_literals

import unittest

from plaso.analyzers.hashers import sha256

from tests import test_lib as shared_test_lib
from tests.analyzers.hashers import test_lib


class SHA256Test(test_lib.HasherTestCase):
  """Tests the SHA-256 hasher."""

  @shared_test_lib.skipUnlessHasTestFile(['empty_file'])
  def testFileHashMatchesEmptyFile(self):
    """Tests that hasher matches the hash of an empty file."""
    expected_sha256 = (
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

    hasher = sha256.SHA256Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, ['empty_file'], expected_sha256)

  @shared_test_lib.skipUnlessHasTestFile(['ímynd.dd'])
  def testFileHashMatchesKnownFile(self):
    """Tests that hasher matches the hash of a known file."""
    expected_sha256 = (
        'a9c0220b1dadd1812fc4bbe137f495d2c3b88c7b33b5a4de545d201fd31b3bc0')

    hasher = sha256.SHA256Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, ['ímynd.dd'], expected_sha256)


if __name__ == '__main__':
  unittest.main()
