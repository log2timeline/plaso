#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the shared functionality for text file based output modules."""

import io
import unittest

from plaso.output import text_file

from tests.output import test_lib


class TextFileOutputModuleTest(test_lib.OutputModuleTestCase):
  """Tests for the shared functionality for text file based output modules."""

  # pylint: disable=protected-access

  def testWriteHeader(self):
    """Tests the WriteHeader function."""
    test_file_object = io.StringIO()

    output_mediator = self._CreateOutputMediator()
    output_module = text_file.TextFileOutputModule()
    output_module._file_object = test_file_object

    output_module.WriteHeader(output_mediator)

    header = test_file_object.getvalue()
    self.assertEqual(header, '')

  def testWriteFooter(self):
    """Tests the WriteFooter function."""
    test_file_object = io.StringIO()

    output_module = text_file.TextFileOutputModule()
    output_module._file_object = test_file_object

    output_module.WriteFooter()

    footer = test_file_object.getvalue()
    self.assertEqual(footer, '')


if __name__ == '__main__':
  unittest.main()
