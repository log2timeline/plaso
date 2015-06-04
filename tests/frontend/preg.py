#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the preg front-end."""

import unittest

from plaso.frontend import preg

from tests.frontend import test_lib


class PregFrontendTest(test_lib.FrontendTestCase):
  """Tests for the preg front-end."""

  def testGetRegistryFilePaths(self):
    """Tests the GetRegistryFilePaths function."""
    test_front_end = preg.PregFrontend()

    expected_paths = [
        u'/Documents And Settings/.+/NTUSER.DAT',
        u'/Users/.+/NTUSER.DAT']

    paths = test_front_end.GetRegistryFilePaths(u'userassist')

    self.assertEqual(sorted(paths), sorted(expected_paths))

    # Test the SOFTWARE hive.
    # TODO: refactor this into a method.
    preg.PregCache.knowledge_base_object.pre_obj.sysregistry = u'C:/Windows/Foo'

    expected_paths = [u'C:/Windows/Foo/SOFTWARE']

    paths = test_front_end.GetRegistryFilePaths(u'', u'SOFTWARE')

    self.assertEqual(sorted(paths), sorted(expected_paths))


if __name__ == '__main__':
  unittest.main()
