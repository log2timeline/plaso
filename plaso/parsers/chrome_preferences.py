# -*- coding: utf-8 -*-
"""A parser for the Chrome preferences file."""

import json
import logging
import os

from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


class ChromePreferencesEvent(time_events.WebKitTimeEvent):
  """Convenience class for Chrome Preferences file events."""

  DATA_TYPE = u'chrome:preferences'


class ChromePreferencesClearHistoryEvent(ChromePreferencesEvent):
  """Convenience class for Chrome history clearing events."""

  DATA_TYPE = u'chrome:preferences:clear_history'

  def __init__(self, timestamp):
    """Initialize the event."""
    super(ChromePreferencesClearHistoryEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.DELETED_TIME)
    self.message = u'Chrome history was cleared by user'


class ChromeExtensionInstallationEvent(time_events.WebKitTimeEvent):
  """Convenience class for Chrome Extension events."""

  DATA_TYPE = u'chrome:preferences:extension_installation'

  def __init__(self, timestamp, extension_id, extension_name, path):
    """Initialize the event."""
    super(ChromeExtensionInstallationEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.extension_id = extension_id
    self.extension_name = extension_name
    self.path = path


class ChromePreferencesParser(interface.FileObjectParser):
  """Parses Chrome Preferences files."""

  NAME = u'chrome_preferences'

  DESCRIPTION = u'Parser for Chrome Preferences files.'

  REQUIRED_KEYS = frozenset([u'browser', u'extensions'])

  def _ExtractExtensionInstallEvents(self, settings_dict, parser_mediator):
    """Extract extension installation events.

    Args:
      settings_dict: A dictionary of settings data from Preferences file.
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    for extension_id, extension in sorted(settings_dict.items()):
      try:
        install_time = int(extension.get(u'install_time', u'0'), 10)
      except ValueError as exception:
        logging.warning(
            u'Extension ID {0:s} is missing timestamp: {1:s}'.format(
                extension_id, exception))
        continue
      manifest = extension.get(u'manifest')
      if manifest:
        extension_name = manifest.get(u'name')
      else:
        extension_name = None
      path = extension.get(u'path')
      event = ChromeExtensionInstallationEvent(
          install_time, extension_id, extension_name, path)
      parser_mediator.ProduceEvent(event)

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a Chrome preferences file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    # First pass check for initial character being open brace.
    file_object.seek(0, os.SEEK_SET)

    if file_object.read(1) != b'{':
      raise errors.UnableToParseFile((
          u'[{0:s}] {1:s} is not a valid Preference file, '
          u'missing opening brace.').format(
              self.NAME, parser_mediator.GetDisplayName()))

    file_object.seek(0, os.SEEK_SET)

    # Second pass to verify it's valid JSON
    try:
      json_dict = json.load(file_object)
    except ValueError as exception:
      raise errors.UnableToParseFile((
          u'[{0:s}] Unable to parse file {1:s} as '
          u'JSON: {2:s}').format(
              self.NAME, parser_mediator.GetDisplayName(), exception))
    except IOError as exception:
      raise errors.UnableToParseFile((
          u'[{0:s}] Unable to open file {1:s} for parsing as'
          u'JSON: {2:s}').format(
              self.NAME, parser_mediator.GetDisplayName(), exception))

    # Third pass to verify the file has the correct keys in it for Preferences
    if not set(self.REQUIRED_KEYS).issubset(set(json_dict.keys())):
      raise errors.UnableToParseFile(u'File does not contain Preference data.')

    extensions_setting_dict = json_dict.get(u'extensions')
    if not extensions_setting_dict:
      raise errors.UnableToParseFile(
          u'[{0:s}] {1:s} is not a valid Preference file, '
          u'does not contain extensions value.'.format(
              self.NAME, parser_mediator.GetDisplayName()))
    extensions_dict = extensions_setting_dict.get(u'settings')
    if not extensions_dict:
      raise errors.UnableToParseFile(
          u'[{0:s}] {1:s} is not a valid Preference file, '
          u'does not contain extensions settings value.'.format(
              self.NAME, parser_mediator.GetDisplayName()))

    browser_dict = json_dict.get(u'browser', None)
    if browser_dict and u'last_clear_browsing_data_time' in browser_dict:
      last_clear_history_timestamp = browser_dict.get(
          u'last_clear_browsing_data_time', u'0')
      last_clear_history = int(last_clear_history_timestamp, 10)
      event = ChromePreferencesClearHistoryEvent(last_clear_history)
      parser_mediator.ProduceEvent(event)

    self._ExtractExtensionInstallEvents(extensions_dict, parser_mediator)


manager.ParsersManager.RegisterParser(ChromePreferencesParser)
