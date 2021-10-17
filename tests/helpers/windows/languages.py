#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows languages helper."""

import unittest

from plaso.helpers.windows import languages

from tests import test_lib as shared_test_lib


class WindowsLanguageHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows languages helper."""

  def testGetLanguageTagForLCID(self):
    """Tests the GetLanguageTagForLCID function."""
    language_tag = languages.WindowsLanguageHelper.GetLanguageTagForLCID(0x040f)
    self.assertEqual(language_tag, 'is-IS')

    language_tag = languages.WindowsLanguageHelper.GetLanguageTagForLCID(0xffff)
    self.assertIsNone(language_tag)

  def testGetLCIDForLanguageTag(self):
    """Tests the GetLCIDForLanguageTag function."""
    lcid = languages.WindowsLanguageHelper.GetLCIDForLanguageTag('is-IS')
    self.assertEqual(lcid, 0x040f)

    lcid = languages.WindowsLanguageHelper.GetLCIDForLanguageTag('bogus')
    self.assertIsNone(lcid)


if __name__ == '__main__':
  unittest.main()
