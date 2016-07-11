# -*- coding: utf-8 -*-
"""The parser preset categories."""

CATEGORIES = {
    u'win_gen': [
        u'bencode', u'esedb', u'filestat', u'sqlite/google_drive', u'java_idx',
        u'lnk', u'mcafee_protection', u'olecf', u'openxml', u'pe', u'prefetch',
        u'sccm', u'skydrive_log', u'skydrive_log_old', u'sqlite/skype',
        u'symantec_scanlog', u'webhist', u'winfirewall', u'winjob', u'winreg'],
    u'winxp': [
        u'recycle_bin_info2', u'win_gen', u'winevt'],
    u'winxp_slow': [
        u'hachoir', u'winxp'],
    u'win7': [
        u'recycle_bin', u'custom_destinations', u'esedb/esedb_file_history',
        u'olecf/olecf_automatic_destinations', u'win_gen', u'winevtx'],
    u'win7_slow': [
        u'hachoir', u'win7'],
    u'webhist': [
        u'binary_cookies', u'chrome_cache', u'sqlite/chrome_cookies',
        u'sqlite/chrome_extension_activity', u'sqlite/chrome_history',
        u'chrome_preferences', u'firefox_cache', u'sqlite/firefox_cookies',
        u'sqlite/firefox_downloads', u'sqlite/firefox_history', u'java_idx',
        u'esedb/msie_webcache', u'msiecf', u'opera_global',
        u'opera_typed_history', u'plist/safari_history'],
    u'linux': [
        u'bencode', u'filestat', u'sqlite/google_drive', u'java_idx', u'olecf',
        u'openxml', u'pls_recall', u'popularity_contest', u'selinux',
        u'sqlite/skype', u'syslog', u'utmp', u'webhist', u'xchatlog',
        u'xchatscrollback', u'sqlite/zeitgeist'],
    u'macosx': [
        u'sqlite/appusage', u'asl_log', u'bencode', u'bsm_log', u'cups_ipp',
        u'filestat', u'sqlite/google_drive', u'java_idx',
        u'sqlite/ls_quarantine', u'mac_appfirewall_log',
        u'sqlite/mac_document_versions', u'mac_keychain', u'mac_securityd',
        u'sqlite/mackeeper_cache', u'macwifi', u'olecf', u'openxml', u'plist',
        u'sqlite/skype', u'utmpx', u'webhist'],
    # TODO: Once syslog parser has been rewritten to be faster than the current
    # one it's moved out of the default parsers for Mac OS X and into the "slow"
    # mode.
    u'macosx_slow': [u'macosx', u'syslog'],
    u'android': [
        u'android_app_usage', u'filestat', u'chrome_cache',
        u'sqlite/android_calls', u'sqlite/android_sms',
        u'sqlite/android_webview', u'sqlite/android_webviewcache',
        u'sqlite/chrome_cookies', u'sqlite/chrome_history', u'sqlite/skype',]}
