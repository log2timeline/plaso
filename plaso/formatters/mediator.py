# -*- coding: utf-8 -*-
"""The formatter mediator object."""

import os

from plaso.formatters import winevt_rc
from plaso.winnt import language_ids


class FormatterMediator(object):
  """Class that implements the formatter mediator."""

  DEFAULT_LANGUAGE_IDENTIFIER = u'en-US'
  # TODO: add smarter language ID to LCID resolving e.g.
  # 'en-US' falls back to 'en'.
  # LCID 0x0409 is en-US.
  DEFAULT_LCID = 0x0409

  _WINEVT_RC_DATABASE = u'winevt-rc.db'

  def __init__(self, data_location=None):
    """Initializes a formatter mediator object.

    Args:
      data_location: the path of the formatter data files.
                     The default is None.
    """
    super(FormatterMediator, self).__init__()
    self._data_location = data_location
    self._language_identifier = self.DEFAULT_LANGUAGE_IDENTIFIER
    self._lcid = self.DEFAULT_LCID
    self._winevt_database_reader = None

  def _GetWinevtRcDatabaseReader(self):
    """Opens the Windows Event Log resource database reader.

    Returns:
      The Windows Event Log resource database reader (instance of
      WinevtResourcesSqlite3DatabaseReader) or None.
    """
    if not self._winevt_database_reader and self._data_location:
      database_path = os.path.join(
          self._data_location, self._WINEVT_RC_DATABASE)
      if not os.path.isfile(database_path):
        return

      self._winevt_database_reader = (
          winevt_rc.WinevtResourcesSqlite3DatabaseReader())
      self._winevt_database_reader.Open(database_path)

    return self._winevt_database_reader

  @property
  def lcid(self):
    """The preferred Language Code identifier (LCID)."""
    return self._lcid

  def GetWindowsEventMessage(self, log_source, message_identifier):
    """Retrieves the message string for a specific Windows Event Log source.

    Args:
      log_source: the Event Log source.
      message_identifier: the message identifier.

    Returns:
      The message string or None if not available.
    """
    database_reader = self._GetWinevtRcDatabaseReader()
    if not database_reader:
      return

    if self._lcid != self.DEFAULT_LCID:
      message_string = database_reader.GetMessage(
          log_source, self.lcid, message_identifier)
      if message_string:
        return message_string

    return database_reader.GetMessage(
        log_source, self.DEFAULT_LCID, message_identifier)

  def SetPreferredLanguageIdentifier(self, language_identifier):
    """Sets the preferred language identifier.

    Args:
      language_identifier: the language identifier string e.g. en-US for
                           US English or is-IS for Icelandic.

    Raises:
      KeyError: if the language identifier is not defined.
      TypeError: if the language identifier is not a string type.
    """
    if not isinstance(language_identifier, basestring):
      raise ValueError(u'Language identifier is not a string.')

    values = language_ids.LANGUAGE_IDENTIFIERS.get(
        language_identifier.lower(), None)
    if not values:
      raise KeyError(u'Language identifier: {0:s} is not defined.'.format(
          language_identifier))
    self._language_identifier = language_identifier
    self._lcid = values[0]
