# -*- coding: utf-8 -*-
"""Tests for the year-less log format helper mix-in."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import yearless_helper

from tests import test_lib as shared_test_lib


class YearLessLogFormatHelperTest(shared_test_lib.BaseTestCase):
  """Year-less log format definition helper mix-in tests."""

  # pylint: disable=protected-access

  def testGetYearsFromFileEntry(self):
    """Tests the _GetYearsFromFileEntry function."""
    test_helper = yearless_helper.YearLessLogFormatHelper()

    test_path = self._GetTestFilePath(['syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path)
    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

    years = test_helper._GetYearsFromFileEntry(file_entry)
    self.assertEqual(years, set([2012]))

    # TODO: improve test coverage.


if __name__ == '__main__':
  unittest.main()
