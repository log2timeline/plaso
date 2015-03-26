# -*- coding: utf-8 -*-
"""This file contains a parser for the Mac OS X MacKeeper cache database."""

import json

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


def DictToList(data_dict):
  """Take a dict object and return a list of strings back."""
  ret_list = []
  for key, value in data_dict.iteritems():
    if key in ('body', 'datetime', 'type', 'room', 'rooms', 'id'):
      continue
    ret_list.append(u'{0:s} = {1!s}'.format(key, value))

  return ret_list


def ExtractJQuery(jquery_raw):
  """Extract and return the data inside a JQuery as a dict object."""
  data_part = u''
  if not jquery_raw:
    return {}

  if '[' in jquery_raw:
    _, _, first_part = jquery_raw.partition('[')
    data_part, _, _ = first_part.partition(']')
  elif jquery_raw.startswith('//'):
    _, _, first_part = jquery_raw.partition('{')
    data_part = u'{{{0:s}'.format(first_part)
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


def ParseChatData(data):
  """Parse a chat comment data dict and return a parsed one back.

  Args:
    data: A dict object that is parsed from the record.

  Returns:
    A dict object to store the results in.
  """
  data_store = {}

  if 'body' in data:
    body = data.get('body', '').replace('\n', ' ')
    if body.startswith('//') and '{' in body:
      body_dict = ExtractJQuery(body)
      title, _, _ = body.partition('{')
      body = u'{0:s} <{1!s}>'.format(title[2:], DictToList(body_dict))
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


class MacKeeperCacheEvent(event.EventObject):
  """Convenience class for a MacKeeper Cache event."""
  DATA_TYPE = 'mackeeper:cache'

  def __init__(self, timestamp, description, identifier, url, data_dict):
    """Initializes the event object.

    Args:
      timestamp: A timestamp as a number of milliseconds since Epoch
                 or as a UTC string.
      description: The description of the cache entry.
      identifier: The row identifier.
      url: The MacKeeper URL value that is stored in every event.
      data_dict: A dict object with the descriptive information.
    """
    super(MacKeeperCacheEvent, self).__init__()

    # Two different types of timestamps stored in log files.
    if type(timestamp) in (int, long):
      self.timestamp = timelib.Timestamp.FromJavaTime(timestamp)
    else:
      self.timestamp = timelib.Timestamp.FromTimeString(timestamp)

    self.timestamp_desc = eventdata.EventTimestamp.ADDED_TIME
    self.description = description
    self.offset = identifier
    self.text = data_dict.get('text', None)
    self.user_sid = data_dict.get('sid', None)
    self.user_name = data_dict.get('user', None)
    self.event_type = data_dict.get('event_type', None)
    self.room = data_dict.get('room', None)
    self.record_id = data_dict.get('id', None)
    self.url = url


class MacKeeperCachePlugin(interface.SQLitePlugin):
  """Plugin for the MacKeeper Cache database file."""

  NAME = 'mackeeper_cache'
  DESCRIPTION = u'Parser for MacKeeper Cache SQLite database files.'

  # Define the needed queries.
  QUERIES = [((
      'SELECT d.entry_ID AS id, d.receiver_data AS data, r.request_key, '
      'r.time_stamp AS time_string FROM cfurl_cache_receiver_data d, '
      'cfurl_cache_response r WHERE r.entry_ID = '
      'd.entry_ID'), 'ParseReceiverData')]

  # The required tables.
  REQUIRED_TABLES = frozenset([
      'cfurl_cache_blob_data', 'cfurl_cache_receiver_data',
      'cfurl_cache_response'])

  def ParseReceiverData(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a single row from the receiver and cache response table.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    data = {}
    key_url = row['request_key']

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
        data['text'] = u'Action started: {0:s}'.format(activity)
      else:
        data['text'] = u'Unknown activity.'
    elif key_url.startswith('http://support.') and 'chat' in key_url:
      description = 'Chat '
      try:
        jquery = unicode(row['data'])
      except UnicodeDecodeError:
        jquery = ''

      data_dict = ExtractJQuery(jquery)
      data = ParseChatData(data_dict)

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
        data['text'] = u';'.join(DictToList(data_dict))
        if not data['text']:
          data['text'] = 'No additional data.'

    event_object = MacKeeperCacheEvent(
        row['time_string'], description, row['id'], key_url, data)
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(MacKeeperCachePlugin)
