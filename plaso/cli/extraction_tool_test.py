#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the extraction tool object."""

import unittest

from plaso.cli import extraction_tool
from plaso.cli import test_lib
from plaso.lib import errors
from plaso.frontend import frontend


class ExtractionToolTest(test_lib.CLIToolTestCase):
  """Tests for the extraction tool object."""

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_tool = extraction_tool.ExtractionTool()

    options = frontend.Options()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    options.source = self._GetTestFilePath([u'ímynd.dd'])

    test_tool.ParseOptions(options)


if __name__ == '__main__':
  unittest.main()
