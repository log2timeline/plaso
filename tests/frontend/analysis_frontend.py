#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the analysis front-end object."""

import unittest

from plaso.frontend import analysis_frontend
from plaso.storage import zip_file as storage_zip_file

from tests import test_lib as shared_test_lib


class AnalysisFrontendTests(shared_test_lib.BaseTestCase):
  """Tests for the analysis front-end object."""

  def testOpenStorage(self):
    """Tests the OpenStorage function."""
    test_front_end = analysis_frontend.AnalysisFrontend()

    storage_file_path = self._GetTestFilePath([u'psort_test.json.plaso'])
    storage_file = test_front_end.OpenStorage(storage_file_path)

    self.assertIsInstance(storage_file, storage_zip_file.StorageFile)

    storage_file.Close()


if __name__ == '__main__':
  unittest.main()
