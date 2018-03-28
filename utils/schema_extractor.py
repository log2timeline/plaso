#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to extract the database schema from SQLite database files.

The resulting schema will be placed into your clipboard which can then
be pasted directly into your plugin.

This script requires the pyperclip Python module.
"""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import os
import sys
import textwrap

try:
  import pyperclip
except ImportError:
  paperclip = None

# Change PYTHONPATH to include plaso.
sys.path.insert(0, '.')

from plaso.parsers import sqlite  # pylint: disable=wrong-import-position


class SQLiteSchemaExtractor(object):
  """SQLite database file schema extractor."""

  def GetDatabaseSchema(self, database_path, wal_path=None):
    """Retrieves schema from given database.

    Args:
      database_path (str): file path to database.
      wal_path (Optional[str]): file path to WAL file.

    Returns:
      dict[str, str]: schema as an SQL query per table name.
    """
    database = sqlite.SQLiteDatabase('database.db')

    with open(database_path, 'rb') as file_object:
      wal_file_object = None
      if wal_path:
        wal_file_object = open(wal_path, 'rb')

      try:
        database.Open(file_object, wal_file_object=wal_file_object)
        schema = database.schema

      finally:
        database.Close()

        if wal_file_object:
          wal_file_object.close()

    return schema

  def FormatSchema(self, schema):
    """Formats a schema into a word-wrapped string.

    Args:
      schema (dict[str, str]): schema as an SQL query per table name.

    Returns:
      str: schema formatted as word-wrapped string.
    """
    textwrapper = textwrap.TextWrapper()
    textwrapper.break_long_words = False
    textwrapper.drop_whitespace = True
    textwrapper.width = 80 - (10 + 4)

    lines = []
    table_index = 1
    number_of_tables = len(schema)
    for table_name, query in sorted(schema.items()):
      line = '      \'{0:s}\': ('.format(table_name)
      lines.append(line)

      query = query.replace('\'', '\\\'')
      query = textwrapper.wrap(query)
      query = ['{0:s}\'{1:s} \''.format(' ' * 10, line) for line in query]

      if table_index == number_of_tables:
        query[-1] = '{0:s}\')}}]'.format(query[-1][:-2])
      else:
        query[-1] = '{0:s}\'),'.format(query[-1][:-2])

      lines.extend(query)
      table_index += 1

    return '\n'.join(lines)


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Extract the database schema from a SQLite database file.'))

  if paperclip:
    argument_parser.add_argument(
        '--to-clipboard', '--to_clipboard', dest='to_clipboard',
        action='store_true', default=False, help=(
            'copy the database schema to the clipboard instead of writing '
            'to stdout.'))

  argument_parser.add_argument(
      'database_path', type=str,
      help='path to the database file to extract schema from.')

  argument_parser.add_argument(
      'wal_path', type=str, nargs='?', default=None,
      help='optional path to a WAL file to commit into the database.')

  options = argument_parser.parse_args()

  if not os.path.exists(options.database_path):
    print('No such database file: {0:s}'.format(options.database_path))
    return False

  if options.wal_path and not os.path.exists(options.wal_path):
    print('No such WAL file: {0:s}'.format(options.wal_path))
    return False

  extractor = SQLiteSchemaExtractor()

  database_schema = extractor.GetDatabaseSchema(
      options.database_path, options.wal_path)

  database_schema = extractor.FormatSchema(database_schema)

  if paperclip and options.to_clipboard:
    pyperclip.copy(database_schema)
  else:
    print(database_schema)

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
