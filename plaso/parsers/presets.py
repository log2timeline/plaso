# -*- coding: utf-8 -*-
"""The parser and parser plugin presets."""

from __future__ import unicode_literals

class ParserPresetDefinition(object):
  """Parser and parser plugin preset definition.

  Attributes:
    name (str): name of the preset.
    parsers (str): names of parser and parser plugins.
  """

  def __init__(self):
    """Initializes a parser and parser plugin preset definition."""
    super(ParserPresetDefinition, self).__init__()
    self.name = None
    self.parsers = None


class ParserPresets(object):
  """Parser and parser plugin presets."""

  CATEGORIES = {
      'win_gen': [
          'bencode', 'esedb', 'filestat', 'sqlite/google_drive',
          'gdrive_synclog', 'java_idx', 'lnk', 'mcafee_protection',
          'olecf', 'czip/oxml', 'pe', 'prefetch', 'sccm', 'skydrive_log',
          'skydrive_log_old', 'sqlite/skype', 'symantec_scanlog', 'usnjrnl',
          'webhist', 'winfirewall', 'winjob', 'winreg'],
      'winxp': ['recycle_bin_info2', 'rplog', 'win_gen', 'winevt'],
      'winxp_slow': ['mft', 'winxp'],
      'win7': [
          'recycle_bin', 'custom_destinations', 'esedb/file_history',
          'olecf/olecf_automatic_destinations', 'win_gen', 'winevtx',
          'amcache'],
      'win7_slow': ['mft', 'win7'],
      'webhist': [
          'binary_cookies', 'chrome_cache', 'sqlite/chrome_autofill',
          'sqlite/chrome_cookies', 'sqlite/chrome_extension_activity',
          'sqlite/chrome_8_history', 'sqlite/chrome_27_history',
          'chrome_preferences', 'firefox_cache', 'sqlite/firefox_cookies',
          'sqlite/firefox_downloads', 'sqlite/firefox_history', 'java_idx',
          'esedb/msie_webcache', 'msiecf', 'opera_global',
          'opera_typed_history', 'plist/safari_history'],
      'linux': [
          'bash_history', 'bencode', 'dockerjson', 'dpkg', 'filestat',
          'sqlite/google_drive', 'gdrive_synclog', 'java_idx', 'olecf',
          'czip/oxml', 'pls_recall', 'popularity_contest', 'selinux',
          'sqlite/skype', 'syslog', 'systemd_journal', 'utmp', 'webhist',
          'xchatlog', 'xchatscrollback', 'sqlite/zeitgeist',
          'zsh_extended_history'],
      'macos': [
          'sqlite/appusage', 'asl_log', 'bash_history', 'bencode', 'bsm_log',
          'cups_ipp', 'filestat', 'fseventsd', 'sqlite/google_drive',
          'gdrive_synclog', 'sqlite/imessage', 'java_idx',
          'sqlite/ls_quarantine', 'mac_appfirewall_log',
          'sqlite/mac_document_versions', 'mac_keychain', 'mac_securityd',
          'sqlite/mackeeper_cache', 'macwifi', 'olecf', 'czip/oxml', 'plist',
          'sqlite/skype', 'syslog', 'utmpx', 'webhist', 'zsh_extended_history'],
      'android': [
          'android_app_usage', 'filestat', 'chrome_cache',
          'sqlite/android_calls', 'sqlite/android_sms',
          'sqlite/android_webview', 'sqlite/android_webviewcache',
          'sqlite/chrome_cookies', 'sqlite/chrome_8_history',
          'sqlite/chrome_27_history', 'sqlite/skype']}

  def GetNames(self):
    """Retrieves the preset names.

    Returns:
      list[str]: preset names in alphabetical order.
    """
    return sorted(self.CATEGORIES.keys())

  def GetPresetByName(self, name):
    """Retrieves a specific preset definition by name.

    Args:
      name (str): name of the preset.

    Returns:
      PresetDefinition: preset definition or None if not available.
    """
    preset_definition = None

    parsers = self.CATEGORIES.get(name, None)
    if parsers is not None:
      preset_definition = ParserPresetDefinition()
      preset_definition.name = name
      preset_definition.parsers = parsers

    return preset_definition

  def GetPresets(self):
    """Retrieves the preset definitions.

    Yields:
      PresetDefinition: preset definition in alphabetical order by name.
    """
    for name, parsers in sorted(self.CATEGORIES.items()):
      preset_definition = ParserPresetDefinition()
      preset_definition.name = name
      preset_definition.parsers = parsers
      yield preset_definition
