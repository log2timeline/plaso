# -*- coding: utf-8 -*-
"""This file contains a parser for the Mac OS X MacKeeper cache database."""

import codecs
import json

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import py2to3
from plaso.lib import timelib
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


def DictToList(data_dict):
  """Take a dict object and return a list of strings back."""
  ret_list = []
  for key, value in data_dict.iteritems():
    if key in [u'body', u'datetime', u'type', u'room', u'rooms', u'id']:
      continue
    ret_list.append(u'{0:s} = {1!s}'.format(key, value))

  return ret_list


def ExtractJQuery(jquery_raw):
  """Extract and return the data inside a JQuery as a dict object."""
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


def ParseChatData(data):
  """Parse a chat comment data dict and return a parsed one back.

  Args:
    data: A dict object that is parsed from the record.

  Returns:
    A dict object to store the results in.
  """
  data_store = {}

  if u'body' in data:
    body = data.get(u'body', u'').replace(u'\n', u' ')
    if body.startswith(u'//') and u'{' in body:
      body_dict = ExtractJQuery(body)
      title, _, _ = body.partition(u'{')
      body = u'{0:s} <{1!s}>'.format(title[2:], DictToList(body_dict))
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


class MacKeeperCacheEvent(time_events.TimestampEvent):
  """Convenience class for a MacKeeper Cache event."""
  DATA_TYPE = u'mackeeper:cache'

  def __init__(self, timestamp, description, identifier, url, data_dict):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC
      description: The description of the cache entry.
      identifier: The row identifier.
      url: The MacKeeper URL value that is stored in every event.
      data_dict: A dict object with the descriptive information.
    """
    super(MacKeeperCacheEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)

    self.description = description
    self.event_type = data_dict.get(u'event_type', None)
    self.offset = identifier
    self.record_id = data_dict.get(u'id', None)
    self.room = data_dict.get(u'room', None)
    self.text = data_dict.get(u'text', None)
    self.url = url
    self.user_name = data_dict.get(u'user', None)
    self.user_sid = data_dict.get(u'sid', None)


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

  def ParseReceiverData(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a single row from the receiver and cache response table.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
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

      data_dict = ExtractJQuery(jquery)
      data = ParseChatData(data_dict)

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
        data[u'text'] = u';'.join(DictToList(data_dict))
        if not data[u'text']:
          data[u'text'] = u'No additional data.'

    time_value = row['time_string']
    if isinstance(time_value, py2to3.INTEGER_TYPES):
      timestamp = timelib.Timestamp.FromJavaTime(time_value)
    else:
      try:
        timestamp = timelib.Timestamp.FromTimeString(time_value)
      except errors.TimestampError:
        parser_mediator.ProduceParseError(
            u'Unable to parse time string: {0:s}'.format(time_value))
        return

    event_object = MacKeeperCacheEvent(
        timestamp, description, row['id'], key_url, data)
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(MacKeeperCachePlugin)
