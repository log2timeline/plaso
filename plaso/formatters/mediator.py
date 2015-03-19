# -*- coding: utf-8 -*-
"""The formatter mediator object."""

import os

from plaso.formatters import winevt_rc


class FormatterMediator(object):
  """Class that implements the formatter mediator."""

  # LCID defaults to us-EN.
  DEFAULT_LCID = 0x00000409

  _WINEVT_RC_DATABASE = u'winevt-rc.db'

  def __init__(self, data_location=None):
    """Initializes a formatter mediator object.

    Args:
      data_location: the path of the formatter data files.
                     The default is None.
    """
    super(FormatterMediator, self).__init__()
    self._data_location = data_location
    # TODO: add means to set the preferred LCID.
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
