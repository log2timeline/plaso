#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MD5 hasher."""

import unittest

from plaso.analyzers.hashers import md5

from tests.analyzers.hashers import test_lib


class MD5Test(test_lib.HasherTestCase):
  """Tests the MD5 hasher."""

  def testFileHashMatchesEmptyFile(self):
    """Tests that hasher matches the hash of an empty file."""
    hasher = md5.MD5Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, ['empty_file'], 'd41d8cd98f00b204e9800998ecf8427e')

  def testFileHashMatchesKnownFile(self):
    """Tests that hasher matches the hash of a known file."""
    hasher = md5.MD5Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, ['ímynd.dd'], 'd73c51f10c7ee6a681b7b619ccc6f1c4')


if __name__ == '__main__':
  unittest.main()
