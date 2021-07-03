# -*- coding: utf-8 -*-
"""Storage attribute container identifier objects."""

import uuid

from plaso.containers import interface as containers_interface


class FakeIdentifier(containers_interface.AttributeContainerIdentifier):
  """Fake attribute container identifier intended for testing.

  Attributes:
    identifier (int): sequence number of the attribute container.
  """

  def __init__(self, identifier):
    """Initializes a fake attribute container identifier.

    Args:
      identifier (int): sequence number of the attribute container.
    """
    super(FakeIdentifier, self).__init__()
    self.identifier = identifier

  def CopyToString(self):
    """Copies the identifier to a string representation.

    Returns:
      str: unique identifier or None.
    """
    if self.identifier is None:
      return None

    return '{0:d}'.format(self.identifier)


class RedisKeyIdentifier(containers_interface.AttributeContainerIdentifier):
  """Redis key attribute container identifier.

  The identifier is used to uniquely identify attribute containers. Where
  for example an attribute container is stored as a JSON serialized data in
  a Redis instance.

  Attributes:
    identifier (UUID): unique identifier of a container.
  """

  def __init__(self, identifier=None):
    """"Initializes a Redis key identifier.

    Args:
      identifier (Optional[str]): hexadecimal representation of a UUID
          (version 4). If not specified, a random UUID (version 4) will be
          generated.
    """
    super(RedisKeyIdentifier, self).__init__()
    if identifier:
      self.identifier = uuid.UUID(identifier)
    else:
      self.identifier = uuid.uuid4()

  def CopyToString(self):
    """Copies the identifier to a string representation.

    Returns:
      str: unique identifier or None.
    """
    if not self.identifier:
      return None

    return self.identifier.hex


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
      return '{0:s}.{1:d}'.format(self.name, self.row_identifier)

    return None
