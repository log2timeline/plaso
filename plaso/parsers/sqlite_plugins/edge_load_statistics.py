# -*- coding: utf-8 -*-
"""Parser for Microsoft Edge load statistics database."""

from dfdatetime import webkit_time as dfdatetime_webkit_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class EdgeLoadStatisticsResourceEventData(events.EventData):
  """Microsoft Edge load statistics resource event data.

  Attributes:
    last_update: Last update time of resource, cached or not.
    query (str): query that created the event data.
    resource_hostname: External domain of the resource that was loaded
    resource_type: Integer descriptor of resource type
    top_level_hostname: Source domain that initiated resource load
  """

  DATA_TYPE = 'edge:resources:load_statistics'

  def __init__(self):
    """Initializes event data."""
    super(EdgeLoadStatisticsResourceEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.last_update = None
    self.query = None
    self.resource_hostname = None
    self.resource_type = None
    self.top_level_hostname = None


class EdgeLoadStatisticsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Microsoft Edge load statistics database."""

  NAME = 'edge_load_statistics'
  DESCRIPTION = 'Parser for Microsoft Edge load_statistics.db'

  QUERIES = [
      ('SELECT top_level_hostname, resource_hostname, resource_type, '
       'last_update FROM load_statistics', 'ParseResourceRow')]

  REQUIRED_STRUCTURE = {
      'load_statistics': frozenset([
          'top_level_hostname', 'resource_hostname', 'resource_url_hash', 
          'resource_type', 'last_update']),
      'meta':frozenset([
          'key','value']),
      'redirect_statistics':frozenset([
          'source_hostname','destination_hostname',
          'is_top_level_document','last_update'])}

  SCHEMAS = [{
     'load_statistics': (
          'CREATE TABLE load_statistics(top_level_hostname TEXT,'
          'resource_hostname TEXT, resource_url_hash TEXT, resource_type'
          'INTEGER, last_update INTEGER NOT NULL,'
          'UNIQUE(top_level_hostname,resource_url_hash))'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY,'
          'value LONGVARCHAR)'),
      'redirect_statistics': (
          'CREATE TABLE redirect_statistics(source_hostname TEXT,'
          'destination_hostname TEXT, is_top_level_document INTEGER NOT'
          'NULL, last_update INTEGER NOT NULL, UNIQUE(source_hostname,desti'
          'nation_hostname,is_top_level_document))')}]

  def _GetWebKitDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a WebKit date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.WebKitTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)

  def ParseResourceRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".
    query_hash = hash(query)

    event_data = EdgeLoadStatisticsResourceEventData()
    event_data.last_update = self._GetWebKitDateTimeRowValue(
        query_hash, row, 'last_update')
    event_data.query = query
    event_data.resource_hostname = self._GetRowValue(
        query_hash, row, 'resource_hostname')
    event_data.resource_type = self._GetRowValue(
        query_hash, row, 'resource_type')
    event_data.top_level_hostname = self._GetRowValue(
        query_hash, row, 'top_level_hostname')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(EdgeLoadStatisticsPlugin)
