# -*- coding: utf-8 -*-
"""The output mediator object."""

from plaso.formatters import manager as formatters_manager
from plaso.lib import eventdata

import pytz


class OutputMediator(object):
  """Class that implements the output mediator."""

  def __init__(
      self, formatter_mediator, fields_filter=None,
      preferred_encoding=u'utf-8', timezone=pytz.UTC):
    """Initializes a output mediator object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      fields_filter: optional filter object (instance of FilterObject) to
                     indicate which fields should be outputed. The default
                     is None.
      preferred_encoding: optional preferred encoding.
      timezone: optional timezone.
    """
    super(OutputMediator, self).__init__()
    self._formatter_mediator = formatter_mediator
    self._hostnames = None
    self._preferred_encoding = preferred_encoding
    self._preprocess_objects = None
    self._storage_file = None
    self._timezone = timezone

    self.fields_filter = fields_filter

  def _InitializeLookupDictionaries(self):
    """Initializes the lookup dictionaries.

    Builds a dictionary of hostnames and usernames from the preprocess
    objects stored inside the storage file.
    """
    self._hostnames = {}
    self._preprocess_objects = {}

    if (not self._storage_file or
        not hasattr(self._storage_file, u'GetStorageInformation')):
      return

    for info in self._storage_file.GetStorageInformation():
      store_range = getattr(info, u'store_range', None)
      if not store_range:
        continue

      # TODO: should this be store_range[1] + 1 with or without + 1?
      # This is inconsistent in the current version of the codebase.
      for store_number in range(store_range[0], store_range[1]):
        self._preprocess_objects[store_number] = info

        hostname = getattr(info, u'hostname', None)
        if hostname:
          # TODO: A bit wasteful, if the range is large we are wasting keys.
          # Rewrite this logic into a more optimal one.
          self._hostnames[store_number] = hostname

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
  def storage_file_path(self):
    """The storage file path."""
    return self._storage_file.file_path

  @property
  def timezone(self):
    """The timezone."""
    return self._timezone

  def GetEventFormatter(self, event_object):
    """Retrieves the event formatter for a specific event object type.

    Args:
      event_object: the event object (instance of EventObject)

    Returns:
      The event formatter object (instance of EventFormatter) or None.
    """
    data_type = getattr(event_object, u'data_type', None)
    if not data_type:
      return

    return formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)

  def GetFormattedMessages(self, event_object):
    """Retrieves the formatted messages related to the event object.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.
      If no event formatter to match the event object can be found the function
      returns a tuple of None, None.
    """
    event_formatter = self.GetEventFormatter(event_object)
    if not event_formatter:
      return None, None

    return event_formatter.GetMessages(self._formatter_mediator, event_object)

  def GetFormattedSources(self, event_object):
    """Retrieves the formatted sources related to the event object.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple of the short and long source string. If no event formatter
      to match the event object can be found the function returns a tuple
      of None, None.
    """
    event_formatter = self.GetEventFormatter(event_object)
    if not event_formatter:
      return None, None

    return event_formatter.GetSources(event_object)

  def GetFormatStringAttributeNames(self, event_object):
    """Retrieves the attribute names in the format string.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A list containing the attribute names. If no event formatter to match
      the event object can be found the function returns None.
    """
    event_formatter = self.GetEventFormatter(event_object)
    if not event_formatter:
      return

    return event_formatter.GetFormatStringAttributeNames()

  def GetHostname(self, event_object, default_hostname=u'-'):
    """Retrieves the hostname related to the event object.

    If the hostname is not stored in the event object it is determined based
    on the preprocessing information that is stored inside the storage file.

    Args:
      event_object: the event object (instance of EventObject).
      default_hostname: optional string string containing the default hostname.

    Returns:
      A string containing the hostname.
    """
    hostname = getattr(event_object, u'hostname', None)
    if hostname:
      return hostname

    store_number = getattr(event_object, u'store_number', None)
    if store_number is None:
      return default_hostname

    if self._hostnames is None:
      self._InitializeLookupDictionaries()

    return self._hostnames.get(store_number, default_hostname)

  # TODO: Fix this function when the MFT parser has been implemented.
  def GetMACBRepresentation(self, event_object):
    """Retrieves the MACB representation.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A string containing the MACB representation.
    """
    data_type = getattr(event_object, u'data_type', None)
    if not data_type:
      return u'....'

    # The filestat parser is somewhat limited.
    if data_type == u'fs:stat':
      descriptions = event_object.timestamp_desc.split(u';')

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
    if event_object.timestamp_desc in [
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
    if event_object.timestamp_desc in [
        eventdata.EventTimestamp.MODIFICATION_TIME,
        eventdata.EventTimestamp.WRITTEN_TIME,
        eventdata.EventTimestamp.DELETED_TIME]:
      return u'M...'

    # Content creation time.
    if event_object.timestamp_desc in [
        eventdata.EventTimestamp.CREATION_TIME,
        eventdata.EventTimestamp.ADDED_TIME,
        eventdata.EventTimestamp.FILE_DOWNLOADED,
        eventdata.EventTimestamp.FIRST_CONNECTED]:
      return '...B'

    # Metadata modification.
    if event_object.timestamp_desc in [
        eventdata.EventTimestamp.CHANGE_TIME,
        eventdata.EventTimestamp.ENTRY_MODIFICATION_TIME]:
      return u'..C.'

    return u'....'

  def GetStoredHostname(self):
    """Retrieves the stored hostname.

    The hostname is determined based on the preprocessing information
    that is stored inside the storage file.

    Returns:
      A string containing the hostname or None.
    """
    if self._hostnames is None:
      self._InitializeLookupDictionaries()

    store_number = len(self._hostnames)
    return self._hostnames.get(store_number, None)

  def GetUsername(self, event_object, default_username=u'-'):
    """Retrieves the username related to the event object.

    If the username in the event object is a user identifier like a SID
    or UID the identifier is resolved to a name based on the preprocessing
    information that is stored inside the storage file.

    Args:
      event_object: the event object (instance of EventObject).
      default_username: optional string string containing the default username.

    Returns:
      A string containing the username.
    """
    username = getattr(event_object, u'username', None)
    if username is None:
      return default_username

    store_number = getattr(event_object, u'store_number', None)
    if store_number is None:
      return username

    if self._preprocess_objects is None:
      self._InitializeLookupDictionaries()

    pre_obj = self._preprocess_objects.get(store_number, None)
    if not pre_obj:
      return username

    preprocess_username = pre_obj.GetUsernameById(username)
    if preprocess_username and preprocess_username != u'-':
      return preprocess_username

    user_sid = getattr(event_object, u'user_sid', None)
    if not user_sid:
      return username

    preprocess_username = pre_obj.GetUsernameById(user_sid)
    if preprocess_username and preprocess_username != u'-':
      return preprocess_username

    return username

  # TODO: refactor to use a storage reader interface.
  def SetStorageFile(self, storage_file):
    """Sets the storage file.

    Args:
      storage_file: a storage file object (instance of StorageFile).
    """
    self._storage_file = storage_file
