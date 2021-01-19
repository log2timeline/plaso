# -*- coding: utf-8 -*-
"""The output mediator object."""

import glob
import os
import pytz

from plaso.engine import path_helper
from plaso.formatters import default
from plaso.formatters import manager as formatters_manager
from plaso.formatters import winevt_rc
from plaso.formatters import yaml_formatters_file
from plaso.lib import definitions
from plaso.output import logger
from plaso.winnt import language_ids


class OutputMediator(object):
  """Output mediator.

  Attributes:
    data_location (Optional[str]): path of the formatter data files.
  """

  DEFAULT_LANGUAGE_IDENTIFIER = 'en-US'

  # TODO: add smarter language ID to LCID resolving e.g.
  # 'en-US' falls back to 'en'.
  # LCID 0x0409 is en-US.
  DEFAULT_LCID = 0x0409

  _DEFAULT_MESSAGE_FORMATTER = default.DefaultEventFormatter()

  _WINEVT_RC_DATABASE = 'winevt-rc.db'

  def __init__(
      self, knowledge_base, data_location=None, preferred_encoding='utf-8'):
    """Initializes an output mediator.

    Args:
      knowledge_base (KnowledgeBase): knowledge base.
      data_location (Optional[str]): path of the formatter data files.
      preferred_encoding (Optional[str]): preferred encoding to output.
    """
    super(OutputMediator, self).__init__()
    self._knowledge_base = knowledge_base
    self._language_identifier = self.DEFAULT_LANGUAGE_IDENTIFIER
    self._lcid = self.DEFAULT_LCID
    self._message_formatters = {}
    self._preferred_encoding = preferred_encoding
    self._timezone = pytz.UTC
    self._winevt_database_reader = None

    self.data_location = data_location

  @property
  def encoding(self):
    """str: preferred encoding."""
    return self._preferred_encoding

  @property
  def timezone(self):
    """The timezone."""
    return self._timezone

  def _GetWinevtRcDatabaseReader(self):
    """Opens the Windows Event Log resource database reader.

    Returns:
      WinevtResourcesSqlite3DatabaseReader: Windows Event Log resource
          database reader or None.
    """
    if not self._winevt_database_reader and self.data_location:
      database_path = os.path.join(
          self.data_location, self._WINEVT_RC_DATABASE)
      if not os.path.isfile(database_path):
        return None

      self._winevt_database_reader = (
          winevt_rc.WinevtResourcesSqlite3DatabaseReader())
      if not self._winevt_database_reader.Open(database_path):
        self._winevt_database_reader = None

    return self._winevt_database_reader

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
    mount_path = self._knowledge_base.GetMountPath()
    text_prepend = self._knowledge_base.GetTextPrepend()
    return path_helper.PathHelper.GetDisplayNameForPathSpec(
        path_spec, mount_path=mount_path, text_prepend=text_prepend)

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

    session_identifier = event_data.GetSessionIdentifier()
    if session_identifier is None:
      return default_hostname

    hostname = self._knowledge_base.GetHostname(
        session_identifier=session_identifier)
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
    mount_path = self._knowledge_base.GetMountPath()
    return path_helper.PathHelper.GetRelativePathForPathSpec(
        path_spec, mount_path=mount_path)

  def GetStoredHostname(self):
    """Retrieves the stored hostname.

    Returns:
      str: hostname.
    """
    return self._knowledge_base.GetHostname()

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

    session_identifier = event_data.GetSessionIdentifier()
    if session_identifier is None:
      return default_username

    user_sid = getattr(event_data, 'user_sid', None)
    username = self._knowledge_base.GetUsernameByIdentifier(
        user_sid, session_identifier=session_identifier)
    return username or default_username

  def GetWindowsEventMessage(self, log_source, message_identifier):
    """Retrieves the message string for a specific Windows Event Log source.

    Args:
      log_source (str): Event Log source, such as "Application Error".
      message_identifier (int): message identifier.

    Returns:
      str: message string or None if not available.
    """
    database_reader = self._GetWinevtRcDatabaseReader()
    if not database_reader:
      return None

    if self._lcid != self.DEFAULT_LCID:
      message_string = database_reader.GetMessage(
          log_source, self._lcid, message_identifier)
      if message_string:
        return message_string

    return database_reader.GetMessage(
        log_source, self.DEFAULT_LCID, message_identifier)

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

  def SetPreferredLanguageIdentifier(self, language_identifier):
    """Sets the preferred language identifier.

    Args:
      language_identifier (str): language identifier string such as "en-US"
          for US English or "is-IS" for Icelandic.

    Raises:
      KeyError: if the language identifier is not defined.
      ValueError: if the language identifier is not a string type.
    """
    if not isinstance(language_identifier, str):
      raise ValueError('Language identifier is not a string.')

    values = language_ids.LANGUAGE_IDENTIFIERS.get(
        language_identifier.lower(), None)
    if not values:
      raise KeyError('Language identifier: {0:s} is not defined.'.format(
          language_identifier))
    self._language_identifier = language_identifier
    self._lcid = values[0]

  def SetTimezone(self, timezone):
    """Sets the timezone.

    Args:
      timezone (str): timezone.

    Raises:
      ValueError: if the timezone is not supported.
    """
    if not timezone:
      return

    try:
      self._timezone = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
      raise ValueError('Unsupported timezone: {0:s}'.format(timezone))
