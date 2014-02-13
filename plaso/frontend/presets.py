#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
        'bencode', 'chrome_cookies', 'chrome_history', 'filestat',
        'firefox_downloads', 'firefox_history', 'google_drive', 'java_idx',
        'lnk', 'mcafee_protection', 'msiecf', 'olecf', 'openxml',
        'opera_global', 'opera_typed_history', 'prefetch', 'recycle_bin_info2',
        'safari_history', 'skydrive_log_error', 'skydrive_log', 'skype',
        'symantec_scanlog', 'winevt', 'winfirewall', 'winjob', 'winreg'],
    'winxp_slow': [
        'bencode', 'chrome_cookies', 'chrome_history', 'filestat',
        'firefox_downloads', 'firefox_history', 'google_drive', 'hachoir',
        'java_idx', 'lnk', 'mcafee_protection', 'msiecf', 'olecf', 'openxml',
        'opera_global', 'opera_typed_history', 'prefetch', 'recycle_bin_info2',
        'safari_history', 'skydrive_log_error', 'skydrive_log', 'skype',
        'symantec_scanlog', 'winevt', 'winfirewall', 'winjob', 'winreg'],
    'win7': [
        'bencode', 'chrome_cookies', 'chrome_history', 'filestat',
        'firefox_downloads', 'firefox_history', 'google_drive', 'java_idx',
        'lnk', 'mcafee_protection', 'msiecf', 'olecf', 'openxml',
        'opera_global', 'opera_typed_history', 'prefetch', 'recycle_bin',
        'safari_history', 'skydrive_log', 'skydrive_log_error', 'skype',
        'symantec_scanlog', 'winevtx', 'winfirewall', 'winjob', 'winreg'],
    'win7_slow': [
        'bencode', 'chrome_cookies', 'chrome_history', 'filestat',
        'firefox_downloads', 'firefox_history', 'google_drive', 'java_idx',
        'lnk', 'mcafee_protection', 'msiecf', 'olecf', 'openxml',
        'opera_global', 'opera_typed_history', 'prefetch', 'recycle_bin',
        'safari_history', 'skydrive_log', 'skydrive_log_error', 'skype',
        'symantec_scanlog', 'winevtx', 'winfirewall', 'winjob', 'winreg'],
    'webhist': [
        'chrome_cookies', 'chrome_history', 'firefox_downloads',
        'firefox_history', 'java_idx', 'opera_global', 'opera_typed_history',
        'msiecf', 'safari_history'],
    'linux': [
        'bencode', 'chrome_cookies', 'chrome_history', 'filestat',
        'firefox_downloads', 'firefox_history', 'google_drive', 'java_idx',
        'olecf', 'openxml', 'opera_global', 'opera_typed_history', 'selinux',
        'skype', 'syslog', 'xchatlog', 'xchatscrollback', 'zeitgeist'],
    'macosx': [
        'appusage', 'asl_log', 'bencode', 'bsm_log', 'chrome_cookies',
        'chrome_history', 'cups_ipp', 'filestat', 'firefox_downloads',
        'firefox_history', 'google_drive', 'java_idx', 'ls_quarantine',
        'mac_appfirewall_log', 'mac_document_versions', 'mac_keychain',
        'mac_securityd', 'mackeeper_cache', 'macwifi', 'olecf', 'openxml',
        'opera_global', 'opera_typed_history', 'plist', 'safari_history',
        'skype', 'syslog', 'utmpx'],
    'android': [
        'android_calls', 'android_sms'],
}
