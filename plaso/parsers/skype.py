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
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib


class SkypeChatEvent(event.EventObject):
  """Convenience class for a Skype event."""
  DATA_TYPE = 'skype:event:chat'

  def __init__(self, row, account):
    """Build a Skype Event from a single row."""
    super(SkypeChatEvent, self).__init__()

    self.timestamp = timelib.Timestamp.FromPosixTime(row['timestamp'])
    self.timestamp_desc = eventdata.EventTimestamp.WRITTEN_TIME
    self.title = row['title']
    self.username = u'{} <{}>'.format(row['from_displayname'], row['author'])
    self.text = row['body_xml']
    self.from_account = self.username
    if self.username == account:
      self.to_account = row['chat_partner']
    else:
      self.to_account = account


class SkypeAccountContainer(event.EventContainer):
  """Convenience container for account information."""
  DATA_TYPE = 'skype:event:account'

  def __init__(self, full_name, display_name, email, country):
    """Initialize the container."""
    super(SkypeAccountContainer, self).__init__()
    self.username = '{} <{}>'.format(full_name, display_name)
    self.display_name = display_name
    self.email = email
    self.country = country
    self.data_type = self.DATA_TYPE


class SkypeParser(parser.SQLiteParser):
  """Parse Skype main.db SQlite database file."""

  # Define the needed queries.
  # TODO: Parse more than just the chat database, there are others, like
  # SMS and Calls, etc.
  QUERIES = [
      (('SELECT c.id, c.friendlyname AS title, m.author AS author, '
        'c.dialog_partner AS chat_partner, c.adder, '
        'm.from_dispname AS from_displayname, m.body_xml, m.timestamp, '
        'm.dialog_partner FROM Chats c,Messages m WHERE c.name = m.chatname'),
       'ParseChat'),
      (('SELECT fullname, given_displayname, emails, country, '
        'profile_timestamp, authreq_timestamp, '
        'lastonline_timestamp, mood_timestamp, sent_authrequest_time, '
        'lastused_timestamp FROM Accounts'), 'ParseAccountInformation')]

  # The required tables.
  REQUIRED_TABLES = frozenset(
      ['Chats', 'Accounts', 'Conversations', 'Contacts'])

  def ParseAccountInformation(self, row, **dummy_kwargs):
    """Parses account information."""
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

    return container

  def ParseChat(self, row, **dummy_kwargs):
    """Parses a chat message row.

    Args:
      row: The row resulting from the query.

    Yields:
      An event object (SkypeChatEvent) containing the event data.
    """
    yield SkypeChatEvent(row, self._GetAccountInformation())

  def _GetAccountInformation(self):
    """Return the account holder."""
    if hasattr(self, '_mainaccount'):
      return self._mainaccount

    query = 'SELECT fullname, skypename FROM Accounts'

    cursor = self.db.cursor()
    result_set = cursor.execute(query)
    row = result_set.fetchone()

    if row:
      self._mainaccount = u'{} <{}>'.format(row['fullname'], row['skypename'])
      return self._mainaccount

