#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the pinfo CLI tool."""

import json
import unittest

from plaso.cli import views as cli_views
from plaso.cli import pinfo_tool
from plaso.lib import errors
from plaso.lib import timelib

from tests.cli import test_lib


class PinfoToolTest(test_lib.CLIToolTestCase):
  """Tests for the pinfo CLI tool."""

  # TODO: add test for _CalculateStorageCounters.
  # TODO: add test for _CompareStorages.
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

  def testCompareStorages(self):
    """Tests the CompareStorages function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    test_file1 = self._GetTestFilePath([u'psort_test.json.plaso'])
    test_file2 = self._GetTestFilePath([u'pinfo_test.json.plaso'])

    options = test_lib.TestOptions()
    options.compare_storage_file = test_file1
    options.storage_file = test_file1

    test_tool.ParseOptions(options)

    self.assertTrue(test_tool.CompareStorages())

    output = output_writer.ReadOutput()
    self.assertEqual(output, b'Storage files are identical.\n')

    options = test_lib.TestOptions()
    options.compare_storage_file = test_file1
    options.storage_file = test_file2

    test_tool.ParseOptions(options)

    self.assertFalse(test_tool.CompareStorages())

    output = output_writer.ReadOutput()
    self.assertEqual(output, b'Storage files are different.\n')

  def testParseArguments(self):
    """Tests the ParseArguments function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    result = test_tool.ParseArguments()
    self.assertFalse(result)

    # TODO: check output.
    # TODO: improve test coverage.

  def testParseOptions(self):
    """Tests the ParseOptions function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    options = test_lib.TestOptions()
    options.storage_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])

    test_tool.ParseOptions(options)

    options = test_lib.TestOptions()

    with self.assertRaises(errors.BadConfigOption):
      test_tool.ParseOptions(options)

    # TODO: improve test coverage.

  def testPrintStorageInformationAsText(self):
    """Tests the _PrintStorageInformationAsText function."""
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)

    test_filename = u'pinfo_test.json.plaso'
    format_version = u'20170121'
    plaso_version = u'20170714'
    session_identifier = u'81ca8bf6-285d-4bac-bb7c-d339f07d7728'
    session_start_time = u'2017-07-15T07:55:31.382324+00:00'
    session_completion_time = u'2017-07-15T07:55:32.171567+00:00'

    command_line_arguments = (
        u'./tools/log2timeline.py --partition=all --quiet '
        u'pinfo_test.json.plaso test_data/tsk_volume_system.raw')

    enabled_parser_names = u', '.join([
        u'android_app_usage', u'asl_log', u'bash', u'bencode',
        u'bencode/bencode_transmission', u'bencode/bencode_utorrent',
        u'binary_cookies', u'bsm_log', u'chrome_cache', u'chrome_preferences',
        u'cups_ipp', u'custom_destinations', u'dockerjson', u'dpkg', u'esedb',
        u'esedb/esedb_file_history', u'esedb/msie_webcache', u'filestat',
        u'firefox_cache', u'firefox_cache2', u'hachoir', u'java_idx', u'lnk',
        u'mac_appfirewall_log', u'mac_keychain', u'mac_securityd', u'mactime',
        u'macwifi', u'mcafee_protection', u'mft', u'msiecf', u'olecf',
        u'olecf/olecf_automatic_destinations', u'olecf/olecf_default',
        u'olecf/olecf_document_summary', u'olecf/olecf_summary', u'openxml',
        u'opera_global', u'opera_typed_history', u'pe', u'plist',
        u'plist/airport', u'plist/apple_id', u'plist/ipod_device',
        u'plist/macosx_bluetooth', u'plist/macosx_install_history',
        u'plist/macuser', u'plist/maxos_software_update',
        u'plist/plist_default', u'plist/safari_history', u'plist/spotlight',
        u'plist/spotlight_volume', u'plist/time_machine', u'pls_recall',
        u'popularity_contest', u'prefetch', u'recycle_bin',
        u'recycle_bin_info2', u'rplog', u'sccm', u'selinux', u'skydrive_log',
        u'skydrive_log_old', u'sqlite', u'sqlite/android_calls',
        u'sqlite/android_sms', u'sqlite/android_webview',
        u'sqlite/android_webviewcache', u'sqlite/appusage',
        u'sqlite/chrome_cookies', u'sqlite/chrome_extension_activity',
        u'sqlite/chrome_history', u'sqlite/firefox_cookies',
        u'sqlite/firefox_downloads', u'sqlite/firefox_history',
        u'sqlite/google_drive', u'sqlite/imessage',
        u'sqlite/kik_messenger', u'sqlite/ls_quarantine',
        u'sqlite/mac_document_versions', u'sqlite/mackeeper_cache',
        u'sqlite/skype', u'sqlite/twitter_ios', u'sqlite/zeitgeist',
        u'symantec_scanlog', u'syslog', u'syslog/cron', u'syslog/ssh',
        u'systemd_journal', u'usnjrnl', u'utmp', u'utmpx', u'winevt',
        u'winevtx', u'winfirewall', u'winiis', u'winjob', u'winreg',
        u'winreg/appcompatcache', u'winreg/bagmru', u'winreg/ccleaner',
        u'winreg/explorer_mountpoints2', u'winreg/explorer_programscache',
        u'winreg/microsoft_office_mru', u'winreg/microsoft_outlook_mru',
        u'winreg/mrulist_shell_item_list', u'winreg/mrulist_string',
        u'winreg/mrulistex_shell_item_list', u'winreg/mrulistex_string',
        u'winreg/mrulistex_string_and_shell_item',
        u'winreg/mrulistex_string_and_shell_item_list', u'winreg/msie_zone',
        u'winreg/mstsc_rdp', u'winreg/mstsc_rdp_mru', u'winreg/network_drives',
        u'winreg/userassist', u'winreg/windows_boot_execute',
        u'winreg/windows_boot_verify', u'winreg/windows_run',
        u'winreg/windows_sam_users', u'winreg/windows_services',
        u'winreg/windows_shutdown', u'winreg/windows_task_cache',
        u'winreg/windows_timezone', u'winreg/windows_typed_urls',
        u'winreg/windows_usb_devices', u'winreg/windows_usbstor_devices',
        u'winreg/windows_version', u'winreg/winlogon', u'winreg/winrar_mru',
        u'winreg/winreg_default', u'xchatlog', u'xchatscrollback',
        u'zsh_extended_history'])

    table_view = cli_views.ViewsFactory.GetTableView(
        cli_views.ViewsFactory.FORMAT_TYPE_CLI,
        title=u'Plaso Storage Information')
    table_view.AddRow([u'Filename', test_filename])
    table_view.AddRow([u'Format version', format_version])
    table_view.AddRow([u'Serialization format', u'json'])
    table_view.Write(output_writer)

    table_view = cli_views.ViewsFactory.GetTableView(
        cli_views.ViewsFactory.FORMAT_TYPE_CLI, title=u'Sessions')
    table_view.AddRow([session_identifier, session_start_time])
    table_view.Write(output_writer)

    title = u'Session: {0!s}'.format(session_identifier)
    table_view = cli_views.ViewsFactory.GetTableView(
        cli_views.ViewsFactory.FORMAT_TYPE_CLI, title=title)
    table_view.AddRow([u'Start time', session_start_time])
    table_view.AddRow([u'Completion time', session_completion_time])
    table_view.AddRow([u'Product name', u'plaso'])
    table_view.AddRow([u'Product version', plaso_version])
    table_view.AddRow([u'Command line arguments', command_line_arguments])
    table_view.AddRow([u'Parser filter expression', u'N/A'])
    table_view.AddRow([u'Enabled parser and plugins', enabled_parser_names])
    table_view.AddRow([u'Preferred encoding', u'UTF-8'])
    table_view.AddRow([u'Debug mode', u'False'])
    table_view.AddRow([u'Filter file', u'N/A'])
    table_view.Write(output_writer)

    table_view = cli_views.ViewsFactory.GetTableView(
        cli_views.ViewsFactory.FORMAT_TYPE_CLI,
        column_names=[u'Parser (plugin) name', u'Number of events'],
        title=u'Events generated per parser')
    table_view.AddRow([u'filestat', u'3'])
    table_view.AddRow([u'Total', u'3'])
    table_view.Write(output_writer)

    expected_output = output_writer.ReadOutput()

    expected_output = (
        b'{0:s}'
        b'No errors stored.\n'
        b'\n'
        b'No analysis reports stored.\n'
        b'\n').format(expected_output)

    test_file = self._GetTestFilePath([test_filename])

    options = test_lib.TestOptions()
    options.storage_file = test_file
    options.output_format = u'text'

    test_tool.ParseOptions(options)

    test_tool.PrintStorageInformation()

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output.split(b'\n'))

  def testPrintStorageInformationAsJSON(self):
    """Tests the _PrintStorageInformationAsJSON function."""
    test_filename = u'pinfo_test.json.plaso'
    session_identifier = u'81ca8bf6285d4bacbb7cd339f07d7728'
    session_start_time = timelib.Timestamp.CopyFromString(
        u'2017-07-15 07:55:31.382324')
    output_writer = test_lib.TestOutputWriter(encoding=u'utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_file = self._GetTestFilePath([test_filename])

    options = test_lib.TestOptions()
    options.storage_file = test_file
    options.output_format = u'json'

    test_tool.ParseOptions(options)

    test_tool.PrintStorageInformation()
    output = output_writer.ReadOutput()
    json_output = json.loads(output)

    first_session_identifier = u'session_{0:s}'.format(session_identifier)
    first_session = json_output.get(first_session_identifier, None)
    self.assertIsNotNone(first_session)

    self.assertEqual(first_session[u'identifier'], session_identifier)
    self.assertEqual(first_session[u'start_time'], session_start_time)

    parsers_counter = first_session[u'parsers_counter']
    self.assertEqual(parsers_counter[u'total'], 3)
    self.assertEqual(parsers_counter[u'filestat'], 3)


if __name__ == '__main__':
  unittest.main()
