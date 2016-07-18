#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the pinfo CLI tool."""

import unittest

from tests.cli import test_lib as cli_test_lib

from tools import pinfo


class PinfoToolTest(cli_test_lib.CLIToolTestCase):
  """Tests for the pinfo CLI tool."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._output_writer = cli_test_lib.TestOutputWriter(encoding=u'utf-8')
    self._test_tool = pinfo.PinfoTool(output_writer=self._output_writer)

  def testCompareStorages(self):
    """Tests the CompareStorages function."""
    test_file1 = self._GetTestFilePath([u'psort_test.json.plaso'])
    test_file2 = self._GetTestFilePath([u'pinfo_test.json.plaso'])

    options = cli_test_lib.TestOptions()
    options.compare_storage_file = test_file1
    options.storage_file = test_file1

    self._test_tool.ParseOptions(options)

    self.assertTrue(self._test_tool.CompareStorages())

    output = self._output_writer.ReadOutput()
    self.assertEqual(output, b'Storages are identical.\n')

    options = cli_test_lib.TestOptions()
    options.compare_storage_file = test_file1
    options.storage_file = test_file2

    self._test_tool.ParseOptions(options)

    self.assertFalse(self._test_tool.CompareStorages())

    output = self._output_writer.ReadOutput()
    self.assertEqual(output, b'Storages are different.\n')

  def testPrintStorageInformation(self):
    """Tests the PrintStorageInformation function."""
    test_file = self._GetTestFilePath([u'pinfo_test.json.plaso'])

    options = cli_test_lib.TestOptions()
    options.storage_file = test_file

    self._test_tool.ParseOptions(options)

    self._test_tool.PrintStorageInformation()

    expected_output = (
        b'\n'
        b'************************** Plaso Storage Information ****************'
        b'***********\n'
        b'            Filename : pinfo_test.json.plaso\n'
        b'      Format version : 20160715\n'
        b'Serialization format : json\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'\n'
        b'*********************************** Sessions ************************'
        b'***********\n'
        b'65e59b3a-afa5-4aee-8d55-735cbd7b8686 : '
        b'2016-07-18T05:37:58.992319+00:00\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'\n'
        b'**************** Session: 65e59b3a-afa5-4aee-8d55-735cbd7b8686 ******'
        b'***********\n'
        b'                Start time : 2016-07-18T05:37:58.992319+00:00\n'
        b'           Completion time : 2016-07-18T05:37:59.761184+00:00\n'
        b'              Product name : plaso\n'
        b'           Product version : 1.4.1_20160717\n'
        b'    Command line arguments : ./tools/log2timeline.py --partition=all '
        b'--quiet\n'
        b'                             pinfo_test.json.plaso\n'
        b'                             test_data/tsk_volume_system.raw\n'
        b'  Parser filter expression : N/A\n'
        b'Enabled parser and plugins : android_app_usage, asl_log, bencode,\n'
        b'                             bencode/bencode_transmission,\n'
        b'                             bencode/bencode_utorrent, '
        b'binary_cookies, bsm_log,\n'
        b'                             chrome_cache, chrome_preferences, '
        b'cups_ipp,\n'
        b'                             custom_destinations, dockerjson, '
        b'esedb,\n'
        b'                             esedb/esedb_file_history, '
        b'esedb/msie_webcache,\n'
        b'                             filestat, firefox_cache, firefox_cache2, '
        b'hachoir,\n'
        b'                             java_idx, lnk, mac_appfirewall_log, '
        b'mac_keychain,\n'
        b'                             mac_securityd, mactime, macwifi,\n'
        b'                             mcafee_protection, mft, msiecf, olecf,\n'
        b'                             olecf/olecf_automatic_destinations,\n'
        b'                             olecf/olecf_default, '
        b'olecf/olecf_document_summary,\n'
        b'                             olecf/olecf_summary, openxml, '
        b'opera_global,\n'
        b'                             opera_typed_history, pe, plist, '
        b'plist/airport,\n'
        b'                             plist/apple_id, plist/ipod_device,\n'
        b'                             plist/macosx_bluetooth,\n'
        b'                             plist/macosx_install_history, '
        b'plist/macuser,\n'
        b'                             plist/maxos_software_update, '
        b'plist/plist_default,\n'
        b'                             plist/safari_history, plist/spotlight,\n'
        b'                             plist/spotlight_volume, '
        b'plist/time_machine,\n'
        b'                             pls_recall, popularity_contest, '
        b'prefetch,\n'
        b'                             recycle_bin, recycle_bin_info2, rplog, '
        b'sccm,\n'
        b'                             selinux, skydrive_log, skydrive_log_old, '
        b'sqlite,\n'
        b'                             sqlite/android_calls, '
        b'sqlite/android_sms,\n'
        b'                             sqlite/appusage, '
        b'sqlite/chrome_cookies,\n'
        b'                             sqlite/chrome_extension_activity,\n'
        b'                             sqlite/chrome_history, '
        b'sqlite/firefox_cookies,\n'
        b'                             sqlite/firefox_downloads, '
        b'sqlite/firefox_history,\n'
        b'                             sqlite/google_drive, sqlite/imessage,\n'
        b'                             sqlite/kik_messenger, '
        b'sqlite/ls_quarantine,\n'
        b'                             sqlite/mac_document_versions,\n'
        b'                             sqlite/mackeeper_cache, sqlite/skype,\n'
        b'                             sqlite/twitter_ios, sqlite/zeitgeist,\n'
        b'                             symantec_scanlog, syslog, syslog/cron, '
        b'syslog/ssh,\n'
        b'                             usnjrnl, utmp, utmpx, winevt, winevtx,\n'
        b'                             winfirewall, winiis, winjob, winreg,\n'
        b'                             winreg/appcompatcache, winreg/bagmru,\n'
        b'                             winreg/ccleaner, '
        b'winreg/explorer_mountpoints2,\n'
        b'                             winreg/explorer_programscache,\n'
        b'                             winreg/microsoft_office_mru,\n'
        b'                             winreg/microsoft_outlook_mru,\n'
        b'                             winreg/mrulist_shell_item_list,\n'
        b'                             winreg/mrulist_string,\n'
        b'                             winreg/mrulistex_shell_item_list,\n'
        b'                             winreg/mrulistex_string,\n'
        b'                             '
        b'winreg/mrulistex_string_and_shell_item,\n'
        b'                             '
        b'winreg/mrulistex_string_and_shell_item_list,\n'
        b'                             winreg/msie_zone, winreg/mstsc_rdp,\n'
        b'                             winreg/mstsc_rdp_mru, '
        b'winreg/network_drives,\n'
        b'                             winreg/userassist, '
        b'winreg/windows_boot_execute,\n'
        b'                             winreg/windows_boot_verify, '
        b'winreg/windows_run,\n'
        b'                             winreg/windows_sam_users, '
        b'winreg/windows_services,\n'
        b'                             winreg/windows_shutdown,\n'
        b'                             winreg/windows_task_cache,\n'
        b'                             winreg/windows_timezone,\n'
        b'                             winreg/windows_typed_urls,\n'
        b'                             winreg/windows_usb_devices,\n'
        b'                             winreg/windows_usbstor_devices,\n'
        b'                             winreg/windows_version, '
        b'winreg/winlogon,\n'
        b'                             winreg/winrar_mru, '
        b'winreg/winreg_default,\n'
        b'                             xchatlog, xchatscrollback\n'
        b'        Preferred encoding : UTF-8\n'
        b'                Debug mode : False\n'
        b'               Filter file : N/A\n'
        b'         Filter expression : N/A\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'\n'
        b'************************* Events generated per parser ***************'
        b'***********\n'
        b'Parser (plugin) name : Number of events\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'            filestat : 3\n'
        b'               Total : 3\n'
        b'---------------------------------------------------------------------'
        b'-----------\n'
        b'No errors stored.\n'
        b'\n'
        b'No analysis reports stored.\n'
        b'\n')

    output = self._output_writer.ReadOutput()

    # Compare the output as list of lines which makes it easier to spot
    # differences.
    self.assertEqual(output.split(b'\n'), expected_output.split(b'\n'))


if __name__ == '__main__':
  unittest.main()
