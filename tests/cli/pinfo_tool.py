#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the pinfo CLI tool."""

from __future__ import unicode_literals

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
  # TODO: add test for _CompareStores.
  # TODO: add test for _PrintAnalysisReportCounter.
  # TODO: add test for _PrintAnalysisReportsDetails.
  # TODO: add test for _PrintWarningsDetails.
  # TODO: add test for _PrintEventLabelsCounter.
  # TODO: add test for _PrintParsersCounter.
  # TODO: add test for _PrintPreprocessingInformation.
  # TODO: add test for _PrintSessionsDetails.
  # TODO: add test for _PrintSessionsOverview.
  # TODO: add test for _PrintTasksInformation.
  # TODO: add test for _PrintStorageInformationAsText.

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

    expected_output = '\n'.join([
        '',
        ('************************* Events generated per parser ***************'
         '***********'),
        'Parser (plugin) name : Number of events',
        ('---------------------------------------------------------------------'
         '-----------'),
        '            filestat : 3 (6)',
        '               total : 3 (38)',
        ('---------------------------------------------------------------------'
         '-----------'),
        '',
        'Storage files are different.',
        ''])

    output = output_writer.ReadOutput()
    self.assertEqual(output, expected_output)

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

  def testPrintStorageInformationAsText(self):
    """Tests the _PrintStorageInformationAsText function."""
    test_filename = 'pinfo_test.plaso'
    format_version = '20190309'
    plaso_version = '20190429'
    session_identifier = '35242873-b939-4a86-a6ff-08c2fdadb946'
    session_start_time = '2019-05-05T11:52:23.388630Z'
    session_completion_time = '2019-05-05T11:52:26.078350Z'

    command_line_arguments = (
        './tools/log2timeline.py --partition=all --quiet '
        'pinfo_test.plaso test_data/tsk_volume_system.raw')

    enabled_parser_names = ', '.join([
        'amcache', 'android_app_usage', 'apache_access', 'asl_log', 'bash',
        'bencode', 'bencode/bencode_transmission', 'bencode/bencode_utorrent',
        'binary_cookies', 'bsm_log', 'chrome_cache', 'chrome_preferences',
        'cups_ipp', 'custom_destinations', 'czip', 'czip/oxml', 'dockerjson',
        'dpkg', 'esedb', 'esedb/file_history', 'esedb/msie_webcache',
        'esedb/srum', 'filestat', 'firefox_cache', 'firefox_cache2', 'fsevents',
        'gdrive_synclog', 'java_idx', 'lnk', 'mac_appfirewall_log',
        'mac_keychain', 'mac_securityd', 'mactime', 'macwifi',
        'mcafee_protection', 'mft', 'msiecf', 'olecf',
        'olecf/olecf_automatic_destinations', 'olecf/olecf_default',
        'olecf/olecf_document_summary', 'olecf/olecf_summary', 'opera_global',
        'opera_typed_history', 'pe', 'plist', 'plist/airport', 'plist/apple_id',
        'plist/ipod_device', 'plist/macosx_bluetooth',
        'plist/macosx_install_history', 'plist/macuser',
        'plist/maxos_software_update', 'plist/plist_default',
        'plist/safari_history', 'plist/spotlight', 'plist/spotlight_volume',
        'plist/time_machine', 'pls_recall', 'popularity_contest', 'prefetch',
        'recycle_bin', 'recycle_bin_info2', 'rplog', 'santa', 'sccm', 'selinux',
        'skydrive_log', 'skydrive_log_old', 'sophos_av', 'sqlite',
        'sqlite/android_calls', 'sqlite/android_sms', 'sqlite/android_webview',
        'sqlite/android_webviewcache', 'sqlite/appusage',
        'sqlite/chrome_27_history', 'sqlite/chrome_8_history',
        'sqlite/chrome_autofill', 'sqlite/chrome_cookies',
        'sqlite/chrome_extension_activity', 'sqlite/firefox_cookies',
        'sqlite/firefox_downloads', 'sqlite/firefox_history',
        'sqlite/google_drive', 'sqlite/hangouts_messages', 'sqlite/imessage',
        'sqlite/kik_messenger', 'sqlite/kodi', 'sqlite/ls_quarantine',
        'sqlite/mac_document_versions', 'sqlite/mac_notificationcenter',
        'sqlite/mackeeper_cache', 'sqlite/safari_history', 'sqlite/skype',
        'sqlite/tango_android_profile', 'sqlite/tango_android_tc',
        'sqlite/twitter_android', 'sqlite/twitter_ios',
        'sqlite/windows_timeline', 'sqlite/zeitgeist', 'symantec_scanlog',
        'syslog', 'syslog/cron', 'syslog/ssh', 'systemd_journal',
        'trendmicro_url', 'trendmicro_vd', 'usnjrnl', 'utmp', 'utmpx',
        'winevt', 'winevtx', 'winfirewall', 'winiis', 'winjob', 'winreg',
        'winreg/appcompatcache', 'winreg/bagmru', 'winreg/ccleaner',
        'winreg/explorer_mountpoints2', 'winreg/explorer_programscache',
        'winreg/microsoft_office_mru', 'winreg/microsoft_outlook_mru',
        'winreg/mrulist_shell_item_list', 'winreg/mrulist_string',
        'winreg/mrulistex_shell_item_list', 'winreg/mrulistex_string',
        'winreg/mrulistex_string_and_shell_item',
        'winreg/mrulistex_string_and_shell_item_list', 'winreg/msie_zone',
        'winreg/mstsc_rdp', 'winreg/mstsc_rdp_mru', 'winreg/network_drives',
        'winreg/networks', 'winreg/userassist', 'winreg/windows_boot_execute',
        'winreg/windows_boot_verify', 'winreg/windows_run',
        'winreg/windows_sam_users', 'winreg/windows_services',
        'winreg/windows_shutdown', 'winreg/windows_task_cache',
        'winreg/windows_timezone', 'winreg/windows_typed_urls',
        'winreg/windows_usb_devices', 'winreg/windows_usbstor_devices',
        'winreg/windows_version', 'winreg/winlogon', 'winreg/winrar_mru',
        'winreg/winreg_default', 'xchatlog', 'xchatscrollback',
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
    table_view.AddRow(['Number of event sources', '2'])
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
        'No warnings stored.\n'
        '\n'
        'No analysis reports stored.\n'
        '\n').format(expected_output)

    test_file_path = self._GetTestFilePath([test_filename])
    self._SkipIfPathNotExists(test_file_path)

    options = test_lib.TestOptions()
    options.storage_file = test_file_path
    options.output_format = 'text'

    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool.ParseOptions(options)

    test_tool.PrintStorageInformation()

    output = output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split('\n'), expected_output.split('\n'))

  def testPrintStorageInformationAsJSON(self):
    """Tests the _PrintStorageInformationAsJSON function."""
    test_filename = 'pinfo_test.plaso'
    session_identifier = '35242873b9394a86a6ff08c2fdadb946'
    session_start_time = timelib.Timestamp.CopyFromString(
        '2019-05-05 11:52:23.388630')

    test_file_path = self._GetTestFilePath([test_filename])
    self._SkipIfPathNotExists(test_file_path)

    options = test_lib.TestOptions()
    options.storage_file = test_file_path
    options.output_format = 'json'

    output_writer = test_lib.TestOutputWriter(encoding='utf-8')
    test_tool = pinfo_tool.PinfoTool(output_writer=output_writer)
    test_tool.ParseOptions(options)

    test_tool.PrintStorageInformation()
    output = output_writer.ReadOutput()
    json_output = json.loads(output)

    sessions = json_output.get('sessions')

    first_session_identifier = 'session_{0:s}'.format(session_identifier)
    first_session = sessions.get(first_session_identifier)
    self.assertIsNotNone(first_session)

    self.assertEqual(first_session['identifier'], session_identifier)
    self.assertEqual(first_session['start_time'], session_start_time)

    parsers_counter = first_session['parsers_counter']
    self.assertEqual(parsers_counter['total'], 3)
    self.assertEqual(parsers_counter['filestat'], 3)


if __name__ == '__main__':
  unittest.main()
