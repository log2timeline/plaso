# -*- coding: utf-8 -*-
"""Script to extract the database schema from SQLite database files.

The resulting schema will be placed into your clipboard which can then
be pasted directly into your plugin.

This script requires the jinja2 and pyperclip Python modules.
"""

from __future__ import print_function
import argparse
import os
import sys

import jinja2  # pylint: disable=import-error
import pyperclip  # pylint: disable=import-error

from plaso.parsers import sqlite


class SQLiteSchemaExtractor(object):
  """SQLite database file schema extractor."""

  _JINJA2_TEMPLATE = ('''
  {% for table, query in schema|dictsort %}
    {% if loop.first %}
      {u'{{ table }}':
    {% else %}
       u'{{ table }}':
    {% endif %}
       u'{{ query|wordwrap(67, wrapstring=" '\n       u'") }}'
         {%- if not loop.last -%}
          ,
         {% else -%}
          }
         {%- endif %}
  {%- endfor %}''')

  def GetDatabaseSchema(self, database_path, wal_path=None):
    """Retrieves schema from given database.

    Args:
      database_path (str): file path to database.
      wal_path (Optional[str]): file path to wal file.

    Returns:
      dict[str, str]: schema as an SQL query per table name.
    """
    database = sqlite.SQLiteDatabase('database.db')

    with open(database_path, u'rb') as file_object:
      wal_file_object = None
      if wal_path:
        wal_file_object = open(wal_path, u'rb')

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
      str: schema formated as word-wrapped string.
    """
    schema = {
        table: u' '.join(query.split()).replace(u'\'', u'\\\'')
        for table, query in schema.items()}

    environment = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
    template = environment.from_string(self._JINJA2_TEMPLATE)
    return template.render(schema=schema)


if __name__ == u'__main__':
  argument_parser = argparse.ArgumentParser()

  argument_parser.add_argument(
      u'database_path', type=str,
      help=u'The path to the database file to extract schema from.')

  argument_parser.add_argument(
      u'wal_path', type=str, nargs=u'?', default=None,
      help=u'Optional path to a wal file to commit into the database.')

  options = argument_parser.parse_args()

  if not os.path.exists(options.database_path):
    print(u'No such database file: {0:s}'.format(options.database_path))
    sys.exit(1)

  if not os.path.exists(options.wal_path):
    print(u'No such wal file: {0:s}'.format(options.wal_path))
    sys.exit(1)

  extractor = SQLiteSchemaExtractor()

  database_schema = extractor.GetDatabaseSchema(
      options.database_path, options.wal_path)

  database_schema = extractor.FormatSchema(database_schema)

  pyperclip.copy(database_schema)

  sys.exit(0)
