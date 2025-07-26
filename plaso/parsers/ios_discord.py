# -*- coding: utf-8 -*-
"""Parser for iOS Discord message."""

import json

from dfdatetime import time_elements as dfdatetime_time_elements
from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class IOSDiscordMessageEventData(events.EventData):
  """iOS discord message event data.

  Attributes:
    attachment_name (str):  The attachment filename.
    attachment_size (int):  The attachment size.
    attachment_type (str):  The attachment type.
    attachment_proxy_urls (str): The attachment proxy URL.
    channel_identifier (str): ID of the user channel.
    content (str): Message content.
    edited_timestamp (str): Message edit time.
    sent_time (dfdatetime.DateTimeValues): Message timestamp.
    user_identifier (str): ID of the message author.
    username (str): The username of the message sender.
  """

  DATA_TYPE = 'ios:discord:message'

  def __init__(self):
    """Initializes event data."""
    super(IOSDiscordMessageEventData, self).__init__(data_type=self.DATA_TYPE)
    self.attachment_name = None
    self.attachment_proxy_url = None
    self.attachment_size = None
    self.attachment_type = None
    self.channel_identifier = None
    self.content = None
    self.sent_time = None
    self.user_identifier = None
    self.username = None


class IOSDiscordParser(interface.FileObjectParser):
  """Parses iOS discord message log files."""

  NAME = 'discord_ios'
  DATA_FORMAT = 'iOS discord message'
  _ENCODING = 'utf-8'
  _MAXIMUM_FILE_SIZE = 16 * 1024 * 1024

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a iOS discord message log file."""
    file_content = file_object.read()

    try:
      file_content = file_content.decode(self._ENCODING)
      json_data = json.loads(file_content)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
      raise errors.WrongParser(f'Failed to parse file as JSON: {e}')

    if not isinstance(json_data, list):
      raise errors.WrongParser(
        'Discord log file does not contain a valid message list.')

    for message in json_data:
      date_time = None
      timestamp = message.get('timestamp')
      if timestamp:
        try:
          date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
          date_time.CopyFromStringISO8601(timestamp)
        except ValueError as exception:
          parser_mediator.ProduceExtractionWarning(
              'Unable to parse time string: {0:s} with error: {1!s}'.format(
                  timestamp, exception))
          date_time = None

      attachments_row = message.get('attachments', [])
      if attachments_row:
        att_filename = attachments_row[0].get('filename') or None
        att_size = attachments_row[0].get('size') or None
        att_type = attachments_row[0].get('content_type') or None
        att_proxy_url = attachments_row[0].get('proxy_url') or None
      else:
        att_filename = None
        att_size = None
        att_type = None
        att_proxy_url = None

      channel_identifier = message.get('channel_id') or None
      content = message.get('content') or None
      user_identifier = message.get('author', {}).get('id') or None
      username = message.get('author', {}).get('username') or None

      event_data = IOSDiscordMessageEventData()
      event_data.attachment_name = att_filename
      event_data.attachment_proxy_url = att_proxy_url
      event_data.attachment_size = att_size
      event_data.attachment_type = att_type
      event_data.channel_identifier = channel_identifier
      event_data.content = content
      event_data.sent_time = date_time
      event_data.user_identifier = user_identifier
      event_data.username = username

      parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(IOSDiscordParser)
