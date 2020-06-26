#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to extract information about the supported data formats."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import collections
import importlib
import inspect
import pkgutil
import sys

from urllib import parse as urllib_parse

import plaso

from plaso.parsers import interface as parsers_interface
from plaso.parsers import plugins as parsers_plugins


class DataFormatDescriptor(object):
  """Descriptor of a specific data format.

  Attributes:
    category (str): category of the data format, for example "File formats" or
        "OLE Compound File formats".
    name (str): name of the data format, for example "Chrome Extension
        activity database".
    url (str): URL to more information about the data format.
  """

  def __init__(self, category=None, name=None, url=None):
    """Initializes a data format descriptor.

    Args:
      category (Optional[str]): category of the data format, for example
        "File formats" or "OLE Compound File formats".
      name (Optional[str]): name of the data format, for example "Chrome
        Extension activity database".
      url (Optional[str]): URL to more information about the data format.
    """
    super(DataFormatDescriptor, self).__init__()
    # TODO: add data format name aliases.
    self.category = category
    self.name = name
    self.url = url


class DataFormatInformationExractor(object):
  """Data format information extractor."""

  _CATEGORIES_OUTPUT_ORDER = [
      'Storage media image file formats',
      'Volume system formats',
      'File system formats',
      'File formats',
      'Bencode file formats',
      'Browser cookie formats',
      'Compound ZIP file formats',
      'ESE database file formats',
      'OLE Compound File formats',
      'Property list (plist) formats',
      'SQLite database file formats',
      'Syslog file formats',
      'Windows Registry formats']

  # TODO: consider extending Plaso parsers and parser plugins with metadata that
  # contain this information.
  _DATA_FORMAT_CATEGORY_PER_PACKAGE_PATH = {
      'plaso/parsers': 'File formats',
      'plaso/parsers/bencode_plugins': 'Bencode file formats',
      'plaso/parsers/cookie_plugins': 'Browser cookie formats',
      'plaso/parsers/czip_plugins': 'Compound ZIP file formats',
      'plaso/parsers/esedb_plugins': 'ESE database file formats',
      'plaso/parsers/olecf_plugins': 'OLE Compound File formats',
      'plaso/parsers/plist_plugins': 'Property list (plist) formats',
      'plaso/parsers/sqlite_plugins': 'SQLite database file formats',
      'plaso/parsers/syslog_plugins': 'Syslog file formats',
      'plaso/parsers/winreg_plugins': 'Windows Registry formats'}

  # Mapping of parser name to tuples of the data format name and an optional URL
  # with more information about the data format.
  # TODO: consider extending Plaso parsers and parser plugins with metadata that
  # contain this information.
  _DATA_FORMAT_NAME_AND_URL_PER_PARSER_NAME = {
      'amcache': (
          'AMCache Windows NT Registry file (AMCache.hve)', ''),
      'android_app_usage': (
          'Android usage-history (app usage)', ''),
      'android_calls': (
          'Android calls SQLite database', ''),
      'android_sms': (
          'Android text messages (SMS) SQLite database', ''),
      'android_webview': (
          'Android WebView SQLite database', ''),
      'android_webviewcache': (
          'Android WebViewCache SQLite database', ''),
      'apache_access': (
          'Apache access log file (access.log)', ''),
      'appcompatcache': (
          'Application Compatibility Cache data', ''),
      'appusage': (
          'MacOS application usage SQLite database file', ''),
      'apt_history': (
          'Advanced Packaging Tool (APT) History log file', ''),
      'asl_log': (
          'Apple System Log (ASL) file',
          'dtformats:Apple System Log (ASL) file format'),
      'bagmru': (
          'BagMRU (or ShellBags) data', ''),
      'bam': (
          'Background Activity Moderator (BAM) data', ''),
      'bash_history': (
          'Bash history file', ''),
      'bencode': (
          'Bencoded file', ''),
      'bencode_transmission': (
          'Transmission BitTorrent activity file', ''),
      'bencode_utorrent': (
          'uTorrent active torrent file', ''),
      'binary_cookies': (
          'Safari Cookies file (Cookies.binarycookies)',
          'dtformats:Safari Cookies'),
      'bsm_log': (
          'Basic Security Module (BSM) event auditing file',
          'dtformats:Basic Security Module (BSM) event auditing file format'),
      'ccleaner': (
          'CCleaner data', ''),
      'chrome_17_cookies': (
          'Google Chrome 17 - 65 cookies SQLite database', ''),
      'chrome_27_history': (
          'Google Chrome 27 and later history SQLite database', ''),
      'chrome_66_cookies': (
          'Google Chrome 66 and later cookies SQLite database', ''),
      'chrome_8_history': (
          'Google Chrome 8 - 25 history SQLite database', ''),
      'chrome_autofill': (
          'Google Chrome autofill SQLite database', ''),
      'chrome_cache': (
          'Chrome Cache file',
          'dtformats:Chrome Cache file format'),
      'chrome_extension_activity': (
          'Google Chrome extension activity SQLite database', ''),
      'chrome_preferences': (
          'Google Chrome preferences', ''),
      'cron': (
          'Cron syslog file', ''),
      'cups_ipp': (
          'CUPS IPP', ''),
      'custom_destinations': (
          'Custom destinations jump list file (.customDestinations-ms)',
          'dtformats:Jump lists format'),
      'czip': (
          'Compound ZIP file', ''),
      'dockerjson': (
          'Docker configuration and log JSON files', ''),
      'dpkg': (
          'Debian package manager log file (dpkg.log)', ''),
      'esedb': (
          'Extensible Storage Engine (ESE) Database File (EDB) format',
          ('libyal:libesedb:Extensible Storage Engine (ESE) Database File '
           '(EDB) format')),
      'explorer_mountpoints2': (
          'Windows Explorer mount points data', ''),
      'explorer_programscache': (
          'Windows Explorer Programs Cache data', ''),
      'file_history': (
          'Windows 8 File History database', ''),
      'firefox_cache': (
          'Mozilla Firefox Cache version 1 file (version 31 or earlier)', ''),
      'firefox_cache2': (
          'Mozilla Firefox Cache version 2 file (version 32 or later)', ''),
      'firefox_cookies': (
          'Mozilla Firefox cookies SQLite database', ''),
      'firefox_downloads': (
          'Mozilla Firefox downloads SQLite database', ''),
      'firefox_history': (
          'Mozilla Firefox history SQLite database', ''),
      'fseventsd': (
          'MacOS File System Events Disk Log Stream files (fseventsd)',
          'dtformats:MacOS File System Events Disk Log Stream format'),
      'gdrive_synclog': (
          'Google Drive Sync log file', ''),
      'google_analytics_utma': (
          'Google Analytics __utma cookie', ''),
      'google_analytics_utmb': (
          'Google Analytics __utmb cookie', ''),
      'google_analytics_utmt': (
          'Google Analytics __utmt cookie', ''),
      'google_analytics_utmz': (
          'Google Analytics __utmz cookie', ''),
      'google_drive': (
          'Google Drive SQLite database', ''),
      'googlelog': (
          'Google-formatted log file', ''),
      'hangouts_messages': (
          'Google Hangouts Messages SQLite database', ''),
      'imessage': (
          'iMessage and SMS SQLite databases', ''),
      'java_idx': (
          'Java WebStart IDX',
          'dtformats:Java WebStart Cache IDX file format'),
      'kik_messenger': (
          'iOS Kik messenger SQLite database', ''),
      'kodi': (
          'Kodi videos SQLite database (MyVideos.db)', ''),
      'lnk': (
          'Windows Shortcut File (LNK) format',
          'libyal:liblnk:Windows Shortcut File (LNK) format'),
      'ls_quarantine': (
          'MacOS LS quarantine events SQLite database', ''),
      'mac_appfirewall_log': (
          'MacOS Application firewall', ''),
      'mac_document_versions': (
          'MacOS document revisions SQLite database', ''),
      'mac_keychain': (
          'MacOS Keychain',
          'dtformats:MacOS keychain database file format'),
      'mac_knowledgec': (
          'MacOS Duet / KnowledgeC SQLites database', ''),
      'mac_notes': (
          'MacOS notes SQLite database (NotesV7.storedata)', ''),
      'mac_notificationcenter': (
          'MacOS Notification Center SQLite database', ''),
      'mac_securityd': (
          'MacOS Securityd', ''),
      'mackeeper_cache': (
          'MacOS MacKeeper cache SQLite database', ''),
      'mactime': (
          'mactime file',
          'https://wiki.sleuthkit.org/index.php?title=Mactime'),
      'macwifi': (
          'MacOS Wifi', ''),
      'mcafee_protection': (
          'McAfee Anti-Virus Logs', ''),
      'mft': (
          'NTFS $MFT file system metadata file',
          'libyal:libfsntfs:New Technologies File System (NTFS)'),
      'microsoft_office_mru': (
          'Microsoft Office MRU data', ''),
      'microsoft_outlook_mru': (
          'Microsoft Outlook search MRU data', ''),
      'mrulist_string': (
          ('Most Recently Used (MRU) list (MRUList and MRUListEx) data, '
           'including shell items'), ''),
      'msie_zone': (
          'Microsofer Internet Explorer zone settings data', ''),
      'msie_webcache': (
          ('Internet Explorer WebCache database (WebCacheV01.dat, '
           'WebCacheV24.dat)'), ''),
      'msiecf': (
          ('Microsoft Internet Explorer History File Format (also known as '
           'MSIE 4 - 9 Cache Files or index.dat)'),
          'libyal:libmsiecf:MSIE Cache File (index.dat) format'),
      'mstsc_rdp': (
          'Terminal Server client connection data', ''),
      'mstsc_rdp_mru': (
          'Terminal Server client Most Recently Used (MRU) data', ''),
      'network_drives': (
          'Windows network drives data', ''),
      'networkminer_fileinfo': (
          'NetworkMiner .fileinfos file', ''),
      'networks': (
          'Windows networks data (NetworkList)', ''),
      'olecf': (
          'OLE Compound File',
          'libyal:libolecf:OLE Compound File format'),
      'olecf_automatic_destinations': (
          'Automatic destinations jump list file (.automaticDestinations-ms)',
          'dtformats:Jump lists format'),
      'olecf_document_summary': (
          'Document summary information', ''),
      'olecf_summary': (
          'Summary information (top-level only)', ''),
      'opera_global': (
          'Opera global_history.dat file', ''),
      'opera_typed_history': (
          'Opera typed_history.xml file', ''),
      'oxml': (
          'OpenXML (OXML) file', ''),
      'pe': (
          'Portable Executable (PE) file', ''),
      'plist': (
          'Property list (plist) file', ''),
      'pls_recall': (
          'PL SQL cache file (PL-SQL developer recall file)', ''),
      'popularity_contest': (
          'Popularity Contest log', ''),
      'prefetch': (
          'Windows Prefetch File (PF)',
          'libyal:libscca:Windows Prefetch File (PF) format'),
      'recycle_bin': (
          'Windows Recycle bin $I/$R files', ''),
      'recycle_bin_info2': (
          'Windows Recycle bin INFO2 file', ''),
      'rplog': (
          'Restore Point log file (rp.log)',
          'dtformats:Restore point formats'),
      'safari_historydb': (
          'Safari history SQLite database (History.db)', ''),
      'santa': (
          'Santa log file (santa.log)', ''),
      'sccm': (
          'SCCM client log file', ''),
      'selinux': (
          'SELinux audit log file', ''),
      'setupapi': (
          'Windows SetupAPI text log file',
          ('https://docs.microsoft.com/en-us/windows-hardware/drivers/install/'
           'setupapi-text-logs')),
      'skydrive_log': (
          'OneDrive (or SkyDrive) log file', ''),
      'skydrive_log_old': (
          'OneDrive (or SkyDrive) old log file', ''),
      'skype': (
          'Skype SQLite database (main.db)', ''),
      'sophos_av': (
          'Sophos Anti-Virus log file (SAV.txt)', ''),
      'sqlite': (
          'SQLite database file', ''),
      'srum': (
          'System Resource Usage Monitor (SRUM) database', ''),
      'ssh': (
          'SSH syslog file', ''),
      'symantec_scanlog': (
          'Symantec AV Corporate Edition and Endpoint Protection log', ''),
      'syslog': (
          'Syslog file', ''),
      'systemd_journal': (
          'Systemd journal file', ''),
      'tango_android_profile': (
          'Tango on Android profile SQlite database', ''),
      'tango_android_tc': (
          'Tango on Android tc SQLite database', ''),
      'trendmicro_url': (
          'Trend Micro Office Web Reputation log file', ''),
      'trendmicro_vd': (
          'Trend Micro Office Scan Virus Detection log file', ''),
      'twitter_android': (
          'Twitter on Android SQLite database', ''),
      'twitter_ios': (
          'Twitter on iOS 8+ SQLite database', ''),
      'userassist': (
          'User Assist data', ''),
      'usnjrnl': (
          'NTFS $UsnJrnl:$J file system metadata file',
          'libyal:libfsntfs:New Technologies File System (NTFS)'),
      'utmp': (
          'Linux libc6 utmp login records file (btmp, utmp, wtmp)',
          'dtformats:Utmp login records format'),
      'utmpx': (
          'Mac OS X 10.5 utmpx login records file',
          'dtformats:Utmp login records format'),
      'vsftpd': (
          'vsftpd log file', ''),
      'windows_boot_execute': (
          'Windows boot execution data', ''),
      'windows_boot_verify': (
          'Windows boot verification data', ''),
      'windows_run': (
          'Run and run once data', ''),
      'windows_sam_users': (
          'Security Accounts Manager (SAM) users data', ''),
      'windows_services': (
          'Windows drivers and services data', ''),
      'windows_shutdown': (
          'Windows last shutdown data', ''),
      'windows_task_cache': (
          'Windows Task Scheduler cache data', ''),
      'windows_timeline': (
          'Windows 10 Timeline SQLite database', ''),
      'windows_timezone': (
          'Windows timezone settings', ''),
      'windows_typed_urls': (
          'Windows Explorer typed URLs data', ''),
      'windows_usb_devices': (
          'Windows USB device data', ''),
      'windows_usbstor_devices': (
          'Windows USB storage device data', ''),
      'windows_version': (
          'Windows version information', ''),
      'winevt': (
          'Windows Event Log (EVT) file',
          'libyal:libevt:Windows Event Log (EVT) format'),
      'winevtx': (
          'Windows XML Event Log (EVTX) file',
          'libyal:libevtx:Windows XML Event Log (EVTX)'),
      'winfirewall': (
          'Windows Firewall', ''),
      'winiis': (
          'Microsoft IIS log file', ''),
      'winjob': (
          'Windows Job file (also known as "at jobs"',
          'dtformats:Job file format'),
      'winlogon': (
          'Windows log-on data', ''),
      'winrar_mru': (
          'WinRar archives history data', ''),
      'winreg': (
          'Windows NT Registry File (REGF)',
          'libyal:libregf:Windows NT Registry File (REGF) format'),
      'xchatlog': (
          'Xchat log file', ''),
      'xchatscrollback': (
          'Xchat scrollback log file', ''),
      'zeitgeist': (
          'Zeitgeist activity SQLite database', ''),
      'zsh_extended_history': (
          'Zsh history file', ''),
  }

  _DTFORMATS_URL_PREFIX = (
      'https://github.com/libyal/dtformats/blob/master/documentation')

  # Names of parsers and parser plugins to ignore.
  _PARSER_NAME_IGNORE_LIST = frozenset([
      'base_parser',
      'base_plugin',
      'bencode_plugin',
      'cookie_plugin',
      'czip_plugin',
      'esedb_plugin',
      'filestat',
      'mrulistex_shell_item_list',
      'mrulistex_string',
      'mrulistex_string_and_shell_item',
      'mrulistex_string_and_shell_item_list',
      'mrulist_shell_item_list',
      'olecf_default',
      'olecf_plugin',
      'plist_default',
      'plist_plugin',
      'sqlite_plugin',
      'syslog_plugin',
      'winreg_default',
      'winreg_plugin'])

  _STANDARD_TEXT_PER_CATEGORY = {
      'File system formats': (
          'File System Format support is provided by [dfVFS]'
          '(https://github.com/log2timeline/dfvfs/wiki#file-systems).'),
      'Storage media image file formats': (
          'Storage media image file format support is provided by [dfVFS]'
          '(https://github.com/log2timeline/dfvfs/wiki#storage-media-types).'),
      'Volume system formats': (
          'Volume system format support is provided by [dfVFS]'
          '(https://github.com/log2timeline/dfvfs/wiki#volume-systems).')}

  def FormatDataFormats(self, data_format_descriptors):
    """Formats data format information.

    Args:
      data_format_descriptors (list[DataFormatDescriptor]): data format
          descriptors.

    Returns:
      str: information about data formats.
    """
    lines = [
        '## Supported Formats',
        '',
        'The information below is based of version {0:s}'.format(
            plaso.__version__),
        '']

    descriptors_per_category = collections.defaultdict(list)
    for data_format_descriptor in data_format_descriptors:
      descriptors_per_category[data_format_descriptor.category].append(
          data_format_descriptor)

    for category in self._CATEGORIES_OUTPUT_ORDER:
      lines.append('### {0:s}'.format(category))
      lines.append('')

      standard_text = self._STANDARD_TEXT_PER_CATEGORY.get(category, None)
      if standard_text is not None:
        lines.append(standard_text)

      lines_per_category = []
      data_format_descriptors = descriptors_per_category.get(category, [])
      for data_format_descriptor in sorted(
          data_format_descriptors, key=lambda cls: cls.name):
        url = data_format_descriptor.url

        # TODO: add support for more generic generation of using information.
        if url.startswith('dtformats:'):
          url = url.split(':')[1]
          url = urllib_parse.quote(url)
          url = '{0:s}/{1:s}.asciidoc'.format(self._DTFORMATS_URL_PREFIX, url)
          line = '* [{0:s}]({1:s})'.format(data_format_descriptor.name, url)

        elif url.startswith('libyal:'):
          library_name, url = url.split(':')[1:3]
          library_url = 'https://github.com/libyal/{0:s}'.format(library_name)
          url = urllib_parse.quote(url)
          url = '{0:s}/blob/master/documentation/{1:s}.asciidoc'.format(
              library_url, url)
          line = '* [{0:s}]({1:s}) using [{2:s}]({3:s})'.format(
              data_format_descriptor.name, url, library_name, library_url)

        elif url.startswith('http:') or url.startswith('https:'):
          line = '* [{0:s}]({1:s})'.format(data_format_descriptor.name, url)

        else:
          line = '* {0:s}'.format(data_format_descriptor.name)

        lines_per_category.append(line)

      # Sort the lines per category case-insensitive and ignoring
      # non-alphanumeric characters.
      lines_per_category = sorted(
          lines_per_category,
          key=lambda name: ''.join(filter(str.isalnum, name.lower())))
      lines.extend(lines_per_category)

      if standard_text or data_format_descriptors:
        lines.append('')

    return '\n'.join(lines)

  def _GetDataFormatInformationFromPackage(self, package):
    """Retrieves event data attribute containers from a package.

    Args:
      package (list[str]): package name segments such as ["plaso", "parsers"].

    Returns:
      list[DataFormatDescriptor]: data format descriptors.
    """
    data_format_descriptors = []
    package_path = '/'.join(package)
    for _, name, is_package in pkgutil.iter_modules(path=[package_path]):
      sub_package = list(package)
      sub_package.append(name)
      if is_package:
        sub_data_format_descriptors = (
            self._GetDataFormatInformationFromPackage(sub_package))
        data_format_descriptors.extend(sub_data_format_descriptors)
      else:
        module_path = '.'.join(sub_package)
        module_object = importlib.import_module(module_path)

        for _, cls in inspect.getmembers(module_object, inspect.isclass):
          if issubclass(cls, (
              parsers_interface.BaseParser, parsers_plugins.BasePlugin)):

            # TODO: detect corresponding dtFabric .yaml file
            parser_name = getattr(cls, 'NAME', None)
            if not parser_name or parser_name in self._PARSER_NAME_IGNORE_LIST:
              continue

            category = self._DATA_FORMAT_CATEGORY_PER_PACKAGE_PATH.get(
                package_path, 'File formats')

            name = getattr(cls, 'DATA_FORMAT', None)
            url = ''
            if not name:
              name, url = self._DATA_FORMAT_NAME_AND_URL_PER_PARSER_NAME.get(
                  parser_name, (parser_name, ''))

            data_format_descriptor = DataFormatDescriptor(
                category=category, name=name, url=url)
            data_format_descriptors.append(data_format_descriptor)

    return data_format_descriptors

  def GetDataFormatInformation(self):
    """Retrieves data format information from Plaso.

    Returns:
      list[DataFormatDescriptor]: data format descriptors.
    """
    return self._GetDataFormatInformationFromPackage(['plaso'])


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Extract data format information from Plaso.'))

  # TODO: option to export for information on forensicswiki.
  # TODO: add information about supported compressed stream formats.
  # TODO: add information about supported archive file formats.

  argument_parser.parse_args()

  extractor = DataFormatInformationExractor()

  data_format_descriptors = extractor.GetDataFormatInformation()
  if not data_format_descriptors:
    print('Unable to determine data format information')
    return False

  output_text = extractor.FormatDataFormats(data_format_descriptors)
  print(output_text)

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
