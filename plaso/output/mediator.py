# -*- coding: utf-8 -*-
"""The output mediator object."""

import glob
import os
import pytz

from plaso.engine import path_helper
from plaso.formatters import default
from plaso.formatters import manager as formatters_manager
from plaso.formatters import yaml_formatters_file
from plaso.helpers.windows import languages
from plaso.lib import definitions
from plaso.output import logger
from plaso.output import winevt_rc


class OutputMediator(object):
  """Output mediator.

  Attributes:
    data_location (Optional[str]): path of the formatter data files.
  """

  _DEFAULT_LANGUAGE_TAG = 'en-US'

  # LCID 0x0409 is en-US.
  _DEFAULT_LCID = 0x0409

  _DEFAULT_MESSAGE_FORMATTER = default.DefaultEventFormatter()

  _DEFAULT_TIME_ZONE = pytz.UTC

  _WINEVT_RC_DATABASE = 'winevt-rc.db'

  def __init__(
      self, knowledge_base, data_location=None, dynamic_time=False,
      preferred_encoding='utf-8'):
    """Initializes an output mediator.

    Args:
      knowledge_base (KnowledgeBase): knowledge base.
      data_location (Optional[str]): path of the formatter data files.
      dynamic_time (Optional[bool]): True if date and time values should be
          represented in their granularity or semantically.
      preferred_encoding (Optional[str]): preferred encoding to output.
    """
    super(OutputMediator, self).__init__()
    self._dynamic_time = dynamic_time
    self._knowledge_base = knowledge_base
    self._language_tag = self._DEFAULT_LANGUAGE_TAG
    self._lcid = self._DEFAULT_LCID
    self._message_formatters = {}
    self._preferred_encoding = preferred_encoding
    self._storage_reader = None
    self._text_prepend = None
    self._time_zone = None

    self.data_location = data_location

  @property
  def dynamic_time(self):
    """bool: True if date and time values should be represented in their
             granularity or semantically.
    """
    return self._dynamic_time

  @property
  def encoding(self):
    """str: preferred encoding."""
    return self._preferred_encoding

  @property
  def timezone(self):
    """The time zone."""
    if not self._time_zone:
      self._time_zone = self._DEFAULT_TIME_ZONE

    return self._time_zone

  def _ReadMessageFormattersFile(self, path):
    """Reads a message formatters configuration file.

    Args:
      path (str): path of file that contains the message formatters
           configuration.

    Raises:
      KeyError: if the message formatter is already set for the corresponding
          data type.
    """
    message_formatters_file = yaml_formatters_file.YAMLFormattersFile()
    for message_formatter in message_formatters_file.ReadFromFile(path):
      for identifier in message_formatter.custom_helpers:
        custom_formatter_helper = (
             formatters_manager.FormattersManager.GetEventFormatterHelper(
                identifier))
        if custom_formatter_helper:
          message_formatter.AddHelper(custom_formatter_helper)

      self._message_formatters[message_formatter.data_type] = message_formatter

  def GetDisplayNameForPathSpec(self, path_spec):
    """Retrieves the display name for a path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      str: human readable version of the path specification.
    """
    return path_helper.PathHelper.GetDisplayNameForPathSpec(
        path_spec, text_prepend=self._text_prepend)

  def GetHostname(self, event_data, default_hostname='-'):
    """Retrieves the hostname related to the event.

    Args:
      event_data (EventData): event data.
      default_hostname (Optional[str]): default hostname.

    Returns:
      str: hostname.
    """
    hostname = getattr(event_data, 'hostname', None)
    if hostname:
      return hostname

    hostname = self._knowledge_base.GetHostname()
    return hostname or default_hostname

  def GetMACBRepresentation(self, event, event_data):
    """Retrieves the MACB representation.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

    Returns:
      str: MACB representation.
    """
    data_type = getattr(event_data, 'data_type', None)
    if not data_type:
      return '....'

    # The filestat parser is somewhat limited.
    if data_type == 'fs:stat':
      descriptions = event.timestamp_desc.split(';')

      return_characters = ['.', '.', '.', '.']
      for description in descriptions:
        if description in (
            'mtime', definitions.TIME_DESCRIPTION_MODIFICATION):
          return_characters[0] = 'M'
        elif description in (
            'atime', definitions.TIME_DESCRIPTION_LAST_ACCESS):
          return_characters[1] = 'A'
        elif description in (
            'ctime', definitions.TIME_DESCRIPTION_CHANGE):
          return_characters[2] = 'C'
        elif description in (
            'crtime', definitions.TIME_DESCRIPTION_CREATION):
          return_characters[3] = 'B'

      return ''.join(return_characters)

    # Access time.
    if event.timestamp_desc in [
        definitions.TIME_DESCRIPTION_LAST_ACCESS,
        definitions.TIME_DESCRIPTION_ACCOUNT_CREATED,
        definitions.TIME_DESCRIPTION_LAST_VISITED,
        definitions.TIME_DESCRIPTION_START,
        definitions.TIME_DESCRIPTION_LAST_SHUTDOWN,
        definitions.TIME_DESCRIPTION_LAST_LOGIN,
        definitions.TIME_DESCRIPTION_LAST_PASSWORD_RESET,
        definitions.TIME_DESCRIPTION_LAST_CONNECTED,
        definitions.TIME_DESCRIPTION_LAST_RUN,
        definitions.TIME_DESCRIPTION_LAST_PRINTED]:
      return '.A..'

    # Content modification.
    if event.timestamp_desc in [
        definitions.TIME_DESCRIPTION_MODIFICATION,
        definitions.TIME_DESCRIPTION_WRITTEN,
        definitions.TIME_DESCRIPTION_DELETED]:
      return 'M...'

    # Content creation time.
    if event.timestamp_desc in [
        definitions.TIME_DESCRIPTION_CREATION,
        definitions.TIME_DESCRIPTION_ADDED,
        definitions.TIME_DESCRIPTION_FILE_DOWNLOADED,
        definitions.TIME_DESCRIPTION_FIRST_CONNECTED]:
      return '...B'

    # Metadata modification.
    if event.timestamp_desc in [
        definitions.TIME_DESCRIPTION_CHANGE,
        definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION]:
      return '..C.'

    return '....'

  def GetMACBRepresentationFromDescriptions(self, timestamp_descriptions):
    """Determines the MACB representation from the timestamp descriptions.

    MACB representation is a shorthand for representing one or more of
    modification, access, change, birth timestamp descriptions as the letters
    "MACB" or a "." if the corresponding timestamp is not set.

    Note that this is an output format shorthand and does not guarantee that
    the timestamps represent the same occurrence.

    Args:
      timestamp_descriptions (list[str]): timestamp descriptions, which are
          defined in definitions.TIME_DESCRIPTIONS.

    Returns:
      str: MACB representation.
    """
    macb_representation = []

    if ('mtime' in timestamp_descriptions or
        definitions.TIME_DESCRIPTION_MODIFICATION in timestamp_descriptions):
      macb_representation.append('M')
    else:
      macb_representation.append('.')

    if ('atime' in timestamp_descriptions or
        definitions.TIME_DESCRIPTION_LAST_ACCESS in timestamp_descriptions):
      macb_representation.append('A')
    else:
      macb_representation.append('.')

    if ('ctime' in timestamp_descriptions or
        definitions.TIME_DESCRIPTION_CHANGE in timestamp_descriptions):
      macb_representation.append('C')
    else:
      macb_representation.append('.')

    if ('crtime' in timestamp_descriptions or
        definitions.TIME_DESCRIPTION_CREATION in timestamp_descriptions):
      macb_representation.append('B')
    else:
      macb_representation.append('.')

    return ''.join(macb_representation)

  def GetMessageFormatter(self, data_type):
    """Retrieves the message formatter for a specific data type.

    Args:
      data_type (str): data type.

    Returns:
      EventFormatter: corresponding message formatter or the default message
          formatter if not available.
    """
    data_type = data_type.lower()
    message_formatter = self._message_formatters.get(data_type, None)
    if not message_formatter:
      logger.warning(
          'Using default message formatter for data type: {0:s}'.format(
              data_type))
      message_formatter = self._DEFAULT_MESSAGE_FORMATTER

    return message_formatter

  def GetRelativePathForPathSpec(self, path_spec):
    """Retrieves the relative path for a path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      str: relateive path of the path specification.
    """
    return path_helper.PathHelper.GetRelativePathForPathSpec(path_spec)

  def GetUsername(self, event_data, default_username='-'):
    """Retrieves the username related to the event.

    Args:
      event_data (EventData): event data.
      default_username (Optional[str]): default username.

    Returns:
      str: username.
    """
    username = getattr(event_data, 'username', None)
    if username and username != '-':
      return username

    user_sid = getattr(event_data, 'user_sid', None)
    username = self._knowledge_base.GetUsernameByIdentifier(user_sid)
    return username or default_username

  def GetWinevtResourcesHelper(self):
    """Retrieves a Windows EventLog resources helper.

    Returns:
      WinevtResourcesHelper: Windows EventLog resources helper.
    """
    lcid = self._lcid or self._DEFAULT_LCID
    environment_variables = self._knowledge_base.GetEnvironmentVariables()
    return winevt_rc.WinevtResourcesHelper(
        self._storage_reader, self.data_location, lcid, environment_variables)

  def ReadMessageFormattersFromDirectory(self, path):
    """Reads message formatters from a directory.

    Args:
      path (str): path of directory that contains the message formatters
          configuration files.

    Raises:
      KeyError: if the message formatter is already set for the corresponding
          data type.
    """
    for formatters_file_path in glob.glob(os.path.join(path, '*.yaml')):
      self._ReadMessageFormattersFile(formatters_file_path)

  def ReadMessageFormattersFromFile(self, path):
    """Reads message formatters from a file.

    Args:
      path (str): path of file that contains the message formatters
          configuration.

    Raises:
      KeyError: if the message formatter is already set for the corresponding
          data type.
    """
    self._ReadMessageFormattersFile(path)

  def SetPreferredLanguageIdentifier(self, language_tag):
    """Sets the preferred language identifier.

    Args:
      language_tag (str): language tag such as "en-US" for US English or
          "is-IS" for Icelandic.

    Raises:
      ValueError: if the language tag is not a string type or no LCID can
          be determined that corresponds with the language tag.
    """
    lcid = None
    if language_tag:
      if not isinstance(language_tag, str):
        raise ValueError('Language tag: {0!s} is not a string.'.format(
            language_tag))

      lcid = languages.WindowsLanguageHelper.GetLCIDForLanguageTag(language_tag)
      if not lcid:
        raise ValueError('No LCID found for language tag: {0:s}.'.format(
            language_tag))

    self._language_tag = language_tag
    self._lcid = lcid

  def SetStorageReader(self, storage_reader):
    """Sets the storage reader.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    self._storage_reader = storage_reader

  def SetTextPrepend(self, text_prepend):
    """Sets the text to prepend to the display name.

    Args:
      text_prepend (str): text to prepend to the display name or None if no
          text should be prepended.
    """
    self._text_prepend = text_prepend

  def SetTimeZone(self, time_zone):
    """Sets the time zone.

    Args:
      time_zone (str): time zone.

    Raises:
      ValueError: if the time zone is not supported.
    """
    if time_zone:
      try:
        time_zone = pytz.timezone(time_zone)
      except pytz.UnknownTimeZoneError:
        raise ValueError('Unsupported time zone: {0:s}'.format(time_zone))

    self._time_zone = time_zone
