# -*- coding: utf-8 -*-
"""The output mediator object."""

import logging

from plaso.formatters import manager as formatters_manager
from plaso.lib import errors

import pytz


class OutputMediator(object):
  """Class that implements the output mediator."""

  def __init__(
      self, formatter_mediator, storage_object, config=None,
      fields_filter=None):
    """Initializes a output mediator object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      storage_object: a storage file object (instance of StorageFile)
                      that defines the storage.
      config: optional configuration object, containing config information.
              The default is None.
      fields_filter: optional filter object (instance of FilterObject) to
                     indicate which fields should be outputed. The default
                     is None.
    """
    super(OutputMediator, self).__init__()
    self._config = config
    self._formatter_mediator = formatter_mediator
    self._hostnames = None
    self._preprocess_objects = None
    self._storage_object = storage_object
    self._timezone = None

    self.fields_filter = fields_filter

  def _InitializeLookupDictionaries(self):
    """Initializes the lookup dictionaries.

    Builds a dictionary of hostnames and usernames from the preprocess
    objects stored inside the storage file.
    """
    self._hostnames = {}
    self._preprocess_objects = {}

    if (not self._storage_object or
        not hasattr(self._storage_object, u'GetStorageInformation')):
      return

    for info in self._storage_object.GetStorageInformation():
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
    return getattr(self._config, u'preferred_encoding', u'utf-8')

  @property
  def timezone(self):
    """The timezone."""
    if not self._timezone:
      timezone_string = getattr(self._config, u'timezone', u'UTC')

      try:
        self._timezone = pytz.timezone(timezone_string)

      except pytz.UnknownTimeZoneError:
        logging.warning(
            u'Unsupported timezone: {0:s} defaulting to: UTC'.format(
                timezone_string))
        self._timezone = pytz.UTC

    return self._timezone

  # TODO: solve this differently in a future refactor.
  def GetConfigurationValue(self, identifier, default_value=None):
    """Retrieves a configuration value.

    Args:
      identifier: the identifier of the configuration value.
      default_value: optional value containing the default.
                     The default is None.

    Returns:
      The configuration value or None if not set.
    """
    return getattr(self._config, identifier, default_value)

  def GetEventFormatter(self, event_object):
    """Retrieves the event formatter for a specific event object type.

    Args:
      event_object: the event object (instance of EventObject)

    Returns:
      The event formatter object (instance of EventFormatter).

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    # TODO: do not raise NoFormatterFound, discuss alternative.
    data_type = getattr(event_object, u'data_type', None)
    if not data_type:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter data type is missing from event '
          u'object.')

    event_formatter = formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(
              event_object.data_type))

    return event_formatter

  def GetFormattedMessages(self, event_object):
    """Retrieves the formatted messages related to the event object.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    event_formatter = self.GetEventFormatter(event_object)
    return event_formatter.GetMessages(self._formatter_mediator, event_object)

  def GetFormattedSources(self, event_object):
    """Retrieves the formatted sources related to the event object.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple of the short and long source string.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    event_formatter = self.GetEventFormatter(event_object)
    return event_formatter.GetSources(event_object)

  def GetFormatStringAttributeNames(self, event_object):
    """Retrieves the attribute names in the format string.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A list containing the attribute names.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    event_formatter = self.GetEventFormatter(event_object)
    return event_formatter.GetFormatStringAttributeNames()

  def GetHostname(self, event_object, default_hostname=u'-'):
    """Retrieves the hostname related to the event object.

    If the hostname is not stored in the event object it is determined based
    on the preprocessing information that is stored inside the storage file.

    Args:
      event_object: the event object (instance of EventObject).
      default_hostname: optional string string containing the default hostname.
                        The default is '-'.

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
                        The default is '-'.

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
