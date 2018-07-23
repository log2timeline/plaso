# -*- coding: utf-8 -*-
"""The formatter mediator object."""

from __future__ import unicode_literals

import os

from plaso.formatters import winevt_rc
from plaso.lib import py2to3
from plaso.winnt import language_ids


class FormatterMediator(object):
  """Class that implements the formatter mediator."""

  DEFAULT_LANGUAGE_IDENTIFIER = 'en-US'
  # TODO: add smarter language ID to LCID resolving e.g.
  # 'en-US' falls back to 'en'.
  # LCID 0x0409 is en-US.
  DEFAULT_LCID = 0x0409

  _WINEVT_RC_DATABASE = 'winevt-rc.db'

  def __init__(self, data_location=None):
    """Initializes a formatter mediator object.

    Args:
      data_location (str): path of the formatter data files.
    """
    super(FormatterMediator, self).__init__()
    self._data_location = data_location
    self._language_identifier = self.DEFAULT_LANGUAGE_IDENTIFIER
    self._lcid = self.DEFAULT_LCID
    self._winevt_database_reader = None

  def _GetWinevtRcDatabaseReader(self):
    """Opens the Windows Event Log resource database reader.

    Returns:
      WinevtResourcesSqlite3DatabaseReader: Windows Event Log resource
          database reader or None.
    """
    if not self._winevt_database_reader and self._data_location:
      database_path = os.path.join(
          self._data_location, self._WINEVT_RC_DATABASE)
      if not os.path.isfile(database_path):
        return None

      self._winevt_database_reader = (
          winevt_rc.WinevtResourcesSqlite3DatabaseReader())
      if not self._winevt_database_reader.Open(database_path):
        self._winevt_database_reader = None

    return self._winevt_database_reader

  @property
  def lcid(self):
    """int: preferred Language Code identifier (LCID)."""
    return self._lcid

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
          log_source, self.lcid, message_identifier)
      if message_string:
        return message_string

    return database_reader.GetMessage(
        log_source, self.DEFAULT_LCID, message_identifier)

  def SetPreferredLanguageIdentifier(self, language_identifier):
    """Sets the preferred language identifier.

    Args:
      language_identifier (str): language identifier string such as "en-US"
          for US English or "is-IS" for Icelandic.

    Raises:
      KeyError: if the language identifier is not defined.
      ValueError: if the language identifier is not a string type.
    """
    if not isinstance(language_identifier, py2to3.STRING_TYPES):
      raise ValueError('Language identifier is not a string.')

    values = language_ids.LANGUAGE_IDENTIFIERS.get(
        language_identifier.lower(), None)
    if not values:
      raise KeyError('Language identifier: {0:s} is not defined.'.format(
          language_identifier))
    self._language_identifier = language_identifier
    self._lcid = values[0]
