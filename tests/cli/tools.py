#!/usr/bin/env python3
"""Tests for the CLI tools classes."""

import io
import locale
import os
import sys
import unittest

from plaso.cli import tools
from plaso.lib import errors

from tests.cli import test_lib


class CLIToolTest(test_lib.CLIToolTestCase):
    """Tests for the CLI tool base class."""

    # pylint: disable=protected-access

    _EXPECTED_BASIC_OPTIONS = f"""\
usage: tool_test.py [-h] [--troubles] [-V]

Test argument parser.

{test_lib.ARGPARSE_OPTIONS}:
  --troubles     Show troubleshooting information.
  -V, --version  Show the version information.
  -h, --help     Show this help message and exit.
"""

    _EXPECTED_INFORMATIONAL_OPTIONS = f"""\
usage: tool_test.py [-d] [-q] [-u]

Test argument parser.

{test_lib.ARGPARSE_OPTIONS}:
  -d, --debug       Enable debug output.
  -q, --quiet       Disable informational output.
  -u, --unattended  Enable unattended mode and do not ask the user for
                    additional input when needed, but terminate with an error
                    instead.
"""

    _EXPECTED_REDACTION_OPTIONS = f"""\
usage: tool_test.py [--redact_secrets]

Test argument parser.

{test_lib.ARGPARSE_OPTIONS}:
  --redact_secrets, --redact-secrets
                        Redact secrets, such as credentials, the OpenSearch
                        password and the VirusTotal API key, in the command
                        line arguments that are stored in the storage file, by
                        replacing them with "<redacted>". The names of the
                        redacted options are logged. By default the command
                        line arguments are stored as-is.
"""

    _EXPECTED_SEPARATOR_LINE = """\
--------------------------------------------------------------------------------
"""

    _EXPECTED_TIME_ZONE_OPTIONS = """\

************************************ Zones *************************************
                        Timezone : UTC Offset
--------------------------------------------------------------------------------
"""

    # TODO: add test for _ConfigureLogging
    # TODO: add test for _EncodeString

    def testParseInformationalOptions(self):
        """Tests the _ParseInformationalOptions function."""
        test_tool = tools.CLITool()

        options = test_lib.TestOptions()
        options.debug = True
        options.quiet = True

        test_tool._ParseInformationalOptions(options)

    def testParseLogFileOptions(self):
        """Tests the _ParseLogFileOptions function."""
        test_tool = tools.CLITool()

        options = test_lib.TestOptions()
        options.log_file = "file.log"

        test_tool._ParseLogFileOptions(options)

    # TODO: add test for _PromptUserForInput

    def testRedactSecrets(self):
        """Tests the _RedactSecrets function."""
        test_tool = tools.CLITool()

        command_line_arguments, redacted_options = test_tool._RedactSecrets(
            [
                "psort.py",
                "--credential",
                "recovery_password:123456",
                "--credential=key_data",
                "--cred",
                "password:test",
                "--opensearch-password",
                "secret1",
                "--opensearch-pass=secret2",
                "--virustotal_api_key",
                "secret3",
                "--virustotal-api-key=secret4",
                "--opensearch-user",
                "analyst",
                "test.plaso",
            ]
        )
        self.assertEqual(
            command_line_arguments,
            [
                "psort.py",
                "--credential",
                "recovery_password:<redacted>",
                "--credential=<redacted>",
                "--cred",
                "password:<redacted>",
                "--opensearch-password",
                "<redacted>",
                "--opensearch-pass=<redacted>",
                "--virustotal_api_key",
                "<redacted>",
                "--virustotal-api-key=<redacted>",
                "--opensearch-user",
                "analyst",
                "test.plaso",
            ],
        )
        self.assertEqual(
            redacted_options,
            [
                "--credential",
                "--cred",
                "--opensearch-password",
                "--opensearch-pass",
                "--virustotal_api_key",
                "--virustotal-api-key",
            ],
        )

    def testAddBasicOptions(self):
        """Tests the AddBasicOptions function."""
        argument_parser = self._GetTestArgumentParser("tool_test.py")

        test_tool = tools.CLITool()
        test_tool.AddBasicOptions(argument_parser)

        output = self._RunArgparseFormatHelp(argument_parser)
        self.assertEqual(output, self._EXPECTED_BASIC_OPTIONS)

    def testAddInformationalOptions(self):
        """Tests the AddInformationalOptions function."""
        argument_parser = self._GetTestArgumentParser("tool_test.py")

        test_tool = tools.CLITool()
        test_tool.AddInformationalOptions(argument_parser)

        output = self._RunArgparseFormatHelp(argument_parser)
        self.assertEqual(output, self._EXPECTED_INFORMATIONAL_OPTIONS)

    # TODO: add test for AddLogFileOptions

    def testAddRedactionOptions(self):
        """Tests the AddRedactionOptions function."""
        argument_parser = self._GetTestArgumentParser("tool_test.py")

        test_tool = tools.CLITool()
        test_tool.AddRedactionOptions(argument_parser)

        output = self._RunArgparseFormatHelp(argument_parser)
        self.assertEqual(output, self._EXPECTED_REDACTION_OPTIONS)

        options = argument_parser.parse_args([])
        self.assertFalse(options.redact_secrets)

        options = argument_parser.parse_args(["--redact_secrets"])
        self.assertTrue(options.redact_secrets)

        options = argument_parser.parse_args(["--redact-secrets"])
        self.assertTrue(options.redact_secrets)

    def testCheckOutDated(self):
        """Tests the CheckOutDated function."""
        cli_tool = tools.CLITool()

        cli_tool.CheckOutDated()

    def testGetCommandLineArguments(self):
        """Tests the GetCommandLineArguments function."""
        cli_tool = tools.CLITool()
        cli_tool.preferred_encoding = "UTF-8"

        command_line_arguments = cli_tool.GetCommandLineArguments()
        self.assertIsNotNone(command_line_arguments)

        original_argv = sys.argv
        sys.argv = [
            "log2timeline.py",
            "--credential",
            "password:BDE-test",
            "--opensearch_password=secret",
            "source.raw",
        ]
        try:
            command_line_arguments = cli_tool.GetCommandLineArguments()
            self.assertEqual(
                command_line_arguments,
                (
                    "log2timeline.py --credential password:BDE-test "
                    "--opensearch_password=secret source.raw"
                ),
            )

            options = test_lib.TestOptions()
            options.redact_secrets = True

            cli_tool._ParseInformationalOptions(options)

            with self.assertLogs("cli", level="INFO") as log_context:
                command_line_arguments = cli_tool.GetCommandLineArguments()

            self.assertEqual(
                command_line_arguments,
                (
                    "log2timeline.py --credential password:<redacted> "
                    "--opensearch_password=<redacted> source.raw"
                ),
            )
            self.assertEqual(
                log_context.output,
                [
                    (
                        "INFO:cli:Redacted the values of the options: "
                        "--credential, --opensearch_password in the command line "
                        "arguments stored in the storage file."
                    )
                ],
            )
            self.assertNotIn("BDE-test", log_context.output[0])

        finally:
            sys.argv = original_argv

    def testListTimeZones(self):
        """Tests the ListTimeZones function."""
        output_writer = test_lib.TestBinaryOutputWriter()
        cli_tool = tools.CLITool(output_writer=output_writer)

        cli_tool.ListTimeZones()

        string = output_writer.ReadOutput()
        self.assertTrue(string[:4], self._EXPECTED_TIME_ZONE_OPTIONS)

    def testParseNumericOption(self):
        """Tests the ParseNumericOption function."""
        output_writer = test_lib.TestBinaryOutputWriter()
        cli_tool = tools.CLITool(output_writer=output_writer)

        options = test_lib.TestOptions()

        numeric_value = cli_tool.ParseNumericOption(options, "buffer_size")
        self.assertIsNone(numeric_value)

        numeric_value = cli_tool.ParseNumericOption(
            options, "buffer_size", default_value=0
        )
        self.assertEqual(numeric_value, 0)

        options.buffer_size = "10"

        numeric_value = cli_tool.ParseNumericOption(options, "buffer_size")
        self.assertEqual(numeric_value, 10)

        numeric_value = cli_tool.ParseNumericOption(options, "buffer_size", base=16)
        self.assertEqual(numeric_value, 16)

        options.buffer_size = "bogus"

        with self.assertRaises(errors.BadConfigOption):
            cli_tool.ParseNumericOption(options, "buffer_size")

        options.buffer_size = (1, "bogus")

        with self.assertRaises(errors.BadConfigOption):
            cli_tool.ParseNumericOption(options, "buffer_size")

    def testParseStringOption(self):
        """Tests the ParseStringOption function."""
        encoding = sys.stdin.encoding

        # Note that sys.stdin.encoding can be None.
        if not encoding:
            encoding = locale.getpreferredencoding()

        cli_tool = tools.CLITool()
        cli_tool.preferred_encoding = "UTF-8"

        expected_string = "Test Unicode string"
        options = test_lib.TestOptions()
        options.test = expected_string

        string = cli_tool.ParseStringOption(options, "test")
        self.assertEqual(string, expected_string)

        options = test_lib.TestOptions()

        string = cli_tool.ParseStringOption(options, "test")
        self.assertIsNone(string)

        string = cli_tool.ParseStringOption(
            options, "test", default_value=expected_string
        )
        self.assertEqual(string, expected_string)

        options = test_lib.TestOptions()
        options.test = expected_string.encode(encoding)

        string = cli_tool.ParseStringOption(options, "test")
        self.assertEqual(string, expected_string)

        if encoding and encoding.upper() == "UTF-8":
            options = test_lib.TestOptions()
            options.test = (
                b"\xad\xfd\xab\x73\x99\xc7\xb4\x78\xd0\x8c\x8a\xee\x6d\x6a\xcb\x90"
            )

            with self.assertRaises(errors.BadConfigOption):
                cli_tool.ParseStringOption(options, "test")

    def testPrintSeparatorLine(self):
        """Tests the PrintSeparatorLine function."""
        output_writer = test_lib.TestOutputWriter()
        cli_tool = tools.CLITool(output_writer=output_writer)

        cli_tool.PrintSeparatorLine()
        string = output_writer.ReadOutput()
        self.assertEqual(string, self._EXPECTED_SEPARATOR_LINE)


class CLIInputReaderTest(test_lib.CLIToolTestCase):
    """Tests for the command line interface input reader interface."""

    def testInitialize(self):
        """Tests the __init__ function."""
        input_reader = tools.CLIInputReader()
        self.assertIsNotNone(input_reader)


class FileObjectInputReaderTest(unittest.TestCase):
    """Tests for the file object command line interface input reader."""

    def testInitialize(self):
        """Tests the __init__ function."""
        input_reader = tools.StdinInputReader()
        self.assertIsNotNone(input_reader)

    _TEST_DATA = (
        b"A first string\n"
        b"A 2nd string\n"
        b"\xc3\xberi\xc3\xb0ja string\n"
        b"\xff\xfef\x00j\x00\xf3\x00r\x00\xf0\x00a\x00 \x00b\x00a\x00n\x00d\x00"
    )

    _TEST_STRING_DATA = "A first string\nA 2nd string\nþriðja string\n"

    def testReadASCII(self):
        """Tests the Read function with ASCII encoding."""
        file_object = io.BytesIO(self._TEST_DATA)
        input_reader = tools.FileObjectInputReader(file_object, encoding="ascii")

        string = input_reader.Read()
        self.assertEqual(string, "A first string\n")

        string = input_reader.Read()
        self.assertEqual(string, "A 2nd string\n")

        # UTF-8 string with non-ASCII characters.
        string = input_reader.Read()
        self.assertEqual(string, "\\xc3\\xberi\\xc3\\xb0ja string\n")

        # UTF-16 string with non-ASCII characters.
        string = input_reader.Read()
        expected_string = (
            "\\xff\\xfef\x00j\x00\\xf3\x00r\x00\\xf0\x00a\x00 \x00b\x00a\x00n\x00d\x00"
        )
        self.assertEqual(string, expected_string)

    def testReadUTF8(self):
        """Tests the Read function with UTF-8 encoding."""
        file_object = io.BytesIO(self._TEST_DATA)
        input_reader = tools.FileObjectInputReader(file_object)

        string = input_reader.Read()
        self.assertEqual(string, "A first string\n")

        string = input_reader.Read()
        self.assertEqual(string, "A 2nd string\n")

        # UTF-8 string with non-ASCII characters.
        string = input_reader.Read()
        self.assertEqual(string, "þriðja string\n")

        # UTF-16 string with non-ASCII characters.
        string = input_reader.Read()
        expected_string = (
            "\\xff\\xfef\x00j\x00\\xf3\x00r\x00\\xf0\x00a\x00 \x00b\x00a\x00n\x00d\x00"
        )
        self.assertEqual(string, expected_string)

    def testReadUnicode(self):
        """Tests the Read function on a unicode string."""
        file_object = io.StringIO(self._TEST_STRING_DATA)
        input_reader = tools.FileObjectInputReader(file_object)
        string = input_reader.Read()
        self.assertEqual(string, "A first string\n")

        string = input_reader.Read()
        self.assertEqual(string, "A 2nd string\n")

        string = input_reader.Read()
        self.assertEqual(string, "þriðja string\n")


class StdinInputReaderTest(unittest.TestCase):
    """Tests for the stdin command line interface input reader."""

    def testInitialize(self):
        """Tests the __init__ function."""
        input_reader = tools.StdinInputReader()
        self.assertIsNotNone(input_reader)


class FileObjectOutputWriterTest(unittest.TestCase):
    """Tests for the file object command line interface output writer."""

    def _ReadOutput(self, file_object):
        """Reads all output added since the last call to ReadOutput.

        Args:
          file_object (file): file-like object.

        Returns:
          str: output data.
        """
        file_object.seek(0, os.SEEK_SET)
        output_data = file_object.read()

        file_object.seek(0, os.SEEK_SET)
        file_object.truncate(0)
        return output_data

    def testWriteAscii(self):
        """Tests the Write function with ASCII encoding."""
        file_object = io.BytesIO()
        output_writer = tools.FileObjectOutputWriter(file_object, encoding="ascii")

        output_writer.Write("A first string\n")

        byte_stream = self._ReadOutput(file_object)
        self.assertEqual(byte_stream, b"A first string\n")

        # Unicode string with non-ASCII characters.
        output_writer.Write("þriðja string\n")

        byte_stream = self._ReadOutput(file_object)
        self.assertEqual(byte_stream, b"\\xferi\\xf0ja string\n")

    def testWriteUtf8(self):
        """Tests the Write function with UTF-8 encoding."""
        file_object = io.BytesIO()
        output_writer = tools.FileObjectOutputWriter(file_object)

        output_writer.Write("A first string\n")

        byte_stream = self._ReadOutput(file_object)
        self.assertEqual(byte_stream, b"A first string\n")

        # Unicode string with non-ASCII characters.
        output_writer.Write("þriðja string\n")

        byte_stream = self._ReadOutput(file_object)
        self.assertEqual(byte_stream, b"\xc3\xberi\xc3\xb0ja string\n")


class StdoutOutputWriterTest(unittest.TestCase):
    """Tests for the stdout command line interface output writer."""

    def testWriteAscii(self):
        """Tests the Write function with ASCII encoding."""
        output_writer = tools.StdoutOutputWriter(encoding="ascii")
        output_writer.Write("A first string\n")


if __name__ == "__main__":
    unittest.main()
