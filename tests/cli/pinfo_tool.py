#!/usr/bin/env python3
"""Tests for the pinfo CLI tool."""

import json
import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.cli import pinfo_tool
from plaso.containers import artifacts
from plaso.containers import counts
from plaso.containers import events
from plaso.engine import path_helper
from plaso.lib import definitions
from plaso.lib import errors
from plaso.storage import factory as storage_factory

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class PinfoToolTest(test_lib.CLIToolTestCase):
    """Tests for the pinfo CLI tool."""

    # pylint: disable=protected-access

    _EXPECTED_OUTPUT_COMPARE_STORES = """\

************************ Events generated per data type ************************
      Data type name : Number of events
--------------------------------------------------------------------------------
             fs:stat : 3 (6)
syslog:cron:task_run : 0 (6)
         syslog:line : 0 (26)
               total : 3 (38)
--------------------------------------------------------------------------------


************************* Events generated per parser **************************
Parser (plugin) name : Number of events
--------------------------------------------------------------------------------
            filestat : 3 (6)
  syslog_traditional : 0 (32)
               total : 3 (38)
--------------------------------------------------------------------------------


******************* Extraction warnings generated per parser *******************
   Parser (plugin) name : Number of warnings
--------------------------------------------------------------------------------
text/syslog_traditional : 0 (2)
--------------------------------------------------------------------------------


******************* Pathspecs with most extraction warnings ********************
Number of warnings : Pathspec
--------------------------------------------------------------------------------
             0 (2) : type: OS, location: /tmp/test/test_data/syslog/syslog\\x0a
--------------------------------------------------------------------------------


************************ Event tags generated per label ************************
   Label : Number of event tags
--------------------------------------------------------------------------------
   exit1 : 0 (2)
   exit2 : 0 (2)
repeated : 0 (4)
   total : 0 (8)
--------------------------------------------------------------------------------

Storage files are different.
"""

    _EXPECTED_OUTPUT_COMPARE_STORES_REVERSED = """\

************************ Events generated per data type ************************
      Data type name : Number of events
--------------------------------------------------------------------------------
             fs:stat : 6 (3)
syslog:cron:task_run : 6 (0)
         syslog:line : 26 (0)
               total : 38 (3)
--------------------------------------------------------------------------------


************************* Events generated per parser **************************
Parser (plugin) name : Number of events
--------------------------------------------------------------------------------
            filestat : 6 (3)
  syslog_traditional : 32 (0)
               total : 38 (3)
--------------------------------------------------------------------------------


******************* Extraction warnings generated per parser *******************
   Parser (plugin) name : Number of warnings
--------------------------------------------------------------------------------
text/syslog_traditional : 2 (0)
--------------------------------------------------------------------------------


******************* Pathspecs with most extraction warnings ********************
Number of warnings : Pathspec
--------------------------------------------------------------------------------
             2 (0) : type: OS, location: /tmp/test/test_data/syslog/syslog\\x0a
--------------------------------------------------------------------------------


************************ Event tags generated per label ************************
   Label : Number of event tags
--------------------------------------------------------------------------------
   exit1 : 2 (0)
   exit2 : 2 (0)
repeated : 4 (0)
   total : 8 (0)
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

    def testGenerateAnalysisResultsReportAsJSONWithQuotedValue(self):
        """Tests the _GenerateAnalysisResultsReport function with a quoted value."""
        image_path = '"C:\\Program Files\\Foo\\svc.exe" -k netsvcs'

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "json"

        with shared_test_lib.TempDirectory() as temp_directory:
            temp_file = os.path.join(temp_directory, "storage.plaso")

            storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
                definitions.DEFAULT_STORAGE_FORMAT
            )
            storage_writer.Open(path=temp_file)
            try:
                service_configuration = artifacts.WindowsServiceConfigurationArtifact(
                    name="Foo", service_type=0x10, start_type=2
                )
                service_configuration.image_path = image_path
                storage_writer.AddAttributeContainer(service_configuration)

            finally:
                storage_writer.Close()

            storage_reader = test_tool._GetStorageReader(temp_file)
            try:
                column_titles = ["Name", "Service type", "Start type", "Image path"]
                attribute_names = ["name", "service_type", "start_type", "image_path"]
                attribute_mappings = {}
                test_tool._GenerateAnalysisResultsReport(
                    storage_reader,
                    "windows_services",
                    column_titles,
                    "windows_service_configuration",
                    attribute_names,
                    attribute_mappings,
                )

            finally:
                storage_reader.Close()

        output = output_writer.ReadOutput()

        json_dict = json.loads(output)
        self.assertEqual(json_dict["windows_services"][0]["image_path"], image_path)

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

    def testGenerateFileHashesReportAsJSONWithQuotedDisplayName(self):
        """Tests the _GenerateFileHashesReport function with a quoted name."""
        location = '/tmp/a"b\\c'
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=location
        )
        # The OS display name is platform dependent, for example it gains
        # a drive letter on Windows.
        expected_display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
            path_spec
        )

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "json"

        with shared_test_lib.TempDirectory() as temp_directory:
            temp_file = os.path.join(temp_directory, "storage.plaso")

            storage_writer = storage_factory.StorageFactory.CreateStorageWriter(
                definitions.DEFAULT_STORAGE_FORMAT
            )
            storage_writer.Open(path=temp_file)
            try:
                event_data_stream = events.EventDataStream()
                event_data_stream.path_spec = path_spec
                event_data_stream.sha256_hash = "0" * 64
                storage_writer.AddAttributeContainer(event_data_stream)

            finally:
                storage_writer.Close()

            storage_reader = test_tool._GetStorageReader(temp_file)
            try:
                test_tool._GenerateFileHashesReport(storage_reader)

            finally:
                storage_reader.Close()

        output = output_writer.ReadOutput()

        json_dict = json.loads(output)
        self.assertIn('a"b', expected_display_name)
        self.assertEqual(
            json_dict["file_hashes"][0]["display_name"], expected_display_name
        )

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

    def testPrintWarningCountersJSON(self):
        """Tests the _PrintWarningCountersJSON function."""
        path_spec_key = (
            'type: OS, location: C:\\image"1.raw\ntype: NTFS, '
            "location: \\Windows\\System32\n"
        )
        warnings_by_path_spec = {path_spec_key: counts.WarningCount(number_of_events=2)}
        warnings_by_parser_chain = {"winreg": counts.WarningCount(number_of_events=2)}

        output_writer = test_lib.TestOutputWriter(encoding="utf-8")
        test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
        test_tool._output_format = "json"

        test_tool._PrintWarningCountersJSON(
            warnings_by_path_spec, warnings_by_parser_chain
        )

        output = output_writer.ReadOutput()

        json_dict = json.loads(f"{{{output:s}}}")
        self.assertEqual(json_dict["warnings_by_parser"], {"winreg": 2})
        self.assertEqual(json_dict["warnings_by_path_spec"], {path_spec_key: 2})

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

        options = test_lib.TestOptions()
        options.compare_storage_file = test_file_path2
        options.storage_file = test_file_path1

        test_tool.ParseOptions(options)

        self.assertFalse(test_tool.CompareStores())

        output = output_writer.ReadOutput()
        self.assertEqual(output, self._EXPECTED_OUTPUT_COMPARE_STORES_REVERSED)

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
