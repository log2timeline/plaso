#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Entropy hasher."""

import unittest

from plaso.analyzers.hashers import entropy

from tests.analyzers.hashers import test_lib


class EntropyHasherTest(test_lib.HasherTestCase):
  """Tests the Entropy hasher."""

  def testFileHashMatchesEmptyFile(self):
    """Tests that hasher matches the hash of an empty file."""
    hasher = entropy.EntropyHasher()
    self._AssertTestPathStringDigestMatch(hasher, ['empty_file'], '0.000000')

  def testFileHashMatchesKnownFile(self):
    """Tests that hasher matches the hash of a known file."""
    hasher = entropy.EntropyHasher()
    self._AssertTestPathStringDigestMatch(hasher, ['syslog.zip'], '7.264319')


if __name__ == '__main__':
  unittest.main()
