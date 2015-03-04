# -*- coding: utf-8 -*-
"""Tests for the MD5 hasher."""

from plaso.hashers import md5
from plaso.hashers import test_lib


class MD5Test(test_lib.HasherTestCase):
  """Tests the MD5 hasher."""

  def testFileHashMatches(self):
    """Tests that a few known files match the expected hashes."""
    empty_file_md5 = u'd41d8cd98f00b204e9800998ecf8427e'
    hasher = md5.MD5Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, [u'empty_file'], empty_file_md5)
    hasher = md5.MD5Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'empty_file'], empty_file_md5.decode(u'hex'))

    unicode_file_md5 = u'd73c51f10c7ee6a681b7b619ccc6f1c4'
    hasher = md5.MD5Hasher()
    self._AssertTestPathStringDigestMatch(
        hasher, [u'ímynd.dd'], unicode_file_md5)
    hasher = md5.MD5Hasher()
    self._AssertTestPathBinaryDigestMatch(
        hasher, [u'ímynd.dd'], unicode_file_md5.decode(u'hex'))
