#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the tagging file."""

from __future__ import unicode_literals

import unittest

from plaso.engine import tagging_file
from plaso.lib import errors

from tests import test_lib as shared_test_lib


class TaggingFileTestCase(shared_test_lib.BaseTestCase):
  """Tests for the tagging file."""

  # pylint: disable=protected-access

  # TODO: add tests for _ParseDefinitions
  # TODO: add tests for _ParseEventTaggingRule

  @shared_test_lib.skipUnlessHasTestFile([
      'tagging_file', 'invalid_syntax.txt'])
  @shared_test_lib.skipUnlessHasTestFile(['tagging_file', 'valid.txt'])
  def testGetEventTaggingRules(self):
    """Tests the GetEventTaggingRules function."""
    test_path = self._GetTestFilePath(['tagging_file', 'valid.txt'])
    tag_file = tagging_file.TaggingFile(test_path)

    tag_expression = tag_file.GetEventTaggingRules()
    self.assertEqual(len(tag_expression.children), 5)

    test_path = self._GetTestFilePath(['tagging_file', 'invalid_syntax.txt'])
    tag_file = tagging_file.TaggingFile(test_path)

    with self.assertRaises(errors.TaggingFileError):
      tag_file.GetEventTaggingRules()


if __name__ == '__main__':
  unittest.main()
