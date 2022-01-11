#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the pinfo CLI tool."""

import json
import unittest

from plaso.cli import views as cli_views
from plaso.cli import pinfo_tool
from plaso.lib import errors

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class PinfoToolTest(test_lib.CLIToolTestCase):
  """Tests for the pinfo CLI tool."""

  # pylint: disable=protected-access

  _EXPECTED_OUTPUT_COMPARE_STORES = """\

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
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'json'

    storage_reader = test_tool._GetStorageReader(test_file_path)
    try:
      column_titles = ['Search engine', 'Search term', 'Number of queries']
      attribute_names = ['search_engine', 'search_term', 'number_of_queries']
      attribute_mappings = {}
      test_tool._GenerateAnalysisResultsReport(
          storage_reader, 'browser_searches', column_titles,
          'browser_search_analysis_result', attribute_names,
          attribute_mappings)

    finally:
      storage_reader.Close()

    expected_output = [
        '{"browser_searches": [', '', ']}',
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateAnalysisResultsReportAsMarkdown(self):
    """Tests the _GenerateAnalysisResultsReport function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'markdown'

    storage_reader = test_tool._GetStorageReader(test_file_path)
    try:
      column_titles = ['Search engine', 'Search term', 'Number of queries']
      attribute_names = ['search_engine', 'search_term', 'number_of_queries']
      attribute_mappings = {}
      test_tool._GenerateAnalysisResultsReport(
          storage_reader, 'browser_searches', column_titles,
          'browser_search_analysis_result', attribute_names,
          attribute_mappings)

    finally:
      storage_reader.Close()

    expected_output = [
        'Search engine | Search term | Number of queries',
        '--- | --- | ---',
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateAnalysisResultsReportAsText(self):
    """Tests the _GenerateAnalysisResultsReport function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'text'

    storage_reader = test_tool._GetStorageReader(test_file_path)
    try:
      column_titles = ['Search engine', 'Search term', 'Number of queries']
      attribute_names = ['search_engine', 'search_term', 'number_of_queries']
      attribute_mappings = {}
      test_tool._GenerateAnalysisResultsReport(
          storage_reader, 'browser_searches', column_titles,
          'browser_search_analysis_result', attribute_names,
          attribute_mappings)

    finally:
      storage_reader.Close()

    expected_output = [
        'Search engine\tSearch term\tNumber of queries',
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateFileHashesReportAsJSON(self):
    """Tests the _GenerateFileHashesReport function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'json'

    storage_reader = test_tool._GetStorageReader(test_file_path)
    try:
      test_tool._GenerateFileHashesReport(storage_reader)

    finally:
      storage_reader.Close()

    expected_output = [
        '{"file_hashes": [',
        ('    {"sha256_hash": '
         '"1f0105612f6ad2d225d6bd9ba631148740e312598878adcd2b74098a3dab50c4", '
         '"display_name": "OS:/tmp/test/test_data/syslog"},'),
        ('    {"sha256_hash": '
         '"1f0105612f6ad2d225d6bd9ba631148740e312598878adcd2b74098a3dab50c4", '
         '"display_name": "OS:/tmp/test/test_data/syslog"}'),
        ']}',
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateFileHashesReportAsMarkdown(self):
    """Tests the _GenerateFileHashesReport function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'markdown'

    storage_reader = test_tool._GetStorageReader(test_file_path)
    try:
      test_tool._GenerateFileHashesReport(storage_reader)

    finally:
      storage_reader.Close()

    expected_output = [
        'SHA256 hash | Display name',
        '--- | ---',
        ('1f0105612f6ad2d225d6bd9ba631148740e312598878adcd2b74098a3dab50c4 | '
         'OS:/tmp/test/test_data/syslog'),
        ('1f0105612f6ad2d225d6bd9ba631148740e312598878adcd2b74098a3dab50c4 | '
         'OS:/tmp/test/test_data/syslog'),
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateFileHashesReportAsText(self):
    """Tests the _GenerateFileHashesReport function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'text'

    storage_reader = test_tool._GetStorageReader(test_file_path)
    try:
      test_tool._GenerateFileHashesReport(storage_reader)

    finally:
      storage_reader.Close()

    expected_output = [
        'SHA256 hash\tDisplay name',
        ('1f0105612f6ad2d225d6bd9ba631148740e312598878adcd2b74098a3dab50c4\t'
         'OS:/tmp/test/test_data/syslog'),
        ('1f0105612f6ad2d225d6bd9ba631148740e312598878adcd2b74098a3dab50c4\t'
         'OS:/tmp/test/test_data/syslog'),
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateReportEntryFormatStringAsJSON(self):
    """Tests the _GenerateReportEntryFormatString function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'json'

    attribute_names = ['search_engine', 'search_term', 'number_of_queries']

    expected_entry_format_string = (
        '    {{"search_engine": "{search_engine!s}", "search_term": '
        '"{search_term!s}", "number_of_queries": "{number_of_queries!s}"}}')

    entry_format_string = test_tool._GenerateReportEntryFormatString(
        attribute_names)
    self.assertEqual(entry_format_string, expected_entry_format_string)

  def testGenerateReportEntryFormatStringAsMarkdown(self):
    """Tests the _GenerateReportEntryFormatString function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'markdown'

    attribute_names = ['search_engine', 'search_term', 'number_of_queries']

    expected_entry_format_string = (
        '{search_engine!s} | {search_term!s} | {number_of_queries!s}\n')

    entry_format_string = test_tool._GenerateReportEntryFormatString(
        attribute_names)
    self.assertEqual(entry_format_string, expected_entry_format_string)

  def testGenerateReportEntryFormatStringAsText(self):
    """Tests the _GenerateReportEntryFormatString function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'text'

    attribute_names = ['search_engine', 'search_term', 'number_of_queries']

    expected_entry_format_string = (
        '{search_engine!s}	{search_term!s}	{number_of_queries!s}\n')

    entry_format_string = test_tool._GenerateReportEntryFormatString(
        attribute_names)
    self.assertEqual(entry_format_string, expected_entry_format_string)

  def testGenerateReportFooterAsJSON(self):
    """Tests the _GenerateReportFooter function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'json'

    test_tool._GenerateReportFooter()

    expected_output = ['', ']}', '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateReportFooterAsMarkdown(self):
    """Tests the _GenerateReportFooter function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'markdown'

    test_tool._GenerateReportFooter()

    expected_output = ['']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateReportFooterAsText(self):
    """Tests the _GenerateReportFooter function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'text'

    test_tool._GenerateReportFooter()

    expected_output = ['']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateReportHeaderAsJSON(self):
    """Tests the _GenerateReportHeader function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'json'

    column_titles = ['Search engine', 'Search term', 'Number of queries']
    test_tool._GenerateReportHeader('browser_searches', column_titles)

    expected_output = [
        '{"browser_searches": [',
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateReportHeaderAsMarkdown(self):
    """Tests the _GenerateReportHeader function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'markdown'

    column_titles = ['Search engine', 'Search term', 'Number of queries']
    test_tool._GenerateReportHeader('browser_searches', column_titles)

    expected_output = [
        'Search engine | Search term | Number of queries',
        '--- | --- | ---',
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateReportHeaderAsText(self):
    """Tests the _GenerateReportHeader function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'text'

    column_titles = ['Search engine', 'Search term', 'Number of queries']
    test_tool._GenerateReportHeader('browser_searches', column_titles)

    expected_output = [
        'Search engine\tSearch term\tNumber of queries',
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateWinEvtProvidersReportAsJSON(self):
    """Tests the _GenerateWinEvtProvidersReport function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'json'

    storage_reader = test_tool._GetStorageReader(test_file_path)
    try:
      test_tool._GenerateWinEvtProvidersReport(storage_reader)

    finally:
      storage_reader.Close()

    expected_output = [
        '{"winevt_providers": [', '', ']}',
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateWinEvtProvidersReportAsMarkdown(self):
    """Tests the _GenerateWinEvtProvidersReport function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'markdown'

    storage_reader = test_tool._GetStorageReader(test_file_path)
    try:
      test_tool._GenerateWinEvtProvidersReport(storage_reader)

    finally:
      storage_reader.Close()

    expected_output = [
        'Log source | Log type | Event message file(s)',
        '--- | --- | ---',
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGenerateWinEvtProvidersReportAsText(self):
    """Tests the _GenerateWinEvtProvidersReport function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool._output_format = 'text'

    storage_reader = test_tool._GetStorageReader(test_file_path)
    try:
      test_tool._GenerateWinEvtProvidersReport(storage_reader)

    finally:
      storage_reader.Close()

    expected_output = [
        'Log source\tLog type\tEvent message file(s)',
        '']

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output)

  def testGetStorageReader(self):
    """Tests the _GetStorageReader function."""
    test_file_path = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    storage_reader = test_tool._GetStorageReader(test_file_path)
    try:
      self.assertIsNotNone(storage_reader)
    finally:
      storage_reader.Close()

    with self.assertRaises(errors.BadConfigOption):
      test_tool._GetStorageReader('bogus.plaso')

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
    test_file_path1 = self._GetTestFilePath(['psort_test.plaso'])
    self._SkipIfPathNotExists(test_file_path1)

    test_file_path2 = self._GetTestFilePath(['pinfo_test.plaso'])
    self._SkipIfPathNotExists(test_file_path2)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.compare_storage_file = test_file_path1
    options.storage_file = test_file_path1

    test_tool.ParseOptions(options)

    self.assertTrue(test_tool.CompareStores())

    output = output_writer.ReadOutput()
    self.assertEqual(output, 'Storage files are identical.\n')

    options = test_lib.TestOptions()
    options.compare_storage_file = test_file_path1
    options.storage_file = test_file_path2

    test_tool.ParseOptions(options)

    self.assertFalse(test_tool.CompareStores())

    output = output_writer.ReadOutput()
    self.assertEqual(output, self._EXPECTED_OUTPUT_COMPARE_STORES)

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestBinaryOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    result = test_tool.ParseArguments([])
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    test_file_path = self._GetTestFilePath(['pinfo_test.plaso'])
    self._SkipIfPathNotExists(test_file_path)

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.storage_file = test_file_path

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  def testPrintStorageInformationAsJSON(self):
    """Tests the PrintStorageInformation function with JSON output format."""
    test_filename = 'pinfo_test.plaso'
    session_identifier = '17c2f64c-ff4c-493d-b79d-18f31deaf7d5'
    session_start_time = '2021-11-21 16:57:49.936026'

    test_file_path = self._GetTestFilePath([test_filename])
    self._SkipIfPathNotExists(test_file_path)

    options = test_lib.TestOptions()
    options.storage_file = test_file_path
    options.output_format = 'json'
    options.sections = 'events,reports,sessions,warnings'

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool.ParseOptions(options)

    test_tool.PrintStorageInformation()
    output = output_writer.ReadOutput()
    json_output = json.loads(output)

    sessions = json_output.get('sessions')
    self.assertIsNotNone(sessions)

    first_session = sessions.get('session')
    self.assertIsNotNone(first_session)

    self.assertEqual(
        first_session['identifier'], session_identifier.replace('-', ''))

    expected_start_time = shared_test_lib.CopyTimestampFromString(
        session_start_time)
    self.assertEqual(first_session['start_time'], expected_start_time)

    storage_counters = json_output.get('storage_counters')
    self.assertIsNotNone(storage_counters)

    parsers_counter = storage_counters['parsers']
    self.assertIsNotNone(parsers_counter)
    self.assertEqual(parsers_counter['total'], 3)
    self.assertEqual(parsers_counter['filestat'], 3)

  def testPrintStorageInformationAsText(self):
    """Tests the PrintStorageInformation function with text output format."""
    test_filename = 'pinfo_test.plaso'
    format_version = '20211121'
    plaso_version = '20211106'
    session_identifier = '17c2f64c-ff4c-493d-b79d-18f31deaf7d5'
    session_start_time = '2021-11-21T16:57:49.936026+00:00'
    session_completion_time = '2021-11-21T16:57:58.645043+00:00'

    command_line_arguments = (
        './tools/log2timeline.py --partition=all --quiet '
        '--storage-file pinfo_test.plaso test_data/tsk_volume_system.raw')

    enabled_parser_names = ', '.join([
        'android_app_usage',
        'apache_access',
        'apt_history',
        'asl_log',
        'bash_history',
        'bencode',
        'bencode/bencode_transmission',
        'bencode/bencode_utorrent',
        'binary_cookies',
        'bsm_log',
        'chrome_cache',
        'chrome_preferences',
        'cups_ipp',
        'custom_destinations',
        'czip',
        'czip/oxml',
        'dockerjson',
        'dpkg',
        'esedb',
        'esedb/file_history',
        'esedb/msie_webcache',
        'esedb/srum',
        'filestat',
        'firefox_cache',
        'firefox_cache2',
        'fish_history',
        'fseventsd',
        'gdrive_synclog',
        'googlelog',
        'java_idx',
        'lnk',
        'locate_database',
        'mac_appfirewall_log',
        'mac_keychain',
        'mac_securityd',
        'mactime',
        'macwifi',
        'mcafee_protection',
        'mft',
        'msiecf',
        'networkminer_fileinfo',
        'olecf',
        'olecf/olecf_automatic_destinations',
        'olecf/olecf_default',
        'olecf/olecf_document_summary',
        'olecf/olecf_summary',
        'opera_global',
        'opera_typed_history',
        'pe',
        'plist',
        'plist/airport',
        'plist/apple_id',
        'plist/ipod_device',
        'plist/launchd_plist',
        'plist/macos_software_update',
        'plist/macosx_bluetooth',
        'plist/macosx_install_history',
        'plist/macuser',
        'plist/plist_default',
        'plist/safari_history',
        'plist/spotlight',
        'plist/spotlight_volume',
        'plist/time_machine',
        'pls_recall',
        'popularity_contest',
        'prefetch',
        'recycle_bin',
        'recycle_bin_info2',
        'rplog',
        'santa',
        'sccm',
        'selinux',
        'setupapi',
        'skydrive_log',
        'skydrive_log_old',
        'sophos_av',
        'spotlight_storedb',
        'sqlite',
        'sqlite/android_calls',
        'sqlite/android_sms',
        'sqlite/android_webview',
        'sqlite/android_webviewcache',
        'sqlite/appusage',
        'sqlite/chrome_17_cookies',
        'sqlite/chrome_27_history',
        'sqlite/chrome_66_cookies',
        'sqlite/chrome_8_history',
        'sqlite/chrome_autofill',
        'sqlite/chrome_extension_activity',
        'sqlite/firefox_cookies',
        'sqlite/firefox_downloads',
        'sqlite/firefox_history',
        'sqlite/google_drive',
        'sqlite/hangouts_messages',
        'sqlite/imessage',
        'sqlite/kik_messenger',
        'sqlite/kodi',
        'sqlite/ls_quarantine',
        'sqlite/mac_document_versions',
        'sqlite/mac_knowledgec',
        'sqlite/mac_notes',
        'sqlite/mac_notificationcenter',
        'sqlite/mackeeper_cache',
        'sqlite/macostcc',
        'sqlite/safari_historydb',
        'sqlite/skype',
        'sqlite/tango_android_profile',
        'sqlite/tango_android_tc',
        'sqlite/twitter_android',
        'sqlite/twitter_ios',
        'sqlite/windows_eventtranscript',
        'sqlite/windows_timeline',
        'sqlite/zeitgeist',
        'symantec_scanlog',
        'syslog',
        'syslog/cron',
        'syslog/ssh',
        'systemd_journal',
        'trendmicro_url',
        'trendmicro_vd',
        'usnjrnl',
        'utmp',
        'utmpx',
        'vsftpd',
        'winevt',
        'winevtx',
        'winfirewall',
        'winiis',
        'winjob',
        'winreg',
        'winreg/amcache',
        'winreg/appcompatcache',
        'winreg/bagmru',
        'winreg/bam',
        'winreg/ccleaner',
        'winreg/explorer_mountpoints2',
        'winreg/explorer_programscache',
        'winreg/microsoft_office_mru',
        'winreg/microsoft_outlook_mru',
        'winreg/mrulist_shell_item_list',
        'winreg/mrulist_string',
        'winreg/mrulistex_shell_item_list',
        'winreg/mrulistex_string',
        'winreg/mrulistex_string_and_shell_item',
        'winreg/mrulistex_string_and_shell_item_list',
        'winreg/msie_zone',
        'winreg/mstsc_rdp',
        'winreg/mstsc_rdp_mru',
        'winreg/network_drives',
        'winreg/networks',
        'winreg/userassist',
        'winreg/windows_boot_execute',
        'winreg/windows_boot_verify',
        'winreg/windows_run',
        'winreg/windows_sam_users',
        'winreg/windows_services',
        'winreg/windows_shutdown',
        'winreg/windows_task_cache',
        'winreg/windows_timezone',
        'winreg/windows_typed_urls',
        'winreg/windows_usb_devices',
        'winreg/windows_usbstor_devices',
        'winreg/windows_version',
        'winreg/winlogon',
        'winreg/winrar_mru',
        'winreg/winreg_default',
        'xchatlog',
        'xchatscrollback',
        'zsh_extended_history'])

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')

    table_view = cli_views.ViewsFactory.GetTableView(
        cli_views.ViewsFactory.FORMAT_TYPE_CLI,
        title='Plaso Storage Information')
    table_view.AddRow(['Filename', test_filename])
    table_view.AddRow(['Format version', format_version])
    table_view.AddRow(['Serialization format', 'json'])
    table_view.Write(output_writer)

    table_view = cli_views.ViewsFactory.GetTableView(
        cli_views.ViewsFactory.FORMAT_TYPE_CLI, title='Sessions')
    table_view.AddRow([session_identifier, session_start_time])
    table_view.Write(output_writer)

    title = 'Session: {0!s}'.format(session_identifier)
    table_view = cli_views.ViewsFactory.GetTableView(
        cli_views.ViewsFactory.FORMAT_TYPE_CLI, title=title)
    table_view.AddRow(['Start time', session_start_time])
    table_view.AddRow(['Completion time', session_completion_time])
    table_view.AddRow(['Product name', 'plaso'])
    table_view.AddRow(['Product version', plaso_version])
    table_view.AddRow(['Command line arguments', command_line_arguments])
    table_view.AddRow(['Parser filter expression', 'N/A'])
    table_view.AddRow(['Enabled parser and plugins', enabled_parser_names])
    table_view.AddRow(['Preferred encoding', 'UTF-8'])
    table_view.AddRow(['Debug mode', 'False'])
    table_view.AddRow(['Artifact filters', 'N/A'])
    table_view.AddRow(['Filter file', 'N/A'])
    table_view.Write(output_writer)

    table_view = cli_views.ViewsFactory.GetTableView(
        cli_views.ViewsFactory.FORMAT_TYPE_CLI,
        column_names=['Parser (plugin) name', 'Number of events'],
        title='Events generated per parser')
    table_view.AddRow(['filestat', '3'])
    table_view.AddRow(['Total', '3'])
    table_view.Write(output_writer)

    expected_output = output_writer.ReadOutput()

    expected_output = (
        '{0:s}'
        '\n'
        'No events labels stored.\n'
        '\n'
        'No warnings stored.\n'
        '\n'
        'No analysis reports stored.\n'
        '\n').format(expected_output)

    test_file_path = self._GetTestFilePath([test_filename])
    self._SkipIfPathNotExists(test_file_path)

    options = test_lib.TestOptions()
    options.storage_file = test_file_path
    options.output_format = 'text'
    options.sections = 'events,reports,sessions,warnings'

    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool.ParseOptions(options)

    test_tool.PrintStorageInformation()

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output.split('\n'))


if __name__ == '__main__':
  unittest.main()
