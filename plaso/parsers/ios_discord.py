"""Parser for iOS Discord message (JSON) files."""

import codecs
import json
import os

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class IOSDiscordMessageEventData(events.EventData):
  """iOS discord message event data.

  Attributes:
    attachment_name (str): The attachment filename.
    attachment_proxy_urls (str): The attachment proxy URL.
    attachment_size (int): The attachment size.
    attachment_type (str): The attachment type.
    channel_identifier (str): identifier of the user channel.
    content (str): Message content.
    edited_timestamp (str): Message edit time.
    sent_time (dfdatetime.DateTimeValues): Message timestamp.
    user_identifier (str): ID of the message author.
    username (str): The username of the message sender.
  """

  DATA_TYPE = 'ios:discord:message'

  def __init__(self):
    """Initializes event data."""
    super().__init__(data_type=self.DATA_TYPE)
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
  """Parses iOS discord message files."""

  NAME = 'discord_ios'
  DATA_FORMAT = 'iOS discord message'

  REQUIRED_MESSAGE_KEYS = frozenset([
      'attachments', 'author', 'channel_id', 'content', 'timestamp'])

  _ENCODING = 'utf-8'
  _MAXIMUM_FILE_SIZE = 16 * 1024 * 1024

  def _GetDateTimeValue(self, parser_mediator, timestamp):
    """Retrieves a date and time value.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      timestamp (Optional[str]): timestamp value.

    Returns:
      dfdatetime.TimeElementsInMicroseconds: date and time value or None if
          not available.
    """
    if timestamp is None:
      return None

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(timestamp)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          f'Unable to parse timestamp value: {timestamp:s} with error: '
          f'{exception!s}')
      date_time = None

    return date_time

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a iOS discord message file."""
    # First check for initial 2 characters being open brace and open list.
    if file_object.read(2) != b'[{':
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          f'[{self.NAME!s}] {display_name!s} is not a valid Discord messages '
          f'file, missing opening brace and list')

    file_object.seek(0, os.SEEK_SET)

    # Note that _MAXIMUM_FILE_SIZE prevents this read to become too large.
    file_content = file_object.read()

    try:
      file_content = codecs.decode(file_content, self._ENCODING)
    except (UnicodeDecodeError, json.JSONDecodeError):
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          f'[{self.NAME!s}] {display_name!s} is not a valid Discord messages '
          f'file, unable to decode as UTF-8')

    # Second verify it is valid JSON.
    try:
      json_dict = json.loads(file_content)

    except OSError as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          f'[{self.NAME!s}] Unable to open file {display_name!s} with error: '
          f'{exception!s}')

    except ValueError as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          f'[{self.NAME!s}] {display_name!s} is not a valid Discord messages '
          f'file, unable to decode as JSON with error: {exception!s}')

    # Third verify the file has the correct keys for a Discord messages file.
    messages = json_dict or [{}]

    if not set(self.REQUIRED_MESSAGE_KEYS).issubset(set(messages[0].keys())):
      raise errors.WrongParser('File does not contain Discord messages data')

    for message in messages:
      attachments = message.get('attachments') or [{}]
      timestamp = message.get('timestamp')

      event_data = IOSDiscordMessageEventData()
      event_data.attachment_name = attachments[0].get('filename') or None
      event_data.attachment_proxy_url = attachments[0].get('proxy_url') or None
      event_data.attachment_size = attachments[0].get('size') or None
      event_data.attachment_type = attachments[0].get('content_type') or None
      event_data.channel_identifier = message.get('channel_id') or None
      event_data.content = message.get('content') or None
      event_data.sent_time = self._GetDateTimeValue(parser_mediator, timestamp)
      event_data.user_identifier = message.get('author', {}).get('id') or None
      event_data.username = message.get('author', {}).get('username') or None

      parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(IOSDiscordParser)
