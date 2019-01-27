# -*- coding: utf-8 -*-
"""Fake implementation of MySQLdb module for testing."""

from __future__ import unicode_literals


class Error(object):
  """Fake implementation of MySQLdb Error class for testing."""


class FakeMySQLdbConnection(object):
  """Fake implementation of MySQLdb Connection class for testing."""

  # Note: that the following functions do not follow the style guide
  # because they are part of the MySQL database connection interface.
  # pylint: disable=invalid-name

  def close(self):
    """Closes the connection."""
    return

  def commit(self):
    """Commits changes to the database."""
    return

  def cursor(self):
    """Retrieves a database cursor.

    Returns:
      FakeMySQLCursor: cursor.
    """
    return FakeMySQLdbCursor()

  # pylint: disable=unused-argument
  def set_character_set(self, character_set):
    """Sets the character set.

    Args:
      character_set (str): character set.
    """
    return


class FakeMySQLdbCursor(object):
  """Fake implementation of MySQLdb Cursor class for testing.

  Attributes:
    expected_query (str): query expected to be passed to the execute method.
    query_results (list[object]): rows to return as results of the query.
  """

  def __init__(self):
    """Initializes the cursor."""
    super(FakeMySQLdbCursor, self).__init__()
    self._result_index = 0
    self.expected_query = None
    self.expected_query_args = None
    self.query_results = []

  # Note: that the following functions do not follow the style guide
  # because they are part of the MySQL database cursor interface.
  # pylint: disable=invalid-name

  def close(self):
    """Closes the cursor."""
    return

  def execute(self, query, args=None):
    """Executes the query.

    Args:
      query (str): SQL query.
      args (Optional[object]): sequence or mapping of the parameters to use
          with the query.

    Raises:
      ValueError: if the query or query arguments do not match the expected
          values.
    """
    if self.expected_query is not None and self.expected_query != query:
      raise ValueError('Query mismatch.')

    if (self.expected_query_args is not None and
        self.expected_query_args != args):
      raise ValueError('Query arguments mismatch.')

    self._result_index = 0

  def fetchone(self):
    """Fetches a single row of the results returned by execute.

    Returns:
      object: row or None.
    """
    if (not self.query_results or self._result_index < 0 or
        self._result_index >= len(self.query_results)):
      return None

    row = self.query_results[self._result_index]
    self._result_index += 1
    return row


# Note: that the following function does not follow the style guide
# because they are part of the MySQL database module interface.
# pylint: disable=invalid-name,unused-argument
def connect(hostname, username, password, database_name):
  """Connects to the MySQL database server.

  Args:
    hostname (str): hostname of the server.
    username (str): username to use to connect to the server.
    password (str): password to use to connect to the server.
    database_name (str): name of the database on the server.

  Returns:
    FakeMySQLdbConnection: connection
  """
  return FakeMySQLdbConnection()
