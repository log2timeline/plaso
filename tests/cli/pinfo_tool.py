#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the pinfo CLI tool."""

from __future__ import unicode_literals

import json
import unittest

from plaso.cli import views as cli_views
from plaso.cli import pinfo_tool
from plaso.lib import errors
from plaso.lib import timelib

from tests import test_lib as shared_test_lib
from tests.cli import test_lib


class PinfoToolTest(test_lib.CLIToolTestCase):
  """Tests for the pinfo CLI tool."""

  # TODO: add test for _CalculateStorageCounters.
  # TODO: add test for _CompareStores.
  # TODO: add test for _PrintAnalysisReportCounter.
  # TODO: add test for _PrintAnalysisReportsDetails.
  # TODO: add test for _PrintErrorsDetails.
  # TODO: add test for _PrintEventLabelsCounter.
  # TODO: add test for _PrintParsersCounter.
  # TODO: add test for _PrintPreprocessingInformation.
  # TODO: add test for _PrintSessionsDetails.
  # TODO: add test for _PrintSessionsOverview.
  # TODO: add test for _PrintTasksInformation.
  # TODO: add test for _PrintStorageInformationAsText.

  @shared_test_lib.skipUnlessHasTestFile(['pinfo_test.plaso'])
  @shared_test_lib.skipUnlessHasTestFile(['psort_test.plaso'])
  def testCompareStores(self):
    """Tests the CompareStores function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    test_file1 = self._GetTestFilePath(['psort_test.plaso'])
    test_file2 = self._GetTestFilePath(['pinfo_test.plaso'])

    options = test_lib.TestOptions()
    options.compare_storage_file = test_file1
    options.storage_file = test_file1

    test_tool.ParseOptions(options)

    self.assertTrue(test_tool.CompareStores())

    output = output_writer.ReadOutput()
    self.assertEqual(output, 'Storage files are identical.\n')

    options = test_lib.TestOptions()
    options.compare_storage_file = test_file1
    options.storage_file = test_file2

    test_tool.ParseOptions(options)

    self.assertFalse(test_tool.CompareStores())

    output = output_writer.ReadOutput()
    self.assertEqual(output, 'Storage files are different.\n')

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestBinaryOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    result = test_tool.ParseArguments()
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  @shared_test_lib.skipUnlessHasTestFile(['pinfo_test.plaso'])
  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath(['pinfo_test.plaso'])

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  @shared_test_lib.skipUnlessHasTestFile(['pinfo_test.plaso'])
  def testPrintStorageInformationAsText(self):
    """Tests the _PrintStorageInformationAsText function."""
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    test_filename = 'pinfo_test.plaso'
    format_version = '20170707'
    plaso_version = '20171228'
    session_identifier = 'd280b33c-845b-4e8b-b3d0-b33da11b180b'
    session_start_time = '2017-12-28T20:06:34.578880+00:00'
    session_completion_time = '2017-12-28T20:06:35.367057+00:00'

    command_line_arguments = (
        './tools/log2timeline.py --partition=all --quiet '
        'pinfo_test.json.plaso test_data/tsk_volume_system.raw')

    enabled_parser_names = ', '.join([
        'amcache', 'android_app_usage', 'asl_log', 'bash', 'bencode',
        'bencode/bencode_transmission', 'bencode/bencode_utorrent',
        'binary_cookies', 'bsm_log', 'chrome_cache', 'chrome_preferences',
        'cups_ipp', 'custom_destinations', 'dockerjson', 'dpkg', 'esedb',
        'esedb/esedb_file_history', 'esedb/msie_webcache', 'filestat',
        'firefox_cache', 'firefox_cache2', 'hachoir', 'java_idx', 'lnk',
        'mac_appfirewall_log', 'mac_keychain', 'mac_securityd', 'mactime',
        'macwifi', 'mcafee_protection', 'mft', 'msiecf', 'olecf',
        'olecf/olecf_automatic_destinations', 'olecf/olecf_default',
        'olecf/olecf_document_summary', 'olecf/olecf_summary', 'openxml',
        'opera_global', 'opera_typed_history', 'pe', 'plist',
        'plist/airport', 'plist/apple_id', 'plist/ipod_device',
        'plist/macosx_bluetooth', 'plist/macosx_install_history',
        'plist/macuser', 'plist/maxos_software_update',
        'plist/plist_default', 'plist/safari_history', 'plist/spotlight',
        'plist/spotlight_volume', 'plist/time_machine', 'pls_recall',
        'popularity_contest', 'prefetch', 'recycle_bin',
        'recycle_bin_info2', 'rplog', 'sccm', 'selinux', 'skydrive_log',
        'skydrive_log_old', 'sophos_av', 'sqlite', 'sqlite/android_calls',
        'sqlite/android_sms', 'sqlite/android_webview',
        'sqlite/android_webviewcache', 'sqlite/appusage',
        'sqlite/chrome_cookies', 'sqlite/chrome_extension_activity',
        'sqlite/chrome_history', 'sqlite/firefox_cookies',
        'sqlite/firefox_downloads', 'sqlite/firefox_history',
        'sqlite/google_drive', 'sqlite/imessage',
        'sqlite/kik_messenger', 'sqlite/ls_quarantine',
        'sqlite/mac_document_versions', 'sqlite/mackeeper_cache',
        'sqlite/skype', 'sqlite/twitter_ios', 'sqlite/zeitgeist',
        'symantec_scanlog', 'syslog', 'syslog/cron', 'syslog/ssh',
        'systemd_journal', 'usnjrnl', 'utmp', 'utmpx', 'winevt',
        'winevtx', 'winfirewall', 'winiis', 'winjob', 'winreg',
        'winreg/appcompatcache', 'winreg/bagmru', 'winreg/ccleaner',
        'winreg/explorer_mountpoints2', 'winreg/explorer_programscache',
        'winreg/microsoft_office_mru', 'winreg/microsoft_outlook_mru',
        'winreg/mrulist_shell_item_list', 'winreg/mrulist_string',
        'winreg/mrulistex_shell_item_list', 'winreg/mrulistex_string',
        'winreg/mrulistex_string_and_shell_item',
        'winreg/mrulistex_string_and_shell_item_list', 'winreg/msie_zone',
        'winreg/mstsc_rdp', 'winreg/mstsc_rdp_mru', 'winreg/network_drives',
        'winreg/userassist', 'winreg/windows_boot_execute',
        'winreg/windows_boot_verify', 'winreg/windows_run',
        'winreg/windows_sam_users', 'winreg/windows_services',
        'winreg/windows_shutdown', 'winreg/windows_task_cache',
        'winreg/windows_timezone', 'winreg/windows_typed_urls',
        'winreg/windows_usb_devices', 'winreg/windows_usbstor_devices',
        'winreg/windows_version', 'winreg/winlogon', 'winreg/winrar_mru',
        'winreg/winreg_default', 'xchatlog', 'xchatscrollback',
        'zsh_extended_history'])

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
        'No errors stored.\n'
        '\n'
        'No analysis reports stored.\n'
        '\n').format(expected_output)

    test_file = self._GetTestFilePath([test_filename])

    options = test_lib.TestOptions()
    options.storage_file = test_file
    options.output_format = 'text'

    test_tool.ParseOptions(options)

    test_tool.PrintStorageInformation()

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output.split('\n'))

  @shared_test_lib.skipUnlessHasTestFile(['pinfo_test.plaso'])
  def testPrintStorageInformationAsJSON(self):
    """Tests the _PrintStorageInformationAsJSON function."""
    test_filename = 'pinfo_test.plaso'
    session_identifier = 'd280b33c845b4e8bb3d0b33da11b180b'
    session_start_time = timelib.Timestamp.CopyFromString(
        '2017-12-28 20:06:34.578880')
    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_file = self._GetTestFilePath([test_filename])

    options = test_lib.TestOptions()
    options.storage_file = test_file
    options.output_format = 'json'

    test_tool.ParseOptions(options)

    test_tool.PrintStorageInformation()
    output = output_writer.ReadOutput()
    json_output = json.loads(output)

    first_session_identifier = 'session_{0:s}'.format(session_identifier)
    first_session = json_output.get(first_session_identifier, None)
    self.assertIsNotNone(first_session)

    self.assertEqual(first_session['identifier'], session_identifier)
    self.assertEqual(first_session['start_time'], session_start_time)

    parsers_counter = first_session['parsers_counter']
    self.assertEqual(parsers_counter['total'], 3)
    self.assertEqual(parsers_counter['filestat'], 3)


if __name__ == '__main__':
  unittest.main()
