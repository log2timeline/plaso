#!/usr/bin/env python3
"""Tests for the shared functionality for text file based output modules."""

import io
import os
import unittest

from plaso.output import text_file

from tests import test_lib as shared_test_lib
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
        self.assertEqual(header, "")

    def testWriteFooter(self):
        """Tests the WriteFooter function."""
        test_file_object = io.StringIO()

        output_module = text_file.TextFileOutputModule()
        output_module._file_object = test_file_object

        output_module.WriteFooter()

        footer = test_file_object.getvalue()
        self.assertEqual(footer, "")

    def testWriteLineWithUnpairedSurrogate(self):
        """Tests the WriteLine function with an unpaired surrogate."""
        # Values read from Windows Registry REG_SZ data can contain an unpaired
        # UTF-16 surrogate, which cannot be encoded as UTF-8. Such a value must
        # not cause the output file to be truncated.
        with shared_test_lib.TempDirectory() as temp_directory:
            test_path = os.path.join(temp_directory, "text_file.out")

            output_module = text_file.TextFileOutputModule()
            output_module.Open(path=test_path)

            try:
                output_module.WriteLine("x\udab3")
            finally:
                output_module.Close()

            with open(test_path, "rt", encoding="utf-8") as file_object:
                output = file_object.read()

        self.assertEqual(output, "x\\udab3\n")


if __name__ == "__main__":
    unittest.main()
