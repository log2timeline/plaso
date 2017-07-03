# -*- coding: utf-8 -*-
"""This file contains a parser for the Mac OS X MacKeeper cache database."""

import codecs
import json

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacKeeperCacheEventData(events.EventData):
  """MacKeeper Cache event data.

  Attributes:
    description (str): description.
    event_type (str): event type.
    record_id (int): record identifier.
    room (str): room.
    text (str): text.
    url (str): URL.
    user_name (str): user name.
    user_sid (str): user security identifier (SID).
  """
  DATA_TYPE = u'mackeeper:cache'

  def __init__(self):
    """Initializes event data."""
    super(MacKeeperCacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.description = None
    self.event_type = None
    self.record_id = None
    self.room = None
    self.text = None
    self.url = None
    self.user_name = None
    self.user_sid = None


class MacKeeperCachePlugin(interface.SQLitePlugin):
  """Plugin for the MacKeeper Cache database file."""

  NAME = u'mackeeper_cache'
  DESCRIPTION = u'Parser for MacKeeper Cache SQLite database files.'

  # Define the needed queries.
  QUERIES = [((
      u'SELECT d.entry_ID AS id, d.receiver_data AS data, r.request_key, '
      u'r.time_stamp AS time_string FROM cfurl_cache_receiver_data d, '
      u'cfurl_cache_response r WHERE r.entry_ID = '
      u'd.entry_ID'), u'ParseReceiverData')]

  # The required tables.
  REQUIRED_TABLES = frozenset([
      u'cfurl_cache_blob_data', u'cfurl_cache_receiver_data',
      u'cfurl_cache_response'])

  SCHEMAS = [{
      u'cfurl_cache_blob_data': (
          u'CREATE TABLE cfurl_cache_blob_data(entry_ID INTEGER PRIMARY KEY, '
          u'response_object BLOB, request_object BLOB, proto_props BLOB, '
          u'user_info BLOB)'),
      u'cfurl_cache_receiver_data': (
          u'CREATE TABLE cfurl_cache_receiver_data(entry_ID INTEGER PRIMARY '
          u'KEY, receiver_data BLOB)'),
      u'cfurl_cache_response': (
          u'CREATE TABLE cfurl_cache_response(entry_ID INTEGER PRIMARY KEY '
          u'AUTOINCREMENT UNIQUE, version INTEGER, hash_value INTEGER, '
          u'storage_policy INTEGER, request_key TEXT UNIQUE, time_stamp NOT '
          u'NULL DEFAULT CURRENT_TIMESTAMP, partition TEXT)'),
      u'cfurl_cache_schema_version': (
          u'CREATE TABLE cfurl_cache_schema_version(schema_version INTEGER)')}]

  def _DictToListOfStrings(self, data_dict):
    """Converts a dictionary into a list of strings.

    Args:
      data_dict (dict[str, object]): dictionary to convert.

    Returns:
      list[str]: list of strings.
    """
    ret_list = []
    for key, value in iter(data_dict.items()):
      if key in (u'body', u'datetime', u'type', u'room', u'rooms', u'id'):
        continue
      ret_list.append(u'{0:s} = {1!s}'.format(key, value))

    return ret_list

  def _ExtractJQuery(self, jquery_raw):
    """Extracts values from a JQuery string.

    Args:
      jquery_raw (str): JQuery string.

    Returns:
      dict[str, str]: extracted values.
    """
    data_part = u''
    if not jquery_raw:
      return {}

    if u'[' in jquery_raw:
      _, _, first_part = jquery_raw.partition(u'[')
      data_part, _, _ = first_part.partition(u']')
    elif jquery_raw.startswith(u'//'):
      _, _, first_part = jquery_raw.partition(u'{')
      data_part = u'{{{0:s}'.format(first_part)
    elif u'({' in jquery_raw:
      _, _, first_part = jquery_raw.partition(u'(')
      data_part, _, _ = first_part.rpartition(u')')

    if not data_part:
      return {}

    try:
      data_dict = json.loads(data_part)
    except ValueError:
      return {}

    return data_dict

  def _ParseChatData(self, data):
    """Parses chat comment data.

    Args:
      data (dict[str, object]): chat comment data as returned by SQLite.

    Returns:
      dict[str, object]: parsed chat comment data.
    """
    data_store = {}

    if u'body' in data:
      body = data.get(u'body', u'').replace(u'\n', u' ')
      if body.startswith(u'//') and u'{' in body:
        body_dict = self._ExtractJQuery(body)
        title, _, _ = body.partition(u'{')
        body = u'{0:s} <{1!s}>'.format(
            title[2:], self._DictToListOfStrings(body_dict))
    else:
      body = u'No text.'

    data_store[u'text'] = body

    room = data.get(u'rooms', None)
    if not room:
      room = data.get(u'room', None)
    if room:
      data_store[u'room'] = room

    data_store[u'id'] = data.get(u'id', None)
    user = data.get(u'user', None)
    if user:
      try:
        user_sid = int(user)
        data_store[u'sid'] = user_sid
      except (ValueError, TypeError):
        data_store[u'user'] = user

    return data_store

  def ParseReceiverData(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a single row from the receiver and cache response table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    data = {}
    key_url = row['request_key']

    data_dict = {}
    description = u'MacKeeper Entry'
    # Check the URL, since that contains vital information about the type of
    # event we are dealing with.
    if key_url.endswith(u'plist'):
      description = u'Configuration Definition'
      data[u'text'] = u'Plist content added to cache.'

    elif key_url.startswith(u'http://event.zeobit.com'):
      description = u'MacKeeper Event'
      try:
        _, _, part = key_url.partition(u'?')
        data[u'text'] = part.replace(u'&', u' ')
      except UnicodeDecodeError:
        data[u'text'] = u'N/A'

    elif key_url.startswith(u'http://account.zeobit.com'):
      description = u'Account Activity'
      _, _, activity = key_url.partition(u'#')
      if activity:
        data[u'text'] = u'Action started: {0:s}'.format(activity)
      else:
        data[u'text'] = u'Unknown activity.'

    elif key_url.startswith(u'http://support.') and u'chat' in key_url:
      description = u'Chat '
      try:
        jquery = codecs.decode(row['data'], u'utf-8')
      except UnicodeDecodeError:
        jquery = u''

      data_dict = self._ExtractJQuery(jquery)
      data = self._ParseChatData(data_dict)

      data[u'entry_type'] = data_dict.get(u'type', u'')
      if data[u'entry_type'] == u'comment':
        description += u'Comment'
      elif data[u'entry_type'] == u'outgoing':
        description += u'Outgoing Message'
      elif data[u'entry_type'] == u'incoming':
        description += u'Incoming Message'
      else:
        # Empty or not known entry type, generic status message.
        description += u'Entry'
        data[u'text'] = u';'.join(self._DictToListOfStrings(data_dict))
        if not data[u'text']:
          data[u'text'] = u'No additional data.'

    event_data = MacKeeperCacheEventData()
    event_data.description = description
    event_data.event_type = data.get(u'event_type', None)
    event_data.offset = row['id']
    event_data.query = query
    event_data.record_id = data.get(u'id', None)
    event_data.room = data.get(u'room', None)
    event_data.text = data.get(u'text', None)
    event_data.url = key_url
    event_data.user_name = data.get(u'user', None)
    event_data.user_sid = data.get(u'sid', None)

    time_value = row['time_string']
    if isinstance(time_value, py2to3.INTEGER_TYPES):
      date_time = dfdatetime_java_time.JavaTime(timestamp=time_value)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_ADDED)

    else:
      try:
        timestamp = timelib.Timestamp.FromTimeString(time_value)
      except errors.TimestampError:
        parser_mediator.ProduceExtractionError(
            u'Unable to parse time string: {0:s}'.format(time_value))
        return

      event = time_events.TimestampEvent(
          timestamp, definitions.TIME_DESCRIPTION_ADDED)

    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(MacKeeperCachePlugin)
