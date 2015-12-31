# -*- coding: utf-8 -*-
"""This file contains a basic Skype SQLite parser."""

import logging

from plaso.events import time_events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


__author__ = 'Joaquin Moreno Garijo (bastionado@gmail.com)'


class SkypeChatEvent(time_events.PosixTimeEvent):
  """Convenience class for a Skype event."""

  DATA_TYPE = u'skype:event:chat'

  def __init__(self, row, to_account):
    """Build a Skype Event from a single row.

    Args:
      row: A row object (instance of sqlite3.Row) that contains the
           extracted data from a single row in the database.
      to_account: A string containing the accounts (excluding the
                  author) of the conversation.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    super(SkypeChatEvent, self).__init__(
        row['timestamp'], u'Chat from Skype', self.DATA_TYPE)

    self.title = row['title']
    self.text = row['body_xml']
    self.from_account = u'{0:s} <{1:s}>'.format(
        row['from_displayname'], row['author'])
    self.to_account = to_account


class SkypeAccountEvent(time_events.PosixTimeEvent):
  """Convenience class for account information."""

  DATA_TYPE = u'skype:event:account'

  def __init__(
      self, timestamp, usage, identifier, full_name, display_name, email,
      country):
    """Initialize the event.

    Args:
      timestamp: The POSIX timestamp value.
      usage: A string containing the description string of the timestamp.
      identifier: The row identifier.
      full_name: A string containing the full name of the Skype account holder.
      display_name: A string containing the chosen display name of the account
                    holder.
      email: A string containing the registered email address of the account
             holder.
      country: A string containing the chosen home country of the account
               holder.
    """
    super(SkypeAccountEvent, self).__init__(timestamp, usage)

    self.offset = identifier
    self.username = u'{0:s} <{1:s}>'.format(full_name, display_name)
    self.display_name = display_name
    self.email = email
    self.country = country
    self.data_type = self.DATA_TYPE


class SkypeSMSEvent(time_events.PosixTimeEvent):
  """Convenience EventObject for SMS."""

  DATA_TYPE = u'skype:event:sms'

  def __init__(self, row, dst_number):
    """Read the information related with the SMS.

      Args:
        row: row form the sql query.
          row['time_sms']: timestamp when the sms was send.
          row['dstnum_sms']: number which receives the sms.
          row['msg_sms']: text send to this sms.
        dst_number: phone number where the user send the sms.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    super(SkypeSMSEvent, self).__init__(
        row['time_sms'], u'SMS from Skype', self.DATA_TYPE)

    self.number = dst_number
    self.text = row['msg_sms']


class SkypeCallEvent(time_events.PosixTimeEvent):
  """Convenience EventObject for the calls."""

  DATA_TYPE = u'skype:event:call'

  def __init__(self, timestamp, call_type, user_start_call,
               source, destination, video_conference):
    """Contains information if the call was cancelled, accepted or finished.

      Args:
        timestamp: the timestamp of the event.
        call_type: WAITING, STARTED, FINISHED.
        user_start_call: boolean, true indicates that the owner
                         account started the call.
        source: the account which started the call.
        destination: the account which gets the call.
        video_conference: boolean, if is true it was a videoconference.
    """

    super(SkypeCallEvent, self).__init__(
        timestamp, u'Call from Skype', self.DATA_TYPE)

    self.call_type = call_type
    self.user_start_call = user_start_call
    self.src_call = source
    self.dst_call = destination
    self.video_conference = video_conference


class SkypeTransferFileEvent(time_events.PosixTimeEvent):
  """Evaluate the action of send a file."""

  DATA_TYPE = u'skype:event:transferfile'

  def __init__(self, row, timestamp, action_type, source, destination):
    """Actions related with sending files.

      Args:
        row:
          filepath: path from the file.
          filename: name of the file.
          filesize: size of the file.
        timestamp: when the action happens.
        action_type: GETSOLICITUDE, SENDSOLICITUDE, ACCEPTED, FINISHED.
        source: The account that sent the file.
        destination: The account that received the file.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    super(SkypeTransferFileEvent, self).__init__(
        timestamp, u'File transfer from Skype', self.DATA_TYPE)

    self.offset = row['id']
    self.action_type = action_type
    self.source = source
    self.destination = destination
    self.transferred_filepath = row['filepath']
    self.transferred_filename = row['filename']

    try:
      self.transferred_filesize = int(row['filesize'])
    except ValueError:
      logging.debug(u'Unknown filesize {0:s}'.format(
          self.transferred_filename))
      self.transferred_filesize = 0


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

  # Define the needed queries.
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

  # The required tables.
  REQUIRED_TABLES = frozenset([
      u'Chats', u'Accounts', u'Conversations', u'Contacts', u'SMSes',
      u'Transfers', u'CallMembers', u'Calls'])

  def ParseAccountInformation(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses the Accounts database.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    if row['profile_timestamp']:
      event_object = SkypeAccountEvent(
          row['profile_timestamp'], u'Profile Changed', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['authreq_timestamp']:
      event_object = SkypeAccountEvent(
          row['authreq_timestamp'], u'Authenticate Request', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['lastonline_timestamp']:
      event_object = SkypeAccountEvent(
          row['lastonline_timestamp'], u'Last Online', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['mood_timestamp']:
      event_object = SkypeAccountEvent(
          row['mood_timestamp'], u'Mood Event', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['sent_authrequest_time']:
      event_object = SkypeAccountEvent(
          row['sent_authrequest_time'], u'Auth Request Sent', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['lastused_timestamp']:
      event_object = SkypeAccountEvent(
          row['lastused_timestamp'], u'Last Used', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

  def ParseChat(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a chat message row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    to_account = u''
    accounts = []
    participants = row['participants'].split(' ')
    for participant in participants:
      if participant != row['author']:
        accounts.append(participant)
    to_account = u', '.join(accounts)

    if not to_account:
      if row['dialog_partner']:
        to_account = row['dialog_partner']
      else:
        to_account = u'Unknown User'

    event_object = SkypeChatEvent(row, to_account)
    parser_mediator.ProduceEvent(event_object, query=query)

  def ParseSMS(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parse SMS.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    dst_number = row['dstnum_sms'].replace(u' ', u'')

    event_object = SkypeSMSEvent(row, dst_number)
    parser_mediator.ProduceEvent(event_object, query=query)

  def ParseCall(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parse the calls taking into accounts some rows.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
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

    if row['videostatus'] == u'3':
      video_conference = True
    else:
      video_conference = False

    event_object = SkypeCallEvent(
        row['try_call'], u'WAITING', user_start_call, source, destination,
        video_conference)
    parser_mediator.ProduceEvent(event_object, query=query)

    if row['accept_call']:
      event_object = SkypeCallEvent(
          row['accept_call'], u'ACCEPTED', user_start_call, source,
          destination, video_conference)
      parser_mediator.ProduceEvent(event_object, query=query)

      if row['call_duration']:
        try:
          timestamp = int(row['accept_call']) + int(row['call_duration'])
          event_object = SkypeCallEvent(
              timestamp, u'FINISHED', user_start_call, source, destination,
              video_conference)
          parser_mediator.ProduceEvent(event_object, query=query)

        except ValueError:
          logging.debug((
              u'[{0:s}] Unable to determine when the call {1:s} was '
              u'finished.').format(self.NAME, row['id']))

  def ParseFileTransfer(
      self, parser_mediator, row, cache=None, database=None, query=None,
      **unused_kwargs):
    """Parse the transfer files.

     There is no direct relationship between who sends the file and
     who accepts the file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: the row with all information related with the file transfers.
      query: Optional query string.
      cache: a cache object (instance of SQLiteCache).
      database: A database object (instance of SQLiteDatabase).
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    source_dict = cache.GetResults(u'source')
    if not source_dict:
      results = database.Query(self.QUERY_SOURCE_FROM_TRANSFER)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      cache.CacheQueryResults(
          results, 'source', 'pk_id', ('skypeid', 'skypename'))
      source_dict = cache.GetResults(u'source')

    dest_dict = cache.GetResults(u'destination')
    if not dest_dict:
      results = database.Query(self.QUERY_DEST_FROM_TRANSFER)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
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

    if row['status'] == 8:
      if row['starttime']:
        event_object = SkypeTransferFileEvent(
            row, row['starttime'], u'GETSOLICITUDE', source, destination)
        parser_mediator.ProduceEvent(event_object, query=query)

      if row['accepttime']:
        event_object = SkypeTransferFileEvent(
            row, row['accepttime'], u'ACCEPTED', source, destination)
        parser_mediator.ProduceEvent(event_object, query=query)

      if row['finishtime']:
        event_object = SkypeTransferFileEvent(
            row, row['finishtime'], u'FINISHED', source, destination)
        parser_mediator.ProduceEvent(event_object, query=query)

    elif row['status'] == 2 and row['starttime']:
      event_object = SkypeTransferFileEvent(
          row, row['starttime'], u'SENDSOLICITUDE', source, destination)
      parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(SkypePlugin)
