# -*- coding: utf-8 -*-
"""Helper file for filtering out parsers."""

categories = {
    'win_gen': [
        'bencode', 'esedb', 'filestat', 'google_drive', 'java_idx', 'lnk',
        'mcafee_protection', 'olecf', 'openxml', 'prefetch',
        'skydrive_log_error', 'skydrive_log', 'skype',
        'symantec_scanlog', 'webhist', 'winfirewall', 'winjob',
        'winreg'],
    'winxp': [
        'recycle_bin_info2', 'win_gen', 'winevt'],
    'winxp_slow': [
        'hachoir', 'winxp'],
    'win7': [
        'recycle_bin', 'custom_destinations', 'esedb_file_history',
        'olecf_automatic_destinations', 'win_gen', 'winevtx'],
    'win7_slow': [
        'hachoir', 'win7'],
    'webhist': [
        'binary_cookies', 'chrome_cache', 'chrome_cookies',
        'chrome_extension_activity', 'chrome_history', 'chrome_preferences',
        'firefox_cache', 'firefox_cookies', 'firefox_downloads',
        'firefox_history', 'java_idx', 'msie_webcache', 'msiecf',
        'opera_global', 'opera_typed_history', 'safari_history'],
    'linux': [
        'bencode', 'filestat', 'google_drive', 'java_idx', 'olecf', 'openxml',
        'pls_recall', 'popularity_contest', 'selinux', 'skype', 'syslog',
        'utmp', 'webhist', 'xchatlog', 'xchatscrollback', 'zeitgeist'],
    'macosx': [
        'appusage', 'asl_log', 'bencode', 'bsm_log', 'cups_ipp', 'filestat',
        'google_drive', 'java_idx', 'ls_quarantine', 'mac_appfirewall_log',
        'mac_document_versions', 'mac_keychain', 'mac_securityd',
        'mackeeper_cache', 'macwifi', 'olecf', 'openxml', 'plist', 'skype',
        'utmpx', 'webhist'],
    # TODO: Once syslog parser has been rewritten to be faster than the current
    # one it's moved out of the default parsers for Mac OS X and into the "slow"
    # mode.
    'macosx_slow': ['macosx', 'syslog'],
    'android': [
        'android_app_usage', 'android_calls', 'android_sms'],
}


def GetParsersFromCategory(category):
  """Return a list of parsers from a parser category."""
  return_list = []
  if category not in categories:
    return return_list

  for item in categories.get(category):
    if item in categories:
      return_list.extend(GetParsersFromCategory(item))
    else:
      return_list.append(item)

  return return_list
