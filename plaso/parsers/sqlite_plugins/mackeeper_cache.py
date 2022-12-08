# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS MacKeeper cache database files."""

import codecs
import json

from dfdatetime import java_time as dfdatetime_java_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class MacKeeperCacheEventData(events.EventData):
  """MacKeeper Cache event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the cache entry was
        added.
    description (str): description.
    event_type (str): event type.
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    record_id (int): record identifier.
    room (str): room.
    text (str): text.
    url (str): URL.
    user_name (str): user name.
    user_sid (str): user security identifier (SID).
  """

  DATA_TYPE = 'mackeeper:cache'

  def __init__(self):
    """Initializes event data."""
    super(MacKeeperCacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.description = None
    self.event_type = None
    self.offset = None
    self.query = None
    self.record_id = None
    self.room = None
    self.text = None
    self.url = None
    self.user_name = None
    self.user_sid = None


class MacKeeperCachePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for MacOS MacKeeper cache database files."""

  NAME = 'mackeeper_cache'
  DATA_FORMAT = 'MacOS MacKeeper cache SQLite database file'

  REQUIRED_STRUCTURE = {
      'cfurl_cache_blob_data': frozenset([]),
      'cfurl_cache_receiver_data': frozenset([
          'entry_ID', 'receiver_data', 'entry_ID']),
      'cfurl_cache_response': frozenset([
          'request_key', 'time_stamp', 'entry_ID'])}

  QUERIES = [((
      'SELECT d.entry_ID AS id, d.receiver_data AS data, r.request_key, '
      'r.time_stamp AS time_string FROM cfurl_cache_receiver_data d, '
      'cfurl_cache_response r WHERE r.entry_ID = '
      'd.entry_ID'), 'ParseReceiverData')]

  SCHEMAS = [{
      'cfurl_cache_blob_data': (
          'CREATE TABLE cfurl_cache_blob_data(entry_ID INTEGER PRIMARY KEY, '
          'response_object BLOB, request_object BLOB, proto_props BLOB, '
          'user_info BLOB)'),
      'cfurl_cache_receiver_data': (
          'CREATE TABLE cfurl_cache_receiver_data(entry_ID INTEGER PRIMARY '
          'KEY, receiver_data BLOB)'),
      'cfurl_cache_response': (
          'CREATE TABLE cfurl_cache_response(entry_ID INTEGER PRIMARY KEY '
          'AUTOINCREMENT UNIQUE, version INTEGER, hash_value INTEGER, '
          'storage_policy INTEGER, request_key TEXT UNIQUE, time_stamp NOT '
          'NULL DEFAULT CURRENT_TIMESTAMP, partition TEXT)'),
      'cfurl_cache_schema_version': (
          'CREATE TABLE cfurl_cache_schema_version(schema_version INTEGER)')}]

  def _DictToListOfStrings(self, data_dict):
    """Converts a dictionary into a list of strings.

    Args:
      data_dict (dict[str, object]): dictionary to convert.

    Returns:
      list[str]: list of strings.
    """
    ret_list = []
    for key, value in data_dict.items():
      if key in ('body', 'datetime', 'type', 'room', 'rooms', 'id'):
        continue
      ret_list.append('{0:s} = {1!s}'.format(key, value))

    return ret_list

  def _ExtractJQuery(self, jquery_raw):
    """Extracts values from a JQuery string.

    Args:
      jquery_raw (str): JQuery string.

    Returns:
      dict[str, str]: extracted values.
    """
    data_part = ''
    if not jquery_raw:
      return {}

    if '[' in jquery_raw:
      _, _, first_part = jquery_raw.partition('[')
      data_part, _, _ = first_part.partition(']')
    elif jquery_raw.startswith('//'):
      _, _, first_part = jquery_raw.partition('{')
      data_part = '{{{0:s}'.format(first_part)
    elif '({' in jquery_raw:
      _, _, first_part = jquery_raw.partition('(')
      data_part, _, _ = first_part.rpartition(')')

    if not data_part:
      return {}

    try:
      data_dict = json.loads(data_part)
    except ValueError:
      return {}

    return data_dict

  def _GetDateTimeRowValue(self, parser_mediator, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.JavaTime: date and time value or None if not available.
    """
    time_value = self._GetRowValue(query_hash, row, value_name)
    if time_value is None:
      return None

    if isinstance(time_value, int):
      return dfdatetime_java_time.JavaTime(timestamp=time_value)

    try:
      date_time = dfdatetime_time_elements.TimeElements()
      date_time.CopyFromDateTimeString(time_value)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse time string: {0:s} with error: {1!s}'.format(
              time_value, exception))
      return None

    return date_time

  def _ParseChatData(self, data):
    """Parses chat comment data.

    Args:
      data (dict[str, object]): chat comment data as returned by SQLite.

    Returns:
      dict[str, object]: parsed chat comment data.
    """
    data_store = {}

    if 'body' in data:
      body = data.get('body', '').replace('\n', ' ')
      if body.startswith('//') and '{' in body:
        body_dict = self._ExtractJQuery(body)
        title, _, _ = body.partition('{')
        body = '{0:s} <{1!s}>'.format(
            title[2:], self._DictToListOfStrings(body_dict))
    else:
      body = 'No text.'

    data_store['text'] = body

    room = data.get('rooms', None)
    if not room:
      room = data.get('room', None)
    if room:
      data_store['room'] = room

    data_store['id'] = data.get('id', None)
    user = data.get('user', None)
    if user:
      try:
        user_sid = int(user)
        data_store['sid'] = user_sid
      except (ValueError, TypeError):
        data_store['user'] = user

    return data_store

  def ParseReceiverData(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a single row from the receiver and cache response table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    data = {}
    key_url = self._GetRowValue(query_hash, row, 'request_key')

    data_dict = {}
    description = 'MacKeeper Entry'
    # Check the URL, since that contains vital information about the type of
    # event we are dealing with.
    if key_url.endswith('plist'):
      description = 'Configuration Definition'
      data['text'] = 'Plist content added to cache.'

    elif key_url.startswith('http://event.zeobit.com'):
      description = 'MacKeeper Event'
      try:
        _, _, part = key_url.partition('?')
        data['text'] = part.replace('&', ' ')
      except UnicodeDecodeError:
        data['text'] = 'N/A'

    elif key_url.startswith('http://account.zeobit.com'):
      description = 'Account Activity'
      _, _, activity = key_url.partition('#')
      if activity:
        data['text'] = 'Action started: {0:s}'.format(activity)
      else:
        data['text'] = 'Unknown activity.'

    elif key_url.startswith('http://support.') and 'chat' in key_url:
      description = 'Chat '
      try:
        jquery = self._GetRowValue(query_hash, row, 'data')
        jquery = codecs.decode(jquery, 'utf-8')
      except UnicodeDecodeError:
        jquery = ''

      data_dict = self._ExtractJQuery(jquery)
      data = self._ParseChatData(data_dict)

      data['entry_type'] = data_dict.get('type', '')
      if data['entry_type'] == 'comment':
        description += 'Comment'
      elif data['entry_type'] == 'outgoing':
        description += 'Outgoing Message'
      elif data['entry_type'] == 'incoming':
        description += 'Incoming Message'
      else:
        # Empty or not known entry type, generic status message.
        description += 'Entry'
        data['text'] = ';'.join(self._DictToListOfStrings(data_dict))
        if not data['text']:
          data['text'] = 'No additional data.'

    event_data = MacKeeperCacheEventData()
    event_data.added_time = self._GetDateTimeRowValue(
        parser_mediator, query_hash, row, 'time_string')
    event_data.description = description
    event_data.event_type = data.get('event_type', None)
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.record_id = data.get('id', None)
    event_data.room = data.get('room', None)
    event_data.text = data.get('text', None)
    event_data.url = key_url
    event_data.user_name = data.get('user', None)
    event_data.user_sid = data.get('sid', None)

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(MacKeeperCachePlugin)
