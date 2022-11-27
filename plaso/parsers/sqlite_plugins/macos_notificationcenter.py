# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS Notification Center database files."""

import plistlib

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacOSNotificationCenterEventData(events.EventData):
  """MacOS NotificationCenter event data.

  Attributes:
    body (str): body of the notification message.
    bundle_name (str): name of the application's bundle that generated
        the notification.
    creation_time (dfdatetime.DateTimeValues): date and time the entry was
        created.
    presented (int): either 1 or 0 if the notification has been shown to the
        user.
    subtitle (str): optional. Subtitle of the notification message.
    title (str): title of the message. Usually the name of the application
        that generated the notification. Occasionally the name of the sender
        of the notification for example, in case of chat messages.
  """

  DATA_TYPE = 'macos:notification_center:entry'

  def __init__(self):
    """Initialize event data."""
    super(MacOSNotificationCenterEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.body = None
    self.bundle_name = None
    self.creation_time = None
    self.presented = None
    self.subtitle = None
    self.title = None


class MacOSNotificationCenterPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for MacOS Notification Center database files.

  The MacOS Notification Center database file is typically stored in:
  /private/var/folders/<W><d>/../0/com.apple.notificationcenter/db2/db

  At the moment it takes into consideration only the main table, 'record'.
  Currently supported tables and related content:
    Record: contains historical records
    Requests: contain pending requests
    Delivered: delivered requests
    Displayed: displayed requests, by app_id
    Snoozed: snoozed by user requests
  """

  NAME = 'mac_notificationcenter'
  DATA_FORMAT = 'MacOS Notification Center SQLite database file'

  REQUIRED_STRUCTURE = {
      'app': frozenset([
          'identifier', 'app_id']),
      'record': frozenset([
          'data', 'delivered_date', 'presented', 'app_id'])}

  QUERIES = [
      ('SELECT a.identifier AS bundle_name, '
       'r.data AS dataBlob, r.delivered_date AS timestamp,'
       'r.presented AS presented '
       'FROM app a, record r '
       'WHERE a.app_id = r.app_id', 'ParseNotificationcenterRow')]

  SCHEMAS = [{
      'app': (
          'CREATE TABLE app (app_id INTEGER PRIMARY KEY, identifier VARCHAR)'),
      'dbinfo': (
          'CREATE TABLE dbinfo (key VARCHAR, value VARCHAR)'),
      'delivered': (
          'CREATE TABLE delivered (app_id INTEGER PRIMARY KEY, list BLOB)'),
      'displayed': (
          'CREATE TABLE displayed (app_id INTEGER PRIMARY KEY, list BLOB)'),
      'record': (
          'CREATE TABLE record (rec_id INTEGER PRIMARY KEY, app_id INTEGER, '
          'uuid BLOB, data BLOB, request_date REAL, request_last_date REAL, '
          'delivered_date REAL, presented Bool, style INTEGER, '
          'snooze_fire_date REAL)'),
      'requests': (
          'CREATE TABLE requests (app_id INTEGER PRIMARY KEY, list BLOB)'),
      'snoozed': (
          'CREATE TABLE snoozed (app_id INTEGER PRIMARY KEY, list BLOB)')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  def ParseNotificationcenterRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    data_blob = self._GetRowValue(query_hash, row, 'dataBlob')

    try:
      property_list = plistlib.loads(data_blob)
      # req_property is the 'req' dictionary from the plist containing extra
      # information about the notification entry.
      req_property = property_list['req']

    except (KeyError, plistlib.InvalidFileException) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to read plist from database with error: {0!s}'.format(
              exception))
      req_property = {}

    event_data = MacOSNotificationCenterEventData()
    event_data.body = req_property.get('body', None)
    event_data.bundle_name = self._GetRowValue(query_hash, row, 'bundle_name')
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'timestamp')
    event_data.presented = self._GetRowValue(query_hash, row, 'presented')
    event_data.subtitle = req_property.get('subt', None)
    event_data.title = req_property.get('titl', None)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(MacOSNotificationCenterPlugin)
