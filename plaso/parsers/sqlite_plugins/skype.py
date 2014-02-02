#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains a basic Skype SQLite parser."""
import logging

from plaso.lib import event
from plaso.parsers.sqlite_plugins import interface

__author__ = 'Joaquin Moreno Garijo (bastionado@gmail.com)'


class SkypeChatEvent(event.PosixTimeEvent):
  """Convenience class for a Skype event."""
  DATA_TYPE = 'skype:event:chat'

  def __init__(self, row, to_account):
    """Build a Skype Event from a single row."""
    super(SkypeChatEvent, self).__init__(
        row['timestamp'], 'Chat from Skype', self.DATA_TYPE)

    self.title = row['title']
    self.text = row['body_xml']
    self.from_account = u'{} <{}>'.format(
        row['from_displayname'], row['author'])
    self.to_account = to_account


class SkypeAccountContainer(event.EventContainer):
  """Convenience container for account information."""
  DATA_TYPE = 'skype:event:account'

  def __init__(self, full_name, display_name, email, country):
    """Initialize the container."""
    super(SkypeAccountContainer, self).__init__()

    self.username = u'{} <{}>'.format(full_name, display_name)
    self.display_name = display_name
    self.email = email
    self.country = country
    self.data_type = self.DATA_TYPE


class SkypeSMSEvent(event.PosixTimeEvent):
  """Convenience EventObject for SMS."""
  DATA_TYPE = 'skype:event:sms'

  def __init__(self, row, dst_number):
    """Read the information related with the SMS.

      Args:
        row: row form the sql query.
          row['time_sms']: timestamp when the sms was send.
          row['dstnum_sms']: number which receives the sms.
          row['msg_sms']: text send to this sms.
        dst_number: phone number where the user send the sms.
    """
    super(SkypeSMSEvent, self).__init__(
        row['time_sms'], 'SMS from Skype', self.DATA_TYPE)

    self.number = dst_number
    self.text = row['msg_sms']


class SkypeCallEvent(event.PosixTimeEvent):
  """Convenience EventObject for the calls."""
  DATA_TYPE = 'skype:event:call'

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
        timestamp, 'Call from Skype', self.DATA_TYPE)

    self.call_type = call_type
    self.user_start_call = user_start_call
    self.src_call = source
    self.dst_call = destination
    self.video_conference = video_conference


class SkypeTransferFileEvent(event.PosixTimeEvent):
  """Evaluate the action of send a file."""
  DATA_TYPE = 'skype:event:transferfile'

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

    super(SkypeTransferFileEvent, self).__init__(
        timestamp, 'File transfer from Skype', self.DATA_TYPE)

    self.action_type = action_type
    self.source = source
    self.destination = destination
    self.transferred_filepath = row['filepath']
    self.transferred_filename = row['filename']
    try:
      self.transferred_filesize = int(row['filesize'])
    except ValueError:
      logging.debug(u'Unknown filesize {}'.format(
          self.transferred_filename))
      self.transferred_filesize = 0


class SkypePlugin(interface.SQLitePlugin):
  """SQLite plugin for Skype main.db SQlite database file."""

  NAME = 'skype'

  # Queries for building cache.
  QUERY_DEST_FROM_TRANSFER = (
      u'SELECT parent_id, partner_handle AS skypeid, '
      u'partner_dispname AS skypename FROM transfers')
  QUERY_SOURCE_FROM_TRANSFER = (
      u'SELECT pk_id, partner_handle AS skypeid, '
      u'partner_dispname AS skypename FROM transfers')

  # Define the needed queries.
  QUERIES = [
      (('SELECT c.id, c.participants, c.friendlyname AS title, '
        'm.author AS author, m.from_dispname AS from_displayname, '
        'm.body_xml, m.timestamp, c.dialog_partner FROM Chats c, Messages m '
        'WHERE c.name = m.chatname'), 'ParseChat'),
      (('SELECT id, fullname, given_displayname, emails, '
        'country, profile_timestamp, authreq_timestamp, '
        'lastonline_timestamp, mood_timestamp, sent_authrequest_time, '
        'lastused_timestamp FROM Accounts'), 'ParseAccountInformation'),
      (('SELECT id, target_numbers AS dstnum_sms, timestamp AS time_sms, '
        'body AS msg_sms FROM SMSes'), 'ParseSMS'),
      (('SELECT id, partner_handle, partner_dispname, offer_send_list, '
        'starttime, accepttime, finishtime, filepath, filename, filesize, '
        'status, parent_id, pk_id FROM Transfers'), 'ParseFileTransfer'),
      (('SELECT c.id, cm.guid, c.is_incoming, '
        'cm.call_db_id, cm.videostatus, c.begin_timestamp AS try_call, '
        'cm.start_timestamp AS accept_call, cm.call_duration '
        'FROM Calls c, CallMembers cm '
        'WHERE c.id = cm.call_db_id;'), 'ParseCall')]

  # The required tables.
  REQUIRED_TABLES = frozenset(
      ['Chats', 'Accounts', 'Conversations', 'Contacts', 'SMSes', 'Transfers',
       'CallMembers', 'Calls'])

  def ParseAccountInformation(self, row, **unused_kwargs):
    """Parses the Accounts database."""
    container = SkypeAccountContainer(
        row['fullname'], row['given_displayname'], row['emails'],
        row['country'])

    if row['profile_timestamp']:
      container.Append(event.PosixTimeEvent(
          row['profile_timestamp'], 'Profile Changed'))

    if row['authreq_timestamp']:
      container.Append(event.PosixTimeEvent(
          row['authreq_timestamp'], 'Authenticate Request'))

    if row['lastonline_timestamp']:
      container.Append(event.PosixTimeEvent(
          row['lastonline_timestamp'], 'Last Online'))

    if row['mood_timestamp']:
      container.Append(event.PosixTimeEvent(
          row['mood_timestamp'], 'Mood Event'))

    if row['sent_authrequest_time']:
      container.Append(event.PosixTimeEvent(
          row['sent_authrequest_time'], 'Auth Request Sent'))

    if row['lastused_timestamp']:
      container.Append(event.PosixTimeEvent(
          row['lastused_timestamp'], 'Last Used'))

    yield container

  def ParseChat(self, row, **unused_kwargs):
    """Parses a chat message row.

    Args:
      row: The row resulting from the query.

    Yields:
      An event object (SkypeChatEvent) containing the event data.
    """
    to_account = ''
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

    yield SkypeChatEvent(row, to_account)

  def ParseSMS(self, row, **unused_kwargs):
    """Parse SMS."""
    dst_number = row['dstnum_sms'].replace(' ', '')

    yield SkypeSMSEvent(row, dst_number)

  def ParseCall(self, row, **unused_kwargs):
    """Parse the calls taking into accounts some rows.

    Args:
      row: The row resulting from the query.

    Yields:
      An event SkypeCallEvent if a call query were done it, but it was
        not be answer, the status from this all is WAITING.
      An event SkypeCallEvent if a call query when the call is accepted,
        the status from this all is ACCEPTED.
      An event SkypeCallEvent if a call query were the call finished,
        the status from this all is FINISHED.
    """
    try:
      aux = row['guid'].split('-')
      src_aux = aux[0]
      dst_aux = aux[1]
    except IndexError:
      src_aux = u'Unknown [{}]'.format(row['guid'])
      dst_aux = u'Unknown [{}]'.format(row['guid'])

    if row['is_incoming'] == '0':
      user_start_call = True
      source = src_aux
      if row['ip_address']:
        destination = u'{} <{}>'.format(dst_aux, row['ip_address'])
      else:
        destination = dst_aux
    else:
      user_start_call = False
      source = src_aux
      destination = dst_aux

    if row['videostatus'] == '3':
      video_conference = True
    else:
      video_conference = False

    yield SkypeCallEvent(row['try_call'], 'WAITING', user_start_call,
                         source, destination, video_conference)
    if row['accept_call']:
      yield SkypeCallEvent(row['accept_call'], 'ACCEPTED', user_start_call,
                           source, destination, video_conference)
      if row['call_duration']:
        try:
          timestamp = int(row['accept_call']) + int(row['call_duration'])
          yield SkypeCallEvent(timestamp, 'FINISHED', user_start_call,
                               source, destination, video_conference)
        except ValueError:
          logging.debug(u'Unknown when the call {} was'
                        u'finished.'.format(row['id']))

  def ParseFileTransfer(self, row, cache, **unused_kwargs):
    """Parse the transfer files.

    Args:
      row: the row with all information related with the file transfers.
      cache: a cache object (instance of SQLiteCache).

    Yields:
      An event SkypeTransferFileEvent when the user gets a file solicitude.
        The status from this event is GETSOLICITUDE
      An event SkypeTransferFileEvent when the user accepts a file.
        The status from this event is ACCEPTED.
      An event SkypeTransferFileEvent when the transfer finish.
        The status from this event is FINISHED.
      An event SkypeTransferFileEvent when the user queries to send a file.
        The status from this event is SENDSOLICITUDE.

     Note: we don't have direct relationship between who sends
           the file and who accepts the file. Only acctions.
    """
    source_dict = cache.GetResults('source')
    if not source_dict:
      cursor = self.db.cursor
      results = cursor.execute(self.QUERY_SOURCE_FROM_TRANSFER)
      cache.CacheQueryResults(
          results, 'source', 'pk_id', ('skypeid', 'skypename'))
      source_dict = cache.GetResults('source')

    dest_dict = cache.GetResults('destination')
    if not dest_dict:
      cursor = self.db.cursor
      results = cursor.execute(self.QUERY_DEST_FROM_TRANSFER)
      cache.CacheQueryResults(
          results, 'destination', 'parent_id', ('skypeid', 'skypename'))
      dest_dict = cache.GetResults('destination')

    source = u'Unknown'
    destination = u'Unknown'

    if row['parent_id']:
      destination = u'{} <{}>'.format(
          row['partner_handle'], row['partner_dispname'])
      skype_id, skype_name = source_dict.get(row['parent_id'], [None, None])
      if skype_name:
        source = u'{} <{}>'.format(skype_id, skype_name)
    else:
      source = u'{} <{}>'.format(
          row['partner_handle'], row['partner_dispname'])

      if row['pk_id']:
        skype_id, skype_name = dest_dict.get(row['pk_id'], [None, None])
        if skype_name:
          destination = u'{} <{}>'.format(skype_id, skype_name)

    if row['status'] == 8:
      if row['starttime']:
        yield SkypeTransferFileEvent(
            row, row['starttime'], 'GETSOLICITUDE', source, destination)
      if row['accepttime']:
        yield SkypeTransferFileEvent(
            row, row['accepttime'], 'ACCEPTED', source, destination)
      if row['finishtime']:
        yield SkypeTransferFileEvent(
            row, row['finishtime'], 'FINISHED', source, destination)
    elif row['status'] == 2 and row['starttime']:
      yield SkypeTransferFileEvent(
          row, row['starttime'], 'SENDSOLICITUDE', source, destination)
