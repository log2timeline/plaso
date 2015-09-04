#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the analysis front-end object."""

import unittest

from plaso.frontend import analysis_frontend
from plaso.lib import storage

from tests.frontend import test_lib


class AnalysisFrontendTests(test_lib.FrontendTestCase):
  """Tests for the analysis front-end object."""

  def testOpenStorage(self):
    """Tests the OpenStorage function."""
    test_front_end = analysis_frontend.AnalysisFrontend()

    storage_file_path = self._GetTestFilePath([u'psort_test.proto.plaso'])
    storage_file = test_front_end.OpenStorage(storage_file_path)

    self.assertIsInstance(storage_file, storage.StorageFile)

    storage_file.Close()


if __name__ == '__main__':
  unittest.main()
