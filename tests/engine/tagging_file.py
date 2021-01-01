#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tagging file."""

import unittest

from plaso.engine import tagging_file
from plaso.lib import errors

from tests import test_lib as shared_test_lib


class TaggingFileTestCase(shared_test_lib.BaseTestCase):
  """Tests for the tagging file."""

  def testGetEventTaggingRules(self):
    """Tests the GetEventTaggingRules function."""
    test_file_path = self._GetTestFilePath(['tagging_file', 'valid.txt'])
    self._SkipIfPathNotExists(test_file_path)

    tag_file = tagging_file.TaggingFile(test_file_path)

    tagging_rules = tag_file.GetEventTaggingRules()
    self.assertEqual(len(tagging_rules), 5)

  def testGetEventTaggingRulesInvalidSyntax(self):
    """Tests the GetEventTaggingRules function on a file with invalid syntax."""
    test_file_path = self._GetTestFilePath([
        'tagging_file', 'invalid_syntax.txt'])
    self._SkipIfPathNotExists(test_file_path)

    tag_file = tagging_file.TaggingFile(test_file_path)

    with self.assertRaises(errors.TaggingFileError):
      tag_file.GetEventTaggingRules()


if __name__ == '__main__':
  unittest.main()
