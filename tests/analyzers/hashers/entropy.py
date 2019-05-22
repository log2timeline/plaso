#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Entropy hasher."""

from __future__ import unicode_literals

import unittest

from plaso.analyzers.hashers import entropy

from tests import test_lib as shared_test_lib
from tests.analyzers.hashers import test_lib


class EntropyHasherTest(test_lib.HasherTestCase):
  """Tests the Entropy hasher."""

  @shared_test_lib.skipUnlessHasTestFile(['empty_file'])
  def testFileHashMatchesEmptyFile(self):
    """Tests that hasher matches the hash of an empty file."""
    expected_entropy = '0.000000'

    hasher = entropy.EntropyHasher()
    self._AssertTestPathStringDigestMatch(
        hasher, ['empty_file'], expected_entropy)

  @shared_test_lib.skipUnlessHasTestFile(['syslog.zip'])
  def testFileHashMatchesKnownFile(self):
    """Tests that hasher matches the hash of a known file."""
    expected_entropy = '7.264319'

    hasher = entropy.EntropyHasher()
    self._AssertTestPathStringDigestMatch(
        hasher, ['syslog.zip'], expected_entropy)


if __name__ == '__main__':
  unittest.main()
