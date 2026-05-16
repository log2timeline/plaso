#!/usr/bin/env python3
"""Tests for the pinfo CLI tool."""

import unittest

from plaso.cli import pinfo_tool
from plaso.lib import errors

from tests.cli import test_lib


class PinfoToolTest(test_lib.CLIToolTestCase):
    """Tests for the pinfo CLI tool."""

    # pylint: disable=protected-access

    _EXPECTED_OUTPUT_COMPARE_STORES = """\

************************ Events generated per data type ************************
Data type name : Number of events
--------------------------------------------------------------------------------
       fs:stat : 3 (6)
         total : 3 (38)
--------------------------------------------------------------------------------


************************* Events generated per parser **************************
Parser (plugin) name : Number of events
--------------------------------------------------------------------------------
            filestat : 3 (6)
               total : 3 (38)
--------------------------------------------------------------------------------

Storage files are different.
"""

    # TODO: add test for _CalculateStorageCounters.
    # TODO: add test for _CompareStores.

    def testGenerateAnalysisResultsReportAsJSON(self):
        """Tests the _GenerateAnalysisResultsReport function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "json"

        storage_reader = test_tool._GetStorageReader(test_file_path)
        try:
            column_titles = ["Search engine", "Search term", "Number of queries"]
            attribute_names = ["search_engine", "search_term", "number_of_queries"]
            attribute_mappings = {}
            test_tool._GenerateAnalysisResultsReport(
                storage_reader,
                "browser_searches",
                column_titles,
                "browser_search_analysis_result",
                attribute_names,
                attribute_mappings,
            )

        finally:
            storage_reader.Close()

        expected_output = ['{"browser_searches": [', "", "]}", ""]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateAnalysisResultsReportAsMarkdown(self):
        """Tests the _GenerateAnalysisResultsReport function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "markdown"

        storage_reader = test_tool._GetStorageReader(test_file_path)
        try:
            column_titles = ["Search engine", "Search term", "Number of queries"]
            attribute_names = ["search_engine", "search_term", "number_of_queries"]
            attribute_mappings = {}
            test_tool._GenerateAnalysisResultsReport(
                storage_reader,
                "browser_searches",
                column_titles,
                "browser_search_analysis_result",
                attribute_names,
                attribute_mappings,
            )

        finally:
            storage_reader.Close()

        expected_output = [
            "Search engine | Search term | Number of queries",
            "--- | --- | ---",
            "",
        ]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateAnalysisResultsReportAsText(self):
        """Tests the _GenerateAnalysisResultsReport function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "text"

        storage_reader = test_tool._GetStorageReader(test_file_path)
        try:
            column_titles = ["Search engine", "Search term", "Number of queries"]
            attribute_names = ["search_engine", "search_term", "number_of_queries"]
            attribute_mappings = {}
            test_tool._GenerateAnalysisResultsReport(
                storage_reader,
                "browser_searches",
                column_titles,
                "browser_search_analysis_result",
                attribute_names,
                attribute_mappings,
            )

        finally:
            storage_reader.Close()

        expected_output = ["Search engine\tSearch term\tNumber of queries", ""]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateFileHashesReportAsJSON(self):
        """Tests the _GenerateFileHashesReport function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "json"

        storage_reader = test_tool._GetStorageReader(test_file_path)
        try:
            test_tool._GenerateFileHashesReport(storage_reader)

        finally:
            storage_reader.Close()

        test_file_path = self._GetTestFilePath(["psort_test.plaso.file_hashes.json"])
        with open(test_file_path, encoding="utf-8") as file_object:
            expected_output = file_object.read()

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output.split("\n"))

    def testGenerateFileHashesReportAsMarkdown(self):
        """Tests the _GenerateFileHashesReport function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "markdown"

        storage_reader = test_tool._GetStorageReader(test_file_path)
        try:
            test_tool._GenerateFileHashesReport(storage_reader)

        finally:
            storage_reader.Close()

        test_file_path = self._GetTestFilePath(["psort_test.plaso.file_hashes.md"])
        with open(test_file_path, encoding="utf-8") as file_object:
            expected_output = file_object.read()

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output.split("\n"))

    def testGenerateFileHashesReportAsText(self):
        """Tests the _GenerateFileHashesReport function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "text"

        storage_reader = test_tool._GetStorageReader(test_file_path)
        try:
            test_tool._GenerateFileHashesReport(storage_reader)

        finally:
            storage_reader.Close()

        test_file_path = self._GetTestFilePath(["psort_test.plaso.file_hashes.txt"])
        with open(test_file_path, encoding="utf-8") as file_object:
            expected_output = file_object.read()

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output.split("\n"))

    def testGenerateReportEntryFormatStringAsJSON(self):
        """Tests the _GenerateReportEntryFormatString function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "json"

        attribute_names = ["search_engine", "search_term", "number_of_queries"]

        expected_entry_format_string = (
            '    {{"search_engine": "{search_engine!s}", "search_term": '
            '"{search_term!s}", "number_of_queries": "{number_of_queries!s}"}}'
        )

        entry_format_string = test_tool._GenerateReportEntryFormatString(
            attribute_names
        )
        self.assertEqual(entry_format_string, expected_entry_format_string)

    def testGenerateReportEntryFormatStringAsMarkdown(self):
        """Tests the _GenerateReportEntryFormatString function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "markdown"

        attribute_names = ["search_engine", "search_term", "number_of_queries"]

        expected_entry_format_string = (
            "{search_engine!s} | {search_term!s} | {number_of_queries!s}\n"
        )

        entry_format_string = test_tool._GenerateReportEntryFormatString(
            attribute_names
        )
        self.assertEqual(entry_format_string, expected_entry_format_string)

    def testGenerateReportEntryFormatStringAsText(self):
        """Tests the _GenerateReportEntryFormatString function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "text"

        attribute_names = ["search_engine", "search_term", "number_of_queries"]

        expected_entry_format_string = (
            "{search_engine!s}	{search_term!s}	{number_of_queries!s}\n"
        )

        entry_format_string = test_tool._GenerateReportEntryFormatString(
            attribute_names
        )
        self.assertEqual(entry_format_string, expected_entry_format_string)

    def testGenerateReportFooterAsJSON(self):
        """Tests the _GenerateReportFooter function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "json"

        test_tool._GenerateReportFooter()

        expected_output = ["", "]}", ""]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateReportFooterAsMarkdown(self):
        """Tests the _GenerateReportFooter function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "markdown"

        test_tool._GenerateReportFooter()

        expected_output = [""]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateReportFooterAsText(self):
        """Tests the _GenerateReportFooter function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "text"

        test_tool._GenerateReportFooter()

        expected_output = [""]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateReportHeaderAsJSON(self):
        """Tests the _GenerateReportHeader function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "json"

        column_titles = ["Search engine", "Search term", "Number of queries"]
        test_tool._GenerateReportHeader("browser_searches", column_titles)

        expected_output = ['{"browser_searches": [', ""]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateReportHeaderAsMarkdown(self):
        """Tests the _GenerateReportHeader function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "markdown"

        column_titles = ["Search engine", "Search term", "Number of queries"]
        test_tool._GenerateReportHeader("browser_searches", column_titles)

        expected_output = [
            "Search engine | Search term | Number of queries",
            "--- | --- | ---",
            "",
        ]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateReportHeaderAsText(self):
        """Tests the _GenerateReportHeader function."""
        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "text"

        column_titles = ["Search engine", "Search term", "Number of queries"]
        test_tool._GenerateReportHeader("browser_searches", column_titles)

        expected_output = ["Search engine\tSearch term\tNumber of queries", ""]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateWinEvtProvidersReportAsJSON(self):
        """Tests the _GenerateWinEvtProvidersReport function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "json"

        storage_reader = test_tool._GetStorageReader(test_file_path)
        try:
            test_tool._GenerateWinEvtProvidersReport(storage_reader)

        finally:
            storage_reader.Close()

        expected_output = ['{"winevt_providers": [', "", "]}", ""]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateWinEvtProvidersReportAsMarkdown(self):
        """Tests the _GenerateWinEvtProvidersReport function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "markdown"

        storage_reader = test_tool._GetStorageReader(test_file_path)
        try:
            test_tool._GenerateWinEvtProvidersReport(storage_reader)

        finally:
            storage_reader.Close()

        expected_output = [
            (
                "Identifier | Log source(s) | Log type(s) | Event message file(s) | "
                "Parameter message file(s)"
            ),
            "--- | --- | --- | --- | ---",
            "",
        ]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGenerateWinEvtProvidersReportAsText(self):
        """Tests the _GenerateWinEvtProvidersReport function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "text"

        storage_reader = test_tool._GetStorageReader(test_file_path)
        try:
            test_tool._GenerateWinEvtProvidersReport(storage_reader)

        finally:
            storage_reader.Close()

        expected_output = [
            (
                "Identifier\tLog source(s)\tLog type(s)\tEvent message file(s)\t"
                "Parameter message file(s)"
            ),
            "",
        ]

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output)

    def testGetStorageReader(self):
        """Tests the _GetStorageReader function."""
        test_file_path = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

        storage_reader = test_tool._GetStorageReader(test_file_path)
        try:
            self.assertIsNotNone(storage_reader)
        finally:
            storage_reader.Close()

        with self.assertRaises(errors.BadConfigOption):
            test_tool._GetStorageReader("bogus.plaso")

    # TODO: add test for _PrintAnalysisReportCounter.
    # TODO: add test for _PrintAnalysisReportsDetails.
    # TODO: add test for _PrintExtractionWarningsDetails.
    # TODO: add test for _PrintEventLabelsCounter.
    # TODO: add test for _PrintParsersCounter.
    # TODO: add test for _PrintPreprocessingInformation.
    # TODO: add test for _PrintRecoveryWarningsDetails.
    # TODO: add test for _PrintSessionsDetails.
    # TODO: add test for _PrintSessionsOverview.
    # TODO: add test for _PrintTasksInformation.

    def testCompareStores(self):
        """Tests the CompareStores function."""
        test_file_path1 = self._GetTestFilePath(["psort_test.plaso"])
        self._SkipIfPathNotExists(test_file_path1)

        test_file_path2 = self._GetTestFilePath(["pinfo_test.plaso"])
        self._SkipIfPathNotExists(test_file_path2)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.compare_storage_file = test_file_path1
        options.storage_file = test_file_path1

        test_tool.ParseOptions(options)

        self.assertTrue(test_tool.CompareStores())

        output = output_writer.ReadOutput()
        self.assertEqual(output, "Storage files are identical.\n")

        options = test_lib.TestOptions()
        options.compare_storage_file = test_file_path1
        options.storage_file = test_file_path2

        test_tool.ParseOptions(options)

        self.assertFalse(test_tool.CompareStores())

        output = output_writer.ReadOutput()
        self.assertEqual(output, self._EXPECTED_OUTPUT_COMPARE_STORES)

    def testParseArguments(self):
        """Tests the ParseArguments function."""
        output_writer = test_lib.TestBinaryOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

        result = test_tool.ParseArguments([])
        self.assertFalse(result)

        # TODO: check output.
        # TODO: improve test coverage.

    def testParseOptions(self):
        """Tests the ParseOptions function."""
        test_file_path = self._GetTestFilePath(["pinfo_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.storage_file = test_file_path

        test_tool.ParseOptions(options)

        options = test_lib.TestOptions()

        with self.assertRaises(errors.BadConfigOption):
            test_tool.ParseOptions(options)

        # TODO: improve test coverage.

    def testPrintStorageInformation(self):
        """Tests the PrintStorageInformation function."""
        test_file_path = self._GetTestFilePath(["pinfo_test.plaso"])
        self._SkipIfPathNotExists(test_file_path)

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

        options = test_lib.TestOptions()
        options.storage_file = test_file_path
        options.output_format = "text"
        options.sections = "events,reports,sessions,warnings"

        test_tool.ParseOptions(options)

        test_tool.PrintStorageInformation()

        test_file_path = self._GetTestFilePath(["pinfo_test.plaso.output.txt"])
        with open(test_file_path, encoding="utf-8") as file_object:
            expected_output = file_object.read()

        output = output_writer.ReadOutput()

        # Compare the output as list of lines which makes it easier to spot
        # differences.
        self.assertEqual(output.split("\n"), expected_output.split("\n"))


if __name__ == "__main__":
    unittest.main()
