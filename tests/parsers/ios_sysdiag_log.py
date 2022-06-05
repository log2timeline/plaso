#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the iOS Mobile Installation log parser."""

import unittest

from plaso.parsers import ios_sysdiag_log

from tests.parsers import test_lib


class IOSSysdiagLogParserTest(test_lib.ParserTestCase):
  """Tests for the iOS Mobile Installation log parser"""

  def testParseLog(self):
    """Tests the Parse function"""
    parser = ios_sysdiag_log.IOSSysdiagLogParser()
    storage_writer = self._ParseFile(['ios_sysdiag.log'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 28)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'body': (
            'Ignoring plugin at /System/Library/PrivateFrameworks/'
            'AccessibilityUtilities.framework/PlugIns/com.apple.accessibility.'
            'Accessibility.HearingAidsTapToRadar.appex due to validation '
            'issue(s). See previous log messages for details.'),
        'originating_call': (
            '+[MILaunchServicesDatabaseGatherer '
            'enumeratePluginKitPluginsInBundle:updatingPluginParentID:'
            'ensurePluginsAreExecutable:installProfiles:error:enumerator:]'),
        'process_identifier': '176',
        'severity': 'err',
        'timestamp': '2021-08-11 05:51:02.000000'}

    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'body': (
            '47: Failed to load Info.plist from bundle at path /System/'
            'Library/PrivateFrameworks/'
            'CoreDuetContext.framework; Extra info about "/System/Library/'
            'PrivateFrameworks/'
            'CoreDuetContext.framework/Info.plist": dev=805306369 '
            'ino=1152921500312080876 mode=0100644 nlink=1 '
            'uid=0 gid=0 rdev=0 size=800 atime=1577865600.000000 '
            'mtime=1577865600.000000 '
            'ctime=1577865600.000000 birthtime=1577865600.000000 '
            'blksize=4096 blocks=0 flags=0x20 '
            'firstBytes={length = 4, bytes = 0x62706c69} ACL=<not found> '
            'extendedAttributes={\n    '
            '"com.apple.decmpfs" = {length = 817, bytes = 0x66706d63 '
            '09000000 20030000 00000000 ... 00000000 '
            '000002a6 };\n} keyCount=22 keySample={ CFBundleName DTXcode '
            'DTSDKName DTSDKBuild '
            'CFBundleDevelopmentRegion }'),
        'originating_call': '-[MIBundle _validateWithError:]',
        'process_identifier': '176',
        'severity': 'err',
        'timestamp': '2021-08-11 05:51:03.000000'}

    self.CheckEventValues(storage_writer, events[14], expected_event_values)

    expected_event_values = {
        'body': 'containermanagerd first boot cleanup complete',
        'originating_call': '_containermanagerd_init_block_invoke',
        'process_identifier': '66',
        'severity': 'notice',
        'timestamp': '2021-01-17 11:20:29.000000'}

    self.CheckEventValues(storage_writer, events[20], expected_event_values)


if __name__ == '__main__':
  unittest.main()
