# -*- coding: utf-8 -*-
"""A parser for the Chrome preferences file."""

import codecs
import json
import os

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import webkit_time as dfdatetime_webkit_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class ChromeContentSettingsExceptionsEventData(events.EventData):
  """Chrome content settings exceptions event data.

  Attributes:
    last_visited_time (dfdatetime.DateTimeValues): date and time the URL was
        last visited.
    permission (str): permission.
    primary_url (str): primary URL.
    secondary_url (str): secondary URL.
  """

  DATA_TYPE = 'chrome:preferences:content_settings:exceptions'

  def __init__(self):
    """Initializes event data."""
    super(ChromeContentSettingsExceptionsEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.last_visited_time = None
    self.permission = None
    self.primary_url = None
    self.secondary_url = None


class ChromeExtensionsAutoupdaterEventData(events.EventData):
  """Chrome Extension Autoupdater event data.

  Attributes:
    message (str): message.
    recorded_time (dfdatetime.DateTimeValues): date and time the entry
        was recorded.
  """

  DATA_TYPE = 'chrome:preferences:extensions_autoupdater'

  def __init__(self):
    """Initializes event data."""
    super(ChromeExtensionsAutoupdaterEventData, self).__init__(
        data_type=self.DATA_TYPE)
    # TODO: refactor this in something more descriptive.
    self.message = None
    self.recorded_time = None


class ChromeExtensionInstallationEventData(events.EventData):
  """Chrome extension event data.

  Attributes:
    extension_identifier (str): extension identifier.
    extension_name (str): extension name.
    installation_time (dfdatetime.DateTimeValues): date and time the Chrome
        extension was installed.
    path (str): path.
  """

  DATA_TYPE = 'chrome:preferences:extension_installation'

  def __init__(self):
    """Initializes event data."""
    super(ChromeExtensionInstallationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.extension_identifier = None
    self.extension_name = None
    self.installation_time = None
    self.path = None


class ChromePreferencesParser(interface.FileObjectParser):
  """Parses Chrome Preferences files."""

  NAME = 'chrome_preferences'

  DATA_FORMAT = 'Google Chrome Preferences file'

  REQUIRED_KEYS = frozenset(['browser', 'extensions'])

  _ENCODING = 'utf-8'

  # TODO: add site_engagement & ssl_cert_decisions.
  _EXCEPTIONS_KEYS = frozenset([
      'geolocation',
      'media_stream_camera',
      'media_stream_mic',
      'midi_sysex',
      'notifications',
      'push_messaging'])

  _MAXIMUM_FILE_SIZE = 16 * 1024 * 1024

  def _ExtractExtensionInstallEvents(self, settings_dict, parser_mediator):
    """Extract extension installation events.

    Args:
      settings_dict (dict[str: object]): settings data from a Preferences file.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """
    for extension_id, extension in sorted(settings_dict.items()):
      install_time = extension.get('install_time', None)
      if not install_time:
        parser_mediator.ProduceExtractionWarning(
            'installation time missing for extension ID {0:s}'.format(
                extension_id))
        continue

      try:
        install_time = int(install_time, 10)
      except ValueError:
        parser_mediator.ProduceExtractionWarning((
            'unable to convert installation time for extension ID '
            '{0:s}').format(extension_id))
        continue

      manifest = extension.get('manifest', None)
      if not manifest:
        parser_mediator.ProduceExtractionWarning(
            'manifest missing for extension ID {0:s}'.format(extension_id))
        continue

      event_data = ChromeExtensionInstallationEventData()
      event_data.extension_identifier = extension_id
      event_data.extension_name = manifest.get('name', None)
      event_data.installation_time = dfdatetime_webkit_time.WebKitTime(
          timestamp=install_time)
      event_data.path = extension.get('path', None)

      parser_mediator.ProduceEventData(event_data)

  def _ExtractContentSettingsExceptions(self, exceptions_dict, parser_mediator):
    """Extracts site specific events.

    Args:
      exceptions_dict (dict): Permission exceptions data from Preferences file.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """
    for permission in exceptions_dict:
      if permission not in self._EXCEPTIONS_KEYS:
        continue

      exception_dict = exceptions_dict.get(permission, {})
      for urls, url_dict in exception_dict.items():
        last_used = url_dict.get('last_used', None)
        if not last_used:
          continue

        timestamp = int(last_used * 1000000)

        # If secondary_url is '*', the permission applies to primary_url.
        # If secondary_url is a valid URL, the permission applies to
        # elements loaded from secondary_url being embedded in primary_url.
        primary_url, secondary_url = urls.split(',')

        event_data = ChromeContentSettingsExceptionsEventData()
        event_data.last_visited_time = (
            dfdatetime_posix_time.PosixTimeInMicroseconds(timestamp=timestamp))
        event_data.permission = permission
        event_data.primary_url = primary_url or None
        event_data.secondary_url = secondary_url or None

        parser_mediator.ProduceEventData(event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a Chrome preferences file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    # First pass check for initial character being open brace.
    if file_object.read(1) != b'{':
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser((
          '[{0:s}] {1:s} is not a valid Preference file, missing opening '
          'brace.').format(self.NAME, display_name))

    file_object.seek(0, os.SEEK_SET)

    # Note that _MAXIMUM_FILE_SIZE prevents this read to become too large.
    file_content = file_object.read()

    try:
      file_content = codecs.decode(file_content, self._ENCODING)
    except UnicodeDecodeError:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser((
          '[{0:s}] {1:s} is not a valid Preference file, unable to decode '
          'UTF-8.').format(self.NAME, display_name))

    # Second pass to verify it's valid JSON
    try:
      json_dict = json.loads(file_content)

    except ValueError as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser((
          '[{0:s}] Unable to parse file {1:s} as JSON: {2!s}').format(
              self.NAME, display_name, exception))

    except IOError as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser((
          '[{0:s}] Unable to open file {1:s} for parsing as JSON: '
          '{2!s}').format(self.NAME, display_name, exception))

    # Third pass to verify the file has the correct keys in it for Preferences
    if not set(self.REQUIRED_KEYS).issubset(set(json_dict.keys())):
      raise errors.WrongParser('File does not contain Preference data.')

    extensions_setting_dict = json_dict.get('extensions')
    if not extensions_setting_dict:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser((
          '[{0:s}] {1:s} is not a valid Preference file, does not contain '
          'extensions value.').format(self.NAME, display_name))

    extensions_dict = extensions_setting_dict.get('settings')
    if not extensions_dict:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser((
          '[{0:s}] {1:s} is not a valid Preference file, does not contain '
          'extensions settings value.').format(self.NAME, display_name))

    extensions_autoupdate_dict = extensions_setting_dict.get('autoupdate')
    if extensions_autoupdate_dict:
      autoupdate_lastcheck_timestamp = extensions_autoupdate_dict.get(
          'last_check', None)

      if autoupdate_lastcheck_timestamp:
        autoupdate_lastcheck = int(autoupdate_lastcheck_timestamp, 10)

        event_data = ChromeExtensionsAutoupdaterEventData()
        event_data.message = 'Chrome extensions autoupdater last run'
        event_data.recorded_time = dfdatetime_webkit_time.WebKitTime(
            timestamp=autoupdate_lastcheck)

        parser_mediator.ProduceEventData(event_data)

      autoupdate_nextcheck_timestamp = extensions_autoupdate_dict.get(
          'next_check', None)
      if autoupdate_nextcheck_timestamp:
        autoupdate_nextcheck = int(autoupdate_nextcheck_timestamp, 10)

        event_data = ChromeExtensionsAutoupdaterEventData()
        event_data.message = 'Chrome extensions autoupdater next run'
        event_data.recorded_time = dfdatetime_webkit_time.WebKitTime(
            timestamp=autoupdate_nextcheck)

        parser_mediator.ProduceEventData(event_data)

    browser_dict = json_dict.get('browser', None)
    if browser_dict and 'last_clear_browsing_data_time' in browser_dict:
      last_clear_history_timestamp = browser_dict.get(
          'last_clear_browsing_data_time', None)

      if last_clear_history_timestamp:
        last_clear_history = int(last_clear_history_timestamp, 10)

        event_data = ChromeExtensionsAutoupdaterEventData()
        event_data.message = 'Chrome history was cleared by user'
        event_data.recorded_time = dfdatetime_webkit_time.WebKitTime(
            timestamp=last_clear_history)

        parser_mediator.ProduceEventData(event_data)

    self._ExtractExtensionInstallEvents(extensions_dict, parser_mediator)

    profile_dict = json_dict.get('profile', None)
    if profile_dict:
      content_settings_dict = profile_dict.get('content_settings', None)
      if content_settings_dict:
        exceptions_dict = content_settings_dict.get('exceptions', None)
        if exceptions_dict:
          self._ExtractContentSettingsExceptions(
              exceptions_dict, parser_mediator)


manager.ParsersManager.RegisterParser(ChromePreferencesParser)
