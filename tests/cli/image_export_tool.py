#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the image export CLI tool."""

import unittest

from plaso.cli import image_export_tool
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib as test_lib


class ImageExportToolTest(test_lib.CLIToolTestCase):
  """Tests for the image export CLI tool."""

  # pylint: disable=protected-access

  def testListSignatureIdentifiers(self):
    """Tests the ListSignatureIdentifiers function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    test_tool._data_location = self._TEST_DATA_PATH

    test_tool.ListSignatureIdentifiers()

    expected_output = (
        b'Available signature identifiers:\n'
        b'7z, bzip2, esedb, evt, evtx, ewf_e01, ewf_l01, exe_mz, gzip, lnk, '
        b'msiecf, nk2,\n'
        b'olecf, olecf_beta, pdf, pff, qcow, rar, regf, tar, tar_old, '
        b'vhdi_footer,\n'
        b'vhdi_header, wtcdb_cache, wtcdb_index, zip\n'
        b'\n')

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output.split(b'\n'))

    test_tool._data_location = self._GetTestFilePath([u'tmp'])

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ListSignatureIdentifiers()

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    result = test_tool.ParseArguments()
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.image = self._GetTestFilePath([u'image.qcow2'])

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  # TODO: add test for PrintFilterCollection

  def testProcessSourcesImage(self):
    """Tests the ProcessSources function on a single partition image."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = image_export_tool.ImageExportTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.image = self._GetTestFilePath([u'ímynd.dd'])
    options.quiet = True

    with shared_test_lib.TempDirectory() as temp_directory:
      options.path = temp_directory

      test_tool.ParseOptions(options)

      test_tool.ProcessSources()

      expected_output = b'\n'.join([
          b'Export started.',
          b'Extracting file entries.',
          b'Export completed.',
          b'',
          b''])

      output = output_writer.ReadOutput()
      self.assertEqual(output, expected_output)


if __name__ == '__main__':
  unittest.main()
