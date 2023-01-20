# -*- coding: utf-8 -*-
"""SQLite Result Codes helper.

For a list of result codes see:
  https://www.sqlite.org/rescode.html
"""


class SQLiteResultCodeHelper(object):
  """SQLite result codes helper."""

  _SQLITE_CODES = {
      0: 'SQLITE_OK',
      1: 'SQLITE_ERROR',
      2: 'SQLITE_INTERNAL',
      3: 'SQLITE_PERM',
      4: 'SQLITE_ABORT',
      5: 'SQLITE_BUSY',
      6: 'SQLITE_LOCKED',
      7: 'SQLITE_NOMEM',
      8: 'SQLITE_READONLY',
      9: 'SQLITE_INTERRUPT',
      10: 'SQLITE_IOERR',
      11: 'SQLITE_CORRUPT',
      12: 'SQLITE_NOTFOUND',
      13: 'SQLITE_FULL',
      14: 'SQLITE_CANTOPEN',
      15: 'SQLITE_PROTOCOL',
      16: 'SQLITE_EMPTY',
      17: 'SQLITE_SCHEMA',
      18: 'SQLITE_TOOBIG',
      19: 'SQLITE_CONSTRAINT',
      20: 'SQLITE_MISMATCH',
      21: 'SQLITE_MISUSE',
      22: 'SQLITE_NOLFS',
      23: 'SQLITE_AUTH',
      24: 'SQLITE_FORMAT',
      25: 'SQLITE_RANGE',
      26: 'SQLITE_NOTADB',
      27: 'SQLITE_NOTICE',
      28: 'SQLITE_WARNING',
      100: 'SQLITE_ROW',
      101: 'SQLITE_DONE',
      266: 'SQLITE IO ERR READ'}

  @classmethod
  def GetResult(cls, code):
    """Retrieves the description for a specific error code.

    Args:
      code (int): error code

    Returns:
      str: name of the error code or None if not available.
    """
    return cls._SQLITE_CODES.get(code, None)
