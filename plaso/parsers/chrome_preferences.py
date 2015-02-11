#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 The Plaso Project Authors.
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
"""A parser for the Chrome preferences file."""

import json
import logging

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


class ChromeExtensionInstallationEvent(time_events.WebKitTimeEvent):
  """Convenience class for Chrome Extension events."""

  DATA_TYPE = 'chrome:preferences:extension_installation'

  def __init__(self, timestamp, extension_id, extension_name, path):
    """Initialize the event."""
    super(ChromeExtensionInstallationEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.extension_id = extension_id
    self.extension_name = extension_name
    self.path = path


class ChromePreferencesParser(interface.BaseParser):
  """Parses Chrome Preferences files."""

  NAME = 'chrome_preferences'

  DESCRIPTION = u'Parser for Chrome Preferences files.'

  REQUIRED_KEYS = frozenset(('browser', 'extensions'))

  def _ExtractExtensionInstallationEvents(self, settings_dict):
    """Extract extension installation events.

    Args:
      settings_dict: A dictionary of settings data from Preferences file.

    Yields:
      A tuple of: install_time, extension_id, extension_name, path.
    """
    for extension_id, extension in settings_dict.iteritems():
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
      yield install_time, extension_id, extension_name, path

  def Parse(self, parser_mediator, **kwargs):
    """Attempt to parse a file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    # First pass check for initial character being open brace
    file_object = parser_mediator.GetFileObject()
    if file_object.tell() != 0:
      file_object.seek(0)
    if file_object.read(1) != '{':
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] {1:s} is not a valid Preference file, '
          u'missing opening brace.'.format(
              self.NAME, parser_mediator.GetDisplayName()))
    file_object.seek(0)

    # Second pass to verify it's valid JSON
    try:
      json_dict = json.load(file_object)
    except ValueError as exception:
      file_object.close()
      raise errors.UnableToParseFile(
           u'[{0:s}] Unable to parse file {1:s} as '
           u'JSON: {2:s}'.format(
              self.NAME, parser_mediator.GetDisplayName(), exception))
    except IOError as exception:
      file_object.close()
      raise errors.errors.UnableToParseFile(
          u'[{0:s}] Unable to open file {1:s} for parsing as'
          u'JSON: {2:s}'.format(
              self.NAME, parser_mediator.GetDisplayName(), exception))

    # Third pass to verify the file has the correct keys in it for Preferences
    if not set(self.REQUIRED_KEYS).issubset(set(json_dict.keys())):
      file_object.close()
      raise errors.UnableToParseFile(u'File does not contain Preference data.')

    extensions_setting_dict = json_dict.get(u'extensions')
    if not extensions_setting_dict:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] {1:s} is not a valid Preference file, '
          u'does not contain extensions value.'.format(
              self.NAME, parser_mediator.GetDisplayName()))
    extensions_dict = extensions_setting_dict.get(u'settings')
    if not extensions_dict:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] {1:s} is not a valid Preference file, '
          u'does not contain extensions settings value.'.format(
              self.NAME, parser_mediator.GetDisplayName()))
    # Callback used due to line length constraints.
    callback = self._ExtractExtensionInstallationEvents
    for install_time, extension_id, extension_name, path in callback(
        extensions_dict):
      event_object = ChromeExtensionInstallationEvent(
          install_time, extension_id, extension_name, path)
      parser_mediator.ProduceEvent(event_object)

    file_object.close()


manager.ParsersManager.RegisterParser(ChromePreferencesParser)
