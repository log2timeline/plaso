# -*- coding: utf-8 -*-
"""Fake implementation of MySQLdb module for testing."""


class Error(object):
  """Fake implementation of MySQLdb Error class for testing."""


class FakeMySQLdbConnection(object):
  """Fake implementation of MySQLdb Connection class for testing."""

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

  def set_character_set(self, unused_character_set):
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

  def close(self):
    """Closes the cursor."""
    return

  def execute(self, query, args=None):
    """Executes the query.

    Args:
      query (str): SQL query.
      args (Optional[object]): sequence or mapping of the parameters to use
          with the query.

    Returns:
      int: number of rows affected by the query.

    Raises:
      ValueError: if the query or query arguments do not match the expected
          values.
    """
    if self.expected_query is not None and self.expected_query != query:
      raise ValueError(u'Query mismatch.')

    if (self.expected_query_args is not None and
        self.expected_query_args != args):
      raise ValueError(u'Query arguments mismatch.')

    self._result_index = 0

  def fetchone(self):
    """Fetches a single row of the results returned by execute.

    Returns:
      object: row or None.
    """
    if (not self.query_results or self._result_index < 0 or
        self._result_index >= len(self.query_results)):
      return

    row = self.query_results[self._result_index]
    self._result_index += 1
    return row


def connect(
    unused_hostname, unused_username, unused_password, unused_database_name):
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
