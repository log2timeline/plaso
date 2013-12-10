#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Helper file for filtering out parsers."""

categories = {
    'winxp': [
        'BencodeParser', 'ChromeHistoryParser', 'FirefoxHistoryParser',
        'GoogleDriveParser', 'JavaIDXParser', 'MsiecfParser', 'OleCfParser',
        'OpenXMLParser', 'OperaGlobalHistoryParser', 'OperaTypedHistoryEvent',
        'PfileStatParser', 'SkyDriveLogParser',
        'SkypeParser', 'Symantec', 'WinEvtParser', 'WinInfo2Parser',
        'WinFirewallParser', 'WinJobParser', 'WinLnkParser',
        'WinPrefetchParser', 'WinRegistryParser'],
    'winxp_slow': [
        'BencodeParser', 'ChromeHistoryParser', 'FirefoxHistoryParser',
        'GoogleDriveParser', 'Hachoir', 'JavaIDXParser', 'MsiecfParser',
        'OleCfParser', 'OperaGlobalHistoryParser', 'OperaTypedHistoryEvent',
        'OpenXMLParser', 'PfileStatParser', 'SkyDriveLogParser', 'SkypeParser',
        'Symantec', 'WinEvtParser', 'WinInfo2Parser', 'WinFirewallParser',
        'WinJobParser', 'WinLnkParser', 'WinPrefetchParser',
        'WinRegistryParser'],
    'win7': [
        'BencodeParser', 'ChromeHistoryParser', 'FirefoxHistoryParser',
        'GoogleDriveParser', 'JavaIDXParser', 'MsiecfParser', 'OleCfParser',
        'OpenXMLParser', 'OperaGlobalHistoryParser', 'OperaTypedHistoryEvent',
        'PfileStatParser', 'SkyDriveLogParser', 'SkypeParser', 'Symantec',
        'WinEvtxParser', 'WinFirewallParser', 'WinJobParser', 'WinLnkParser',
        'WinPrefetchParser', 'WinRecycleParser', 'WinRegistryParser'],
    'win7_slow': [
        'BencodeParser', 'ChromeHistoryParser', 'FirefoxHistoryParser',
        'GoogleDriveParser', 'Hachoir', 'JavaIDXParser', 'MsiecfParser',
        'OleCfParser', 'OperaGlobalHistoryParser', 'OperaTypedHistoryEvent',
        'OpenXMLParser', 'PfileStatParser', 'SkyDriveLogParser', 'SkypeParser',
        'Symantec', 'WinEvtxParser', 'WinFirewallParser', 'WinJobParser',
        'WinLnkParser', 'WinPrefetchParser', 'WinRecycleParser',
        'WinRegistryParser'],
    'webhist': [
        'ChromeHistoryParser', 'FirefoxHistoryParser', 'JavaIDXParser',
        'OperaGlobalHistoryParser', 'OperaTypedHistoryEvent', 'MsiecfParser'],
    'linux': [
        'BencodeParser', 'ChromeHistoryParser', 'FirefoxHistoryParser',
        'GoogleDriveParser', 'JavaIDXParser', 'OleCfParser', 'OpenXMLParser',
        'OperaGlobalHistoryParser', 'OperaTypedHistoryEvent',
        'PfileStatParser', 'SELinux', 'SkypeParser', 'SyslogParser',
        'XChatScrollbackParser', 'ZeitgeistParser'],
    'macosx': [
        'ApplicationUsageParser', 'BencodeParser', 'ChromeHistoryParser',
        'FirefoxHistoryParser', 'GoogleDriveParser', 'JavaIDXParser',
        'LsQuarantineParser', 'MacKeeperCacheParser', 'OleCfParser',
        'OpenXMLParser', 'OperaGlobalHistoryParser', 'OperaTypedHistoryEvent',
        'PfileStatParser', 'PlistParser', 'SkypeParser',
        'SyslogParser', 'UtmpxParser'],
    'android': [
        'AndroidSmsParser', 'AndroidCallParser'],
}
