#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the analysis front-end object."""

import unittest

from plaso.frontend import analysis_frontend
from plaso.frontend import frontend
from plaso.frontend import test_lib
from plaso.lib import errors
from plaso.lib import storage


class AnalysisFrontendTests(test_lib.FrontendTestCase):
  """Tests for the analysis front-end object."""

  def setUp(self):
    """Sets up the objects used throughout the test."""
    self._input_reader = frontend.StdinFrontendInputReader()
    self._output_writer = frontend.StdoutFrontendOutputWriter()

  def testOpenStorageFile(self):
    """Tests the open storage file function."""
    test_front_end = analysis_frontend.AnalysisFrontend(
        self._input_reader, self._output_writer)

    options = frontend.Options()
    options.storage_file = self._GetTestFilePath([u'psort_test.out'])

    test_front_end.ParseOptions(options)
    storage_file = test_front_end.OpenStorageFile()

    self.assertIsInstance(storage_file, storage.StorageFile)

    storage_file.Close()

  def testParseOptions(self):
    """Tests the parse options function."""
    test_front_end = analysis_frontend.AnalysisFrontend(
        self._input_reader, self._output_writer)

    options = frontend.Options()

    with self.assertRaises(errors.BadConfigOption):
      test_front_end.ParseOptions(options)

    options.storage_file = self._GetTestFilePath([u'no_such_file.out'])

    with self.assertRaises(errors.BadConfigOption):
      test_front_end.ParseOptions(options)

    options.storage_file = self._GetTestFilePath([u'psort_test.out'])

    test_front_end.ParseOptions(options)


if __name__ == '__main__':
  unittest.main()
