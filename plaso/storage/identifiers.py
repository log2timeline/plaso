# -*- coding: utf-8 -*-
"""Storage attribute container identifier objects."""

from plaso.containers import interface as containers_interface


class SerializedStreamIdentifier(
    containers_interface.AttributeContainerIdentifier):
  """Serialized stream attribute container identifier.

  The identifier is used to uniquely identify attribute containers. Where
  for example an attribute container is stored as a JSON serialized data in
  a ZIP file.

  Attributes:
    stream_number (int): number of the serialized attribute container stream.
    entry_index (int): number of the serialized event within the stream.
  """

  def __init__(self, stream_number, entry_index):
    """Initializes a serialized stream attribute container identifier.

    Args:
      stream_number (int): number of the serialized attribute container stream.
      entry_index (int): number of the serialized event within the stream.
    """
    super(SerializedStreamIdentifier, self).__init__()
    self.entry_index = entry_index
    self.stream_number = stream_number

  def CopyToString(self):
    """Copies the identifier to a string representation.

    Returns:
      str: unique identifier or None.
    """
    if self.stream_number is not None and self.entry_index is not None:
      return u'{0:d}.{1:d}'.format(self.stream_number, self.entry_index)


class SQLTableIdentifier(containers_interface.AttributeContainerIdentifier):
  """SQL table attribute container identifier.

  The identifier is used to uniquely identify attribute containers. Where
  for example an attribute container is stored as a JSON serialized data in
  a SQLite database file.

  Attributes:
    name (str): name of the table.
    row_identifier (int): unique identifier of the row in the table.
  """

  def __init__(self, name, row_identifier):
    """Initializes a SQL table attribute container identifier.

    Args:
      name (str): name of the table.
      row_identifier (int): unique identifier of the row in the table.
    """
    super(SQLTableIdentifier, self).__init__()
    self.name = name
    self.row_identifier = row_identifier

  def CopyToString(self):
    """Copies the identifier to a string representation.

    Returns:
      str: unique identifier or None.
    """
    if self.name is not None and self.row_identifier is not None:
      return u'{0:s}.{1:d}'.format(self.name, self.row_identifier)
