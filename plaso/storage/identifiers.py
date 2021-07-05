# -*- coding: utf-8 -*-
"""Storage attribute container identifier objects."""

from plaso.containers import interface as containers_interface


class FakeIdentifier(containers_interface.AttributeContainerIdentifier):
  """Fake attribute container identifier intended for testing.

  Attributes:
    squence_number (int): sequence number of the attribute container.
  """

  def __init__(self, squence_number):
    """Initializes a fake attribute container identifier.

    Args:
      squence_number (int): sequence number of the attribute container.
    """
    super(FakeIdentifier, self).__init__()
    self.squence_number = squence_number

  def CopyToString(self):
    """Copies the identifier to a string representation.

    Returns:
      str: unique identifier or None.
    """
    if self.squence_number is None:
      return None

    return '{0:d}'.format(self.squence_number)


class RedisKeyIdentifier(containers_interface.AttributeContainerIdentifier):
  """Redis key attribute container identifier.

  Attributes:
    name (str): name of the attribute container.
    squence_number (int): sequence number of the attribute container.
  """

  def __init__(self, name, squence_number):
    """"Initializes a Redis key identifier.

    Args:
      name (str): name of the table.
      squence_number (int): sequence number of the attribute container.
    """
    super(RedisKeyIdentifier, self).__init__()
    self.name = name
    self.squence_number = squence_number

  def CopyToString(self):
    """Copies the identifier to a string representation.

    Returns:
      str: unique identifier or None.
    """
    if self.name is not None and self.squence_number is not None:
      return '{0:s}.{1:d}'.format(self.name, self.squence_number)

    return None


class SQLTableIdentifier(containers_interface.AttributeContainerIdentifier):
  """SQL table attribute container identifier.

  The identifier is used to uniquely identify attribute containers. Where
  for example an attribute container is stored as a JSON serialized data in
  a SQLite database file.

  Attributes:
    name (str): name of the table (attribute container).
    row_identifier (int): unique identifier of the row in the table.
  """

  def __init__(self, name, row_identifier):
    """Initializes a SQL table attribute container identifier.

    Args:
      name (str): name of the table (attribute container).
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
      return '{0:s}.{1:d}'.format(self.name, self.row_identifier)

    return None
