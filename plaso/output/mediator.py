# -*- coding: utf-8 -*-
"""The output mediator object."""

from __future__ import unicode_literals

from plaso.formatters import manager as formatters_manager
from plaso.lib import definitions

import pytz  # pylint: disable=wrong-import-order


class OutputMediator(object):
  """Output mediator.

  Attributes:
    fields_filter (FilterObject): filter object that indicates
        which fields to output.
  """

  def __init__(
      self, knowledge_base, formatter_mediator, fields_filter=None,
      preferred_encoding='utf-8'):
    """Initializes an output mediator.

    Args:
      knowledge_base (KnowledgeBase): knowledge base.
      formatter_mediator (FormatterMediator): formatter mediator.
      fields_filter (Optional[FilterObject]): filter object that indicates
          which fields to output.
      preferred_encoding (Optional[str]): preferred encoding to output.
    """
    super(OutputMediator, self).__init__()
    self._formatter_mediator = formatter_mediator
    self._knowledge_base = knowledge_base
    self._preferred_encoding = preferred_encoding
    self._timezone = pytz.UTC

    self.fields_filter = fields_filter

  @property
  def encoding(self):
    """str: preferred encoding."""
    return self._preferred_encoding

  @property
  def filter_expression(self):
    """str: filter expression if a filter is set, None otherwise."""
    if not self.fields_filter:
      return None

    return self.fields_filter.filter_expression

  @property
  def timezone(self):
    """The timezone."""
    return self._timezone

  def GetEventFormatter(self, event):
    """Retrieves the event formatter for a specific event type.

    Args:
      event (EventObject): event.

    Returns:
      EventFormatter: event formatter or None.
    """
    data_type = getattr(event, 'data_type', None)
    if not data_type:
      return None

    return formatters_manager.FormattersManager.GetFormatterObject(
        event.data_type)

  def GetFormattedMessages(self, event):
    """Retrieves the formatted messages related to the event.

    Args:
      event (EventObject): event.

    Returns:
      tuple: containing:

        str: full message string or None if no event formatter was found.
        str: short message string or None if no event formatter was found.
    """
    event_formatter = self.GetEventFormatter(event)
    if not event_formatter:
      return None, None

    return event_formatter.GetMessages(self._formatter_mediator, event)

  def GetFormattedSources(self, event, event_data):
    """Retrieves the formatted sources related to the event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

    Returns:
      tuple: containing:

        str: full source string or None if no event formatter was found.
        str: short source string or None if no event formatter was found.
    """
    event_formatter = self.GetEventFormatter(event_data)
    if not event_formatter:
      return None, None

    return event_formatter.GetSources(event, event_data)

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
