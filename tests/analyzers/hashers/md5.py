#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MD5 hasher."""

from __future__ import unicode_literals

import unittest

from plaso.analyzers.hashers import md5

from tests import test_lib as shared_test_lib
from tests.analyzers.hashers import test_lib


class MD5Test(test_lib.HasherTestCase):
  """Tests the MD5 hasher."""

  @shared_test_lib.skipUnlessHasTestFile(['empty_file'])
  def testFileHashMatchesEmptyFile(self):
    """Tests that hasher matches the hash of an empty file."""
    expected_md5 = 'd41d8cd98f00b204e9800998ecf8427e'

    hasher = md5.MD5Hasher()
    self._AssertTestPathStringDigestMatch(hasher, ['empty_file'], expected_md5)

  @shared_test_lib.skipUnlessHasTestFile(['ímynd.dd'])
  def testFileHashMatchesKnownFile(self):
    """Tests that hasher matches the hash of a known file."""
    expected_md5 = 'd73c51f10c7ee6a681b7b619ccc6f1c4'

    hasher = md5.MD5Hasher()
    self._AssertTestPathStringDigestMatch(hasher, ['ímynd.dd'], expected_md5)


if __name__ == '__main__':
  unittest.main()
