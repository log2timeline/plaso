# -*- coding: utf-8 -*-
"""Helper file for filtering out parsers."""

categories = {
    u'win_gen': [
        u'bencode', u'esedb', u'filestat', u'google_drive', u'java_idx', u'lnk',
        u'mcafee_protection', u'olecf', u'openxml', u'pe', u'prefetch',
        u'skydrive_log_error', u'skydrive_log', u'skype',
        u'symantec_scanlog', u'webhist', u'winfirewall', u'winjob',
        u'winreg'],
    u'winxp': [
        u'recycle_bin_info2', u'win_gen', u'winevt'],
    u'winxp_slow': [
        u'hachoir', u'winxp'],
    u'win7': [
        u'recycle_bin', u'custom_destinations', u'esedb_file_history',
        u'olecf_automatic_destinations', u'win_gen', u'winevtx'],
    u'win7_slow': [
        u'hachoir', u'win7'],
    u'webhist': [
        u'binary_cookies', u'chrome_cache', u'chrome_cookies',
        u'chrome_extension_activity', u'chrome_history', u'chrome_preferences',
        u'firefox_cache', u'firefox_cookies', u'firefox_downloads',
        u'firefox_history', u'java_idx', u'msie_webcache', u'msiecf',
        u'opera_global', u'opera_typed_history', u'safari_history'],
    u'linux': [
        u'bencode', u'filestat', u'google_drive', u'java_idx', u'olecf',
        u'openxml', u'pls_recall', u'popularity_contest', u'selinux', u'skype',
        u'syslog', u'utmp', u'webhist', u'xchatlog', u'xchatscrollback',
        u'zeitgeist'],
    u'macosx': [
        u'appusage', u'asl_log', u'bencode', u'bsm_log', u'cups_ipp',
        u'filestat', u'google_drive', u'java_idx', u'ls_quarantine',
        u'mac_appfirewall_log', u'mac_document_versions', u'mac_keychain',
        u'mac_securityd', u'mackeeper_cache', u'macwifi', u'olecf', u'openxml',
        u'plist', u'skype', u'utmpx', u'webhist'],
    # TODO: Once syslog parser has been rewritten to be faster than the current
    # one it's moved out of the default parsers for Mac OS X and into the "slow"
    # mode.
    u'macosx_slow': [u'macosx', u'syslog'],
    u'android': [
        u'android_app_usage', u'android_calls', u'android_sms'],
  }


def GetParsersFromCategory(category):
  """Return a list of parsers from a parser category.

  Args:
    category: One of the parser categories.
  """
  return_list = []
  if category not in categories:
    return return_list

  for item in categories.get(category):
    if item in categories:
      return_list.extend(GetParsersFromCategory(item))
    else:
      return_list.append(item)

  return return_list
