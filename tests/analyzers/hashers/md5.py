# -*- coding: utf-8 -*-
"""Tests for the MD5 hasher."""

import unittest

from plaso.analyzers.hashers import md5

from tests import test_lib as shared_test_lib
from tests.analyzers.hashers import test_lib


class MD5Test(test_lib.HasherTestCase):
  """Tests the MD5 hasher."""

  @shared_test_lib.skipUnlessHasTestFile([u'empty_file'])
  def testFileHashMatchesEmptyFile(self):
    """Tests that hasher matches the hash of an empty file."""
    expected_md5 = u'd41d8cd98f00b204e9800998ecf8427e'

    hasher = md5.MD5Hasher()
    self._AssertTestPathStringDigestMatch(hasher, [u'empty_file'], expected_md5)

    hasher = md5.MD5Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'empty_file'], expected_md5.decode(u'hex'))

  @shared_test_lib.skipUnlessHasTestFile([u'ímynd.dd'])
  def testFileHashMatchesKnownFile(self):
    """Tests that hasher matches the hash of a known file."""
    expected_md5 = u'd73c51f10c7ee6a681b7b619ccc6f1c4'

    hasher = md5.MD5Hasher()
    self._AssertTestPathStringDigestMatch(hasher, [u'ímynd.dd'], expected_md5)

    hasher = md5.MD5Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'ímynd.dd'], expected_md5.decode(u'hex'))


if __name__ == '__main__':
  unittest.main()
