# -*- coding: utf-8 -*-
"""SQLite parser plugin for Health Achievements database on iOS."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSHealthAchievementsEventData(events.EventData):
  """iOS Health achievements event data.

  Attributes:
    created_date (dfdatetime.DateTimeValues): Date the achievement was created.
    creator_device (int): Identifier of the device that created the achievement.
    earned_date (dfdatetime.DateTimeValues): Date the achievement was earned.
    sync_provenance (int): Identifier for the sync provenance.
    template_unique_name (str): Unique name of the achievement template.
    value_canonical_unit (str): Unit of the value (e.g., "count").
    value_in_canonical_unit (float): Value of the achievement in canonical
        units.
  """

  DATA_TYPE = 'ios:health:achievements'

  def __init__(self):
    """Initializes event data."""
    super(IOSHealthAchievementsEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.created_date = None
    self.creator_device = None
    self.earned_date = None
    self.sync_provenance = None
    self.template_unique_name = None
    self.value_canonical_unit = None
    self.value_in_canonical_unit = None


class IOSHealthAchievementsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Health Achievements database on iOS.

  The Health Achievements data are stored in a SQLite database file named
  iOS_13_3_1_healthdb_secure.sqlite.
  """

  NAME = 'ios_health_achievements'
  DATA_FORMAT = (
      'iOS Health Achievements SQLite database file '
      'iOS_13_3_1_healthdb_secure.sqlite')

  REQUIRED_STRUCTURE = {
      'ACHAchievementsPlugin_earned_instances': frozenset([
          'template_unique_name', 'created_date', 'earned_date',
          'value_in_canonical_unit', 'value_canonical_unit', 'creator_device',
          'sync_provenance'])}

  QUERIES = [((
      'SELECT template_unique_name, created_date, earned_date, '
      'value_in_canonical_unit, value_canonical_unit, creator_device, '
      'sync_provenance FROM ACHAchievementsPlugin_earned_instances'),
      'ParseAchievementRow')]

  SCHEMAS = {
      'ACHAchievementsPlugin_earned_instances': (
          'CREATE TABLE ACHAchievementsPlugin_earned_instances ('
          'ROWID INTEGER PRIMARY KEY, template_unique_name TEXT, '
          'created_date REAL, earned_date TEXT, value_in_canonical_unit REAL, '
          'value_canonical_unit TEXT, creator_device INTEGER, '
          'sync_provenance INTEGER)')}

  REQUIRE_SCHEMA_MATCH = False

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: Date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  def ParseAchievementRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses an achievement row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = IOSHealthAchievementsEventData()
    event_data.template_unique_name = self._GetRowValue(
        query_hash, row, 'template_unique_name')
    event_data.created_date = self._GetDateTimeRowValue(
        query_hash, row, 'created_date')
    event_data.earned_date = self._GetRowValue(
        query_hash, row, 'earned_date')
    event_data.value_in_canonical_unit = self._GetRowValue(
        query_hash, row, 'value_in_canonical_unit')
    event_data.value_canonical_unit = self._GetRowValue(
        query_hash, row, 'value_canonical_unit')
    event_data.creator_device = self._GetRowValue(
        query_hash, row, 'creator_device')
    event_data.sync_provenance = self._GetRowValue(
        query_hash, row, 'sync_provenance')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(IOSHealthAchievementsPlugin)
