#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the language tags helper."""

import unittest

from plaso.helpers import language_tags

from tests import test_lib as shared_test_lib


class LanguageTagHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the language tags helper."""

  def testGetLanguages(self):
    """Tests the GetLanguages function."""
    languages = dict(language_tags.LanguageTagHelper.GetLanguages())

    self.assertIn('is-IS', languages)
    self.assertEqual(languages['is-IS'], 'Icelandic, Iceland')

  def testIsLanguageTag(self):
    """Tests the IsLanguageTag function."""
    result = language_tags.LanguageTagHelper.IsLanguageTag('is-IS')
    self.assertTrue(result)

    result = language_tags.LanguageTagHelper.IsLanguageTag('bogus')
    self.assertFalse(result)


if __name__ == '__main__':
  unittest.main()
