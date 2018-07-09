# -*- coding: utf-8 -*-
"""This file contains a parser for the Notification Center database on MacOS.

Notification Center events on MacOS are stored in a
SQLite database file named "db", path is usually something like
/private/var/folders/<W><d>/../0/com.apple.notificationcenter/db2/

At the moment it takes into consideration only the main table, 'record'.
Documentation of the behavior of each table still work in progress,
current tables and supposed related content is the following:
    Record: contains Historical Records
    Requests: contain pending requests
    Delivered: delivered requests
    Displayed: Displayed requests, by app_id
    Snoozed: Snoozed by user requests
"""

from __future__ import unicode_literals

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface
from biplist import *


class MacNotificationCenterEventData(events.EventData):
  """ MacOS NotificationCenter database event data

  Attributes:
    bundle_name (str): name of the application's bundle that generated the notification
    identity (str):
    message (str):
    presented (int): either 1 or 0 if the notification has been shown to the user.
                      Research on the full meaning of this still ongoing
    subtitle (str):
    title (str):
  """

  DATA_TYPE = 'mac:notificationcenter:db'

  def __init__(self):
    """Initialize event data."""
    super(MacNotificationCenterEventData, self).__init__(data_type=self.DATA_TYPE)
    self.bundle_name = None
    self.identity = None
    self.message = None
    self.presented = None
    self.subtitle = None
    self.title = None


class MacNotificationCenterPlugin(interface.SQLitePlugin):
  """Parse the MacOS Notification Center SQLite database"""

  NAME = 'mac_notificationcenter'
  DESCRIPTION = 'Parser for the Notification Center SQLite database'

  QUERIES = [('SELECT a.identifier AS bundle_name, '
              'r.data AS dataBlob, r.delivered_date AS timestamp,'
              'r.presented AS presented '
              'FROM app a, record r '
              'WHERE a.app_id = r.app_id', 'ParseNotificationcenterRow')]

  REQUIRED_TABLES = frozenset(['app', 'record'])

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

  def ParseNotificationcenterRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = MacNotificationCenterEventData()
    event_data.bundle_name = self._GetRowValue(query_hash, row, 'bundle_name')
    event_data.presented = self._GetRowValue(query_hash, row, 'presented')

    # full_biplist is the entire blob content as stored in the sqlite record
    full_biplist = readPlistFromString(self._GetRowValue(query_hash, row, 'dataBlob'))
    # plist is the subsection 'req' containing the extra info about the notification entry
    plist = full_biplist['req']

    event_data.title = plist['titl']
    if 'subt' in plist.keys():
      event_data.subtitle = plist['subt']

    event_data.message = plist['body']
    if 'iden' in plist.keys():
      event_data.identity = plist['iden']

    timestamp = self._GetRowValue(query_hash, row, 'timestamp')
    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

sqlite.SQLiteParser.RegisterPlugin(MacNotificationCenterPlugin)