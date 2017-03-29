# -*- coding: utf-8 -*-
"""This file contains a basic Skype SQLite parser."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


__author__ = 'Joaquin Moreno Garijo (bastionado@gmail.com)'


class SkypeChatEventData(events.EventData):
  """Skype chat event data.

  Attributes:
    from_account (str): from display name and the author.
    text (str): body XML.
    title (str): title.
    to_account (str): accounts, excluding the author, of the conversation.
  """

  DATA_TYPE = u'skype:event:chat'

  def __init__(self):
    """Initializes event data."""
    super(SkypeChatEventData, self).__init__(data_type=self.DATA_TYPE)
    self.from_account = None
    self.text = None
    self.title = None
    self.to_account = None


class SkypeAccountEventData(events.EventData):
  """Skype account event data.

  Attributes:
    country (str): home country of the account holder.
    display_name (str): display name of the account holder.
    email (str): registered email address of the account holder.
    username (str): full name of the Skype account holder and display name.
  """

  DATA_TYPE = u'skype:event:account'

  def __init__(self):
    """Initialize event data."""
    super(SkypeAccountEventData, self).__init__(data_type=self.DATA_TYPE)
    self.country = None
    self.display_name = None
    self.email = None
    self.offset = None
    self.username = None


class SkypeSMSEventData(events.EventData):
  """SKype SMS event data.

  Attributes:
    number (str): phone number where the SMS was sent.
    text (str): text (SMS body) that was sent.
  """

  DATA_TYPE = u'skype:event:sms'

  def __init__(self):
    """Initialize event data."""
    super(SkypeSMSEventData, self).__init__(data_type=self.DATA_TYPE)
    self.number = None
    self.text = None


class SkypeCallEventData(events.EventData):
  """Skype call event data.

  Attributes:
    call_type (str): call type, such as: WAITING, STARTED, FINISHED.
    dst_call (str): account which received the call.
    src_call (str): account which started the call.
    user_start_call (bool): True if the owner account started the call.
    video_conference (bool): True if the call was a video conference.
  """

  DATA_TYPE = u'skype:event:call'

  def __init__(self):
    """Initialize event data."""
    super(SkypeCallEventData, self).__init__(data_type=self.DATA_TYPE)
    self.call_type = None
    self.dst_call = None
    self.src_call = None
    self.user_start_call = None
    self.video_conference = None


class SkypeTransferFileEventData(events.EventData):
  """Skype file transfer event data.

  Attributes:
    action_type (str): action type e.g. GETSOLICITUDE, SENDSOLICITUDE,
        ACCEPTED, FINISHED.
    destination (str): account that received the file.
    source (str): account that sent the file.
    transferred_filename (str): name of the file transferred.
    transferred_file_path (str): path of the file transferred.
    transferred_filesize (int): size of the file transferred.
  """

  DATA_TYPE = u'skype:event:transferfile'

  def __init__(self):
    """Initialize event data."""
    super(SkypeTransferFileEventData, self).__init__(data_type=self.DATA_TYPE)
    self.action_type = None
    self.destination = None
    self.source = None
    self.transferred_filename = None
    self.transferred_filepath = None
    self.transferred_filesize = None


class SkypePlugin(interface.SQLitePlugin):
  """SQLite plugin for Skype main.db SQlite database file."""

  NAME = u'skype'
  DESCRIPTION = u'Parser for Skype SQLite database files.'

  # Queries for building cache.
  QUERY_DEST_FROM_TRANSFER = (
      u'SELECT parent_id, partner_handle AS skypeid, '
      u'partner_dispname AS skypename FROM transfers')
  QUERY_SOURCE_FROM_TRANSFER = (
      u'SELECT pk_id, partner_handle AS skypeid, '
      u'partner_dispname AS skypename FROM transfers')

  QUERIES = [
      ((u'SELECT c.id, c.participants, c.friendlyname AS title, '
        u'm.author AS author, m.from_dispname AS from_displayname, '
        u'm.body_xml, m.timestamp, c.dialog_partner FROM Chats c, Messages m '
        u'WHERE c.name = m.chatname'), u'ParseChat'),
      ((u'SELECT id, fullname, given_displayname, emails, '
        u'country, profile_timestamp, authreq_timestamp, '
        u'lastonline_timestamp, mood_timestamp, sent_authrequest_time, '
        u'lastused_timestamp FROM Accounts'), u'ParseAccountInformation'),
      ((u'SELECT id, target_numbers AS dstnum_sms, timestamp AS time_sms, '
        u'body AS msg_sms FROM SMSes'), u'ParseSMS'),
      ((u'SELECT id, partner_handle, partner_dispname, offer_send_list, '
        u'starttime, accepttime, finishtime, filepath, filename, filesize, '
        u'status, parent_id, pk_id FROM Transfers'), u'ParseFileTransfer'),
      ((u'SELECT c.id, cm.guid, c.is_incoming, '
        u'cm.call_db_id, cm.videostatus, c.begin_timestamp AS try_call, '
        u'cm.start_timestamp AS accept_call, cm.call_duration '
        u'FROM Calls c, CallMembers cm '
        u'WHERE c.id = cm.call_db_id;'), u'ParseCall')]

  REQUIRED_TABLES = frozenset([
      u'Chats', u'Accounts', u'Conversations', u'Contacts', u'SMSes',
      u'Transfers', u'CallMembers', u'Calls'])

  def ParseAccountInformation(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses account information.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row with account information.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".
    display_name = row['given_displayname']
    username = u'{0:s} <{1:s}>'.format(row['fullname'], display_name)

    event_data = SkypeAccountEventData()
    event_data.country = row['country']
    event_data.display_name = display_name
    event_data.email = row['emails']
    event_data.offset = row['id']
    event_data.query = query
    event_data.username = username

    timestamp = row['profile_timestamp']
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, u'Profile Changed')
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = row['authreq_timestamp']
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, u'Authenticate Request')
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = row['lastonline_timestamp']
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, u'Last Online')
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = row['mood_timestamp']
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, u'Mood Event')
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = row['sent_authrequest_time']
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, u'Auth Request Sent')
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = row['lastused_timestamp']
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, u'Last Used')
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseChat(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a chat message.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row resulting from query.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    accounts = []
    participants = row['participants'].split(' ')
    for participant in participants:
      if participant != row['author']:
        accounts.append(participant)

    to_account = u', '.join(accounts)
    if not to_account:
      to_account = row['dialog_partner'] or u'Unknown User'

    from_account = u'{0:s} <{1:s}>'.format(
        row['from_displayname'], row['author'])

    event_data = SkypeChatEventData()
    event_data.from_account = from_account
    event_data.query = query
    event_data.text = row['body_xml']
    event_data.title = row['title']
    event_data.to_account = to_account

    timestamp = row['timestamp']
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, u'Chat from Skype')
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseSMS(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses an SMS.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row resulting from query.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    phone_number = row['dstnum_sms']
    if phone_number:
      phone_number = phone_number.replace(u' ', u'')

    event_data = SkypeSMSEventData()
    event_data.number = phone_number
    event_data.query = query
    event_data.text = row['msg_sms']

    timestamp = row['time_sms']
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, u'SMS from Skype')
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseCall(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a call.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row resulting from query.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    try:
      aux = row['guid']
      if aux:
        aux_list = aux.split(u'-')
        src_aux = aux_list[0]
        dst_aux = aux_list[1]
      else:
        src_aux = u'Unknown [no GUID]'
        dst_aux = u'Unknown [no GUID]'
    except IndexError:
      src_aux = u'Unknown [{0:s}]'.format(row['guid'])
      dst_aux = u'Unknown [{0:s}]'.format(row['guid'])

    if row['is_incoming'] == u'0':
      user_start_call = True
      source = src_aux
      if row['ip_address']:
        destination = u'{0:s} <{1:s}>'.format(dst_aux, row['ip_address'])
      else:
        destination = dst_aux
    else:
      user_start_call = False
      source = src_aux
      destination = dst_aux

    call_identifier = row['id']

    event_data = SkypeCallEventData()
    event_data.dst_call = destination
    event_data.offset = call_identifier
    event_data.query = query
    event_data.src_call = source
    event_data.user_start_call = user_start_call
    event_data.video_conference = row['videostatus'] == u'3'

    timestamp = row['try_call']
    event_data.call_type = u'WAITING'
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(date_time, u'Call from Skype')
    parser_mediator.ProduceEventWithEventData(event, event_data)

    try:
      timestamp = int(row['accept_call'])
    except ValueError:
      timestamp = None

    if timestamp:
      event_data.call_type = u'ACCEPTED'
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(date_time, u'Call from Skype')
      parser_mediator.ProduceEventWithEventData(event, event_data)

      try:
        call_duration = int(row['call_duration'])
      except ValueError:
        parser_mediator.ProduceExtractionError(
            u'unable to determine when call: {0:s} was finished.'.format(
                call_identifier))
        call_duration = None

      if call_duration:
        timestamp += call_duration
        event_data.call_type = u'FINISHED'
        date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
        event = time_events.DateTimeValuesEvent(date_time, u'Call from Skype')
        parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileTransfer(
      self, parser_mediator, row, cache=None, database=None, query=None,
      **unused_kwargs):
    """Parses a file transfer.

    There is no direct relationship between who sends the file and
    who accepts the file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row resulting from query.
      cache (Optional[SQLiteCache]): cache.
      database (Optional[SQLiteDatabase]): database.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    source_dict = cache.GetResults(u'source')
    if not source_dict:
      results = database.Query(self.QUERY_SOURCE_FROM_TRANSFER)

      cache.CacheQueryResults(
          results, 'source', 'pk_id', ('skypeid', 'skypename'))
      source_dict = cache.GetResults(u'source')

    dest_dict = cache.GetResults(u'destination')
    if not dest_dict:
      results = database.Query(self.QUERY_DEST_FROM_TRANSFER)

      cache.CacheQueryResults(
          results, 'destination', 'parent_id', ('skypeid', 'skypename'))
      dest_dict = cache.GetResults(u'destination')

    source = u'Unknown'
    destination = u'Unknown'

    if row['parent_id']:
      destination = u'{0:s} <{1:s}>'.format(
          row['partner_handle'], row['partner_dispname'])
      skype_id, skype_name = source_dict.get(row['parent_id'], [None, None])
      if skype_name:
        source = u'{0:s} <{1:s}>'.format(skype_id, skype_name)
    else:
      source = u'{0:s} <{1:s}>'.format(
          row['partner_handle'], row['partner_dispname'])

      if row['pk_id']:
        skype_id, skype_name = dest_dict.get(row['pk_id'], [None, None])
        if skype_name:
          destination = u'{0:s} <{1:s}>'.format(skype_id, skype_name)

    filename = row['filename']
    filesize = row['filesize']

    try:
      # TODO: add a conversion base.
      file_size = int(filesize)
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'unable to convert file size: {0!s} of file: {1:s}'.format(
              filesize, filename))
      file_size = 0

    event_data = SkypeTransferFileEventData()
    event_data.destination = destination
    event_data.offset = row['id']
    event_data.query = query
    event_data.source = source
    event_data.transferred_filename = filename
    event_data.transferred_filepath = row['filepath']
    event_data.transferred_filesize = file_size

    if row['status'] == 2:
      if row['starttime']:
        event_data.action_type = u'SENDSOLICITUDE'

        date_time = dfdatetime_posix_time.PosixTime(timestamp=row['starttime'])
        event = time_events.DateTimeValuesEvent(
            date_time, u'File transfer from Skype')
        parser_mediator.ProduceEventWithEventData(event, event_data)

    elif row['status'] == 8:
      if row['starttime']:
        event_data.action_type = u'GETSOLICITUDE'

        date_time = dfdatetime_posix_time.PosixTime(timestamp=row['starttime'])
        event = time_events.DateTimeValuesEvent(
            date_time, u'File transfer from Skype')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if row['accepttime']:
        event_data.action_type = u'ACCEPTED'

        date_time = dfdatetime_posix_time.PosixTime(timestamp=row['accepttime'])
        event = time_events.DateTimeValuesEvent(
            date_time, u'File transfer from Skype')
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if row['finishtime']:
        event_data.action_type = u'FINISHED'

        date_time = dfdatetime_posix_time.PosixTime(timestamp=row['finishtime'])
        event = time_events.DateTimeValuesEvent(
            date_time, u'File transfer from Skype')
        parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(SkypePlugin)
