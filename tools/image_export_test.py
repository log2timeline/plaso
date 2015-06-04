#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the image export CLI tool."""

import unittest

from plaso.lib import errors
from plaso.frontend import frontend
from tests.cli import test_lib as cli_test_lib

from tools import image_export


class ImageExportToolTest(cli_test_lib.CLIToolTestCase):
  """Tests for the image export CLI tool."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    self._test_tool = image_export.ImageExportTool(
        output_writer=self._output_writer)

  def testListSignatureIdentifiers(self):
    """Tests the ListSignatureIdentifiers function."""
    options = frontend.Options()
    options.data_location = self._TEST_DATA_PATH
    options.signature_identifiers = u'list'

    self._test_tool.ParseOptions(options)

    self._test_tool.ListSignatureIdentifiers()

    expected_output = (
        b'Available signature identifiers:\n'
        b'7z, bzip2, esedb, evt, evtx, ewf_e01, ewf_l01, exe_mz, gzip, lnk, '
        b'msiecf, nk2,\n'
        b'olecf, olecf_beta, pdf, pff, qcow, rar, regf, tar, tar_old, '
        b'vhdi_footer,\n'
        b'vhdi_header, wtcdb_cache, wtcdb_index, zip\n'
        b'\n')

    output = self._output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output.split(b'\n'))

    options = frontend.Options()
    options.data_location = self._GetTestFilePath([u'tmp'])
    options.signature_identifiers = u'list'

    self._test_tool.ParseOptions(options)

    with self.assertRaises(errors.BadConfigOption):
      self._test_tool.ListSignatureIdentifiers()


if __name__ == '__main__':
  unittest.main()
