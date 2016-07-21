# -*- coding: utf-8 -*-
"""The output mediator object."""

from plaso.formatters import manager as formatters_manager
from plaso.lib import eventdata

import pytz  # pylint: disable=wrong-import-order


class OutputMediator(object):
  """Class that implements the output mediator.

  Attributes:
    fields_filter (FilterObject): filter object that indicates
                                  which fields to output.
  """

  def __init__(
      self, knowledge_base, formatter_mediator, fields_filter=None,
      preferred_encoding=u'utf-8'):
    """Initializes a output mediator object.

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
    """The preferred encoding."""
    return self._preferred_encoding

  @property
  def filter_expression(self):
    """The filter expression if a filter is set, None otherwise."""
    if not self.fields_filter:
      return

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
      The event formatter object (instance of EventFormatter) or None.
    """
    data_type = getattr(event, u'data_type', None)
    if not data_type:
      return

    return formatters_manager.FormattersManager.GetFormatterObject(
        event.data_type)

  def GetFormattedMessages(self, event):
    """Retrieves the formatted messages related to the event.

    Args:
      event (EventObject): event.

    Returns:
      A tuple containing the formatted message string and short message string.
      If no event formatter to match the event can be found the function
      returns a tuple of None, None.
    """
    event_formatter = self.GetEventFormatter(event)
    if not event_formatter:
      return None, None

    return event_formatter.GetMessages(self._formatter_mediator, event)

  def GetFormattedSources(self, event):
    """Retrieves the formatted sources related to the event.

    Args:
      event (EventObject): event.

    Returns:
      A tuple of the short and long source string. If no event formatter
      to match the event can be found the function returns a tuple
      of None, None.
    """
    event_formatter = self.GetEventFormatter(event)
    if not event_formatter:
      return None, None

    return event_formatter.GetSources(event)

  def GetFormatStringAttributeNames(self, event):
    """Retrieves the attribute names in the format string.

    Args:
      event (EventObject): event.

    Returns:
      A list containing the attribute names. If no event formatter to match
      the event can be found the function returns None.
    """
    event_formatter = self.GetEventFormatter(event)
    if not event_formatter:
      return

    return event_formatter.GetFormatStringAttributeNames()

  def GetHostname(self, event, default_hostname=u'-'):
    """Retrieves the hostname related to the event.

    Args:
      event (EventObject): event.
      default_hostname (Optional[str]): default hostname.

    Returns:
      str: hostname.
    """
    hostname = getattr(event, u'hostname', None)
    if hostname:
      return hostname

    # TODO: remove the need to pass store number.
    store_number = getattr(event, u'store_number', None)
    if store_number is None:
      return default_hostname

    return self._knowledge_base.GetHostname(
        store_number, default_hostname=default_hostname)

  # TODO: Fix this function when the MFT parser has been implemented.
  def GetMACBRepresentation(self, event):
    """Retrieves the MACB representation.

    Args:
      event (EventObject): event.

    Returns:
      str: MACB representation.
    """
    data_type = getattr(event, u'data_type', None)
    if not data_type:
      return u'....'

    # The filestat parser is somewhat limited.
    if data_type == u'fs:stat':
      descriptions = event.timestamp_desc.split(u';')

      return_characters = [u'.', u'.', u'.', u'.']
      for description in descriptions:
        if description == u'mtime':
          return_characters[0] = u'M'
        elif description == u'atime':
          return_characters[1] = u'A'
        elif description == u'ctime':
          return_characters[2] = u'C'
        elif description == u'crtime':
          return_characters[3] = u'B'

      return u''.join(return_characters)

    # Access time.
    if event.timestamp_desc in [
        eventdata.EventTimestamp.ACCESS_TIME,
        eventdata.EventTimestamp.ACCOUNT_CREATED,
        eventdata.EventTimestamp.PAGE_VISITED,
        eventdata.EventTimestamp.LAST_VISITED_TIME,
        eventdata.EventTimestamp.START_TIME,
        eventdata.EventTimestamp.LAST_SHUTDOWN,
        eventdata.EventTimestamp.LAST_LOGIN_TIME,
        eventdata.EventTimestamp.LAST_PASSWORD_RESET,
        eventdata.EventTimestamp.LAST_CONNECTED,
        eventdata.EventTimestamp.LAST_RUNTIME,
        eventdata.EventTimestamp.LAST_PRINTED]:
      return u'.A..'

    # Content modification.
    if event.timestamp_desc in [
        eventdata.EventTimestamp.MODIFICATION_TIME,
        eventdata.EventTimestamp.WRITTEN_TIME,
        eventdata.EventTimestamp.DELETED_TIME]:
      return u'M...'

    # Content creation time.
    if event.timestamp_desc in [
        eventdata.EventTimestamp.CREATION_TIME,
        eventdata.EventTimestamp.ADDED_TIME,
        eventdata.EventTimestamp.FILE_DOWNLOADED,
        eventdata.EventTimestamp.FIRST_CONNECTED]:
      return '...B'

    # Metadata modification.
    if event.timestamp_desc in [
        eventdata.EventTimestamp.CHANGE_TIME,
        eventdata.EventTimestamp.ENTRY_MODIFICATION_TIME]:
      return u'..C.'

    return u'....'

  # TODO: remove this function it is incorrect.
  def GetStoredHostname(self):
    """Retrieves the stored hostname.

    Returns:
      str: hostname.
    """
    return self._knowledge_base.GetStoredHostname()

  def GetUsername(self, event, default_username=u'-'):
    """Retrieves the username related to the event.

    Args:
      event (EventObject): event.
      default_username (Optional[str]): default username.

    Returns:
      str: username.
    """
    username = getattr(event, u'username', None)
    if username and username != u'-':
      return username

    # TODO: remove the need to pass store number.
    user_sid = getattr(event, u'user_sid', None)
    store_number = getattr(event, u'store_number', None)
    return self._knowledge_base.GetUsername(
        user_sid, store_number, default_username=default_username)

  def SetTimezone(self, timezone):
    """Sets the timezone.

    Args:
      timezone (str): timezone.

    Raises:
      ValueError: if the timezone is not supported.
    """
    try:
      self._timezone = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
      raise ValueError(u'Unsupported timezone: {0:s}'.format(timezone))
