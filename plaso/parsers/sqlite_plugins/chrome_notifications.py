# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google Chrome notifications database files."""

import json

from dfdatetime import webkit_time as dfdatetime_webkit_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ChromeNotificationEventData(events.EventData):
  """Chrome notification event data.

  Attributes:
    badge (str): badge URL from the notification data.
    body (str): body text of the notification.
    icon (str): icon URL from the notification data.
    notification_id (str): unique identifier for the notification.
    origin (str): URL origin that created the notification.
    query (str): SQL query that was used to obtain the event data.
    replaced_time (dfdatetime.DateTimeValues): date and time the notification
        was replaced.
    service_worker_registration_id (int): service worker registration
        identifier.
    time (dfdatetime.DateTimeValues): date and time the notification was
        created.
    title (str): title of the notification.
  """

  DATA_TYPE = 'chrome:notification:entry'

  def __init__(self):
    """Initializes event data."""
    super(ChromeNotificationEventData, self).__init__(data_type=self.DATA_TYPE)
    self.badge = None
    self.body = None
    self.icon = None
    self.notification_id = None
    self.origin = None
    self.query = None
    self.replaced_time = None
    self.service_worker_registration_id = None
    self.time = None
    self.title = None


class ChromeNotificationsPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Google Chrome notifications database files.

  The Google Chrome notifications database file is typically stored in:
  Notifications
  """

  NAME = 'chrome_notifications'
  DATA_FORMAT = 'Google Chrome notifications SQLite database file'

  REQUIRED_STRUCTURE = {
      'notifications': frozenset([
          'notification_id', 'origin', 'service_worker_registration_id',
          'time', 'data'])}

  QUERIES = [
      (('SELECT notification_id, origin, service_worker_registration_id, '
        'replaced_time, time, data, shown_notification_data '
        'FROM notifications'),
       'ParseNotificationRow')]

  SCHEMAS = [{
      'notifications': (
          'CREATE TABLE notifications (notification_id TEXT NOT NULL, '
          'origin TEXT NOT NULL, service_worker_registration_id INTEGER NOT '
          'NULL, replaced_time INTEGER, time INTEGER NOT NULL, data BLOB NOT '
          'NULL, shown_notification_data BLOB, PRIMARY KEY (notification_id, '
          'origin, service_worker_registration_id))')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

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

  def ParseNotificationRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a notification row.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from the query.
    """
    query_hash = hash(query)

    # Parse the data BLOB which contains JSON notification data
    data_blob = self._GetRowValue(query_hash, row, 'data')
    notification_data = {}

    if data_blob:
      try:
        # Try to parse as JSON
        if isinstance(data_blob, bytes):
          data_blob = data_blob.decode('utf-8')
        notification_data = json.loads(data_blob)
      except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse notification data with error: {0!s}'.format(
                exception))

    # Try to also parse shown_notification_data if data parsing failed
    if not notification_data:
      shown_data_blob = self._GetRowValue(
          query_hash, row, 'shown_notification_data')
      if shown_data_blob:
        try:
          if isinstance(shown_data_blob, bytes):
            shown_data_blob = shown_data_blob.decode('utf-8')
          notification_data = json.loads(shown_data_blob)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
          pass

    event_data = ChromeNotificationEventData()
    event_data.badge = notification_data.get('badge', None)
    event_data.body = notification_data.get('body', None)
    event_data.icon = notification_data.get('icon', None)
    event_data.notification_id = self._GetRowValue(
        query_hash, row, 'notification_id')
    event_data.origin = self._GetRowValue(query_hash, row, 'origin')
    event_data.query = query
    event_data.replaced_time = self._GetDateTimeRowValue(
        query_hash, row, 'replaced_time')
    event_data.service_worker_registration_id = self._GetRowValue(
        query_hash, row, 'service_worker_registration_id')
    event_data.time = self._GetDateTimeRowValue(query_hash, row, 'time')
    event_data.title = notification_data.get('title', None)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(ChromeNotificationsPlugin)
