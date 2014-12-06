#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Parser for Mac OS X Keychain files."""

# INFO: Only supports internet and application passwords,
#       because it is the only data that contains timestamp events.
#       Keychain can also store "secret notes". These notes are stored
#       in the same type than the application format, then, they are already
#       supported. The stored wifi are also application passwords.

# TODO: the AccessControl for each entry has not been implemented. Until now,
#       I know that the AccessControl from Internet and App password are stored
#       using other tables (Symmetric, certificates, etc). Access Control
#       indicates which specific tool, or all, is able to use this entry.


import binascii
import construct
import logging
import os

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class KeychainInternetRecordEvent(event.EventObject):
  """Convenience class for an keychain internet record event."""

  DATA_TYPE = 'mac:keychain:internet'

  def __init__(
      self, timestamp, timestamp_desc, entry_name, account_name,
      text_description, comments, where, protocol, type_protocol, ssgp_hash):
    """Initializes the event object.

    Args:
      timestamp: Description of the timestamp value.
      timestamp_desc: Timelib type of the timestamp.
      entry_name: Name of the entry.
      account_name: Name of the account.
      text_description: Short description about the entry.
      comments: String that contains the comments added by the user.
      where: The domain name or IP where the password is used.
      protocol: The internet protocol used (eg. https).
      type_protocol: The sub-protocol used (eg. form).
      ssgp_hash: String with hexadecimal values from the password / cert hash.
    """
    super(KeychainInternetRecordEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = timestamp_desc
    self.entry_name = entry_name
    self.account_name = account_name
    self.text_description = text_description
    self.where = where
    self.protocol = protocol
    self.type_protocol = type_protocol
    self.comments = comments
    self.ssgp_hash = ssgp_hash


class KeychainApplicationRecordEvent(event.EventObject):
  """Convenience class for an keychain application password record event."""
  DATA_TYPE = 'mac:keychain:application'

  def __init__(
      self, timestamp, timestamp_desc, entry_name,
      account_name, text_description, comments, ssgp_hash):
    """Initializes the event object.

    Args:
      timestamp: Description of the timestamp value.
      timestamp_desc: Timelib type of the timestamp.
      entry_name: Name of the entry.
      account_name: Name of the account.
      text_description: Short description about the entry.
      comments: String that contains the comments added by the user.
      ssgp_hash: String with hexadecimal values from the password / cert hash.
    """
    super(KeychainApplicationRecordEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = timestamp_desc
    self.entry_name = entry_name
    self.account_name = account_name
    self.text_description = text_description
    self.comments = comments
    self.ssgp_hash = ssgp_hash


class KeychainParser(interface.BaseParser):
  """Parser for Keychain files."""

  NAME = 'mac_keychain'
  DESCRIPTION = u'Parser for Mac OS X Keychain files.'

  KEYCHAIN_MAGIC_HEADER = 'kych'
  KEYCHAIN_MAJOR_VERSION = 1
  KEYCHAIN_MINOR_VERSION = 0

  RECORD_TYPE_APPLICATION = 0x80000000
  RECORD_TYPE_INTERNET = 0x80000001

  # DB HEADER.
  KEYCHAIN_DB_HEADER = construct.Struct(
      'db_header',
      construct.String('magic', 4),
      construct.UBInt16('major_version'),
      construct.UBInt16('minor_version'),
      construct.UBInt32('header_size'),
      construct.UBInt32('schema_offset'),
      construct.Padding(4))

  # DB SCHEMA.
  KEYCHAIN_DB_SCHEMA = construct.Struct(
      'db_schema',
      construct.UBInt32('size'),
      construct.UBInt32('number_of_tables'))
  # For each number_of_tables, the schema has a TABLE_OFFSET with the
  # offset starting in the DB_SCHEMA.
  TABLE_OFFSET = construct.UBInt32('table_offset')

  TABLE_HEADER = construct.Struct(
      'table_header',
      construct.UBInt32('table_size'),
      construct.UBInt32('record_type'),
      construct.UBInt32('number_of_records'),
      construct.UBInt32('first_record'),
      construct.UBInt32('index_offset'),
      construct.Padding(4),
      construct.UBInt32('recordnumbercount'))

  RECORD_HEADER = construct.Struct(
      'record_header',
      construct.UBInt32('entry_length'),
      construct.Padding(12),
      construct.UBInt32('ssgp_length'),
      construct.Padding(4),
      construct.UBInt32('creation_time'),
      construct.UBInt32('last_mod_time'),
      construct.UBInt32('text_description'),
      construct.Padding(4),
      construct.UBInt32('comments'),
      construct.Padding(8),
      construct.UBInt32('entry_name'),
      construct.Padding(20),
      construct.UBInt32('account_name'),
      construct.Padding(4))
  RECORD_HEADER_APP = construct.Struct(
      'record_entry_app',
      RECORD_HEADER,
      construct.Padding(4))
  RECORD_HEADER_INET = construct.Struct(
      'record_entry_inet',
      RECORD_HEADER,
      construct.UBInt32('where'),
      construct.UBInt32('protocol'),
      construct.UBInt32('type'),
      construct.Padding(4),
      construct.UBInt32('url'))

  TEXT = construct.PascalString(
      'text', length_field=construct.UBInt32('length'))
  TIME = construct.Struct(
      'timestamp',
      construct.String('year', 4),
      construct.String('month', 2),
      construct.String('day', 2),
      construct.String('hour', 2),
      construct.String('minute', 2),
      construct.String('second', 2),
      construct.Padding(2))
  TYPE_TEXT = construct.String('type', 4)

  # TODO: add more protocols.
  _PROTOCOL_TRANSLATION_DICT = {
      u'htps': u'https',
      u'smtp': u'smtp',
      u'imap': u'imap',
      u'http': u'http'}

  def _GetTimestampFromEntry(self, parser_context, file_entry, structure):
    """Parse a time entry structure into a microseconds since Epoch in UTC.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      structure: TIME entry structure:
                 year: String with the number of the year.
                 month: String with the number of the month.
                 day: String with the number of the day.
                 hour: String with the number of the month.
                 minute: String with the number of the minute.
                 second: String with the number of the second.

    Returns:
      Microseconds since Epoch in UTC.
    """
    try:
      return timelib.Timestamp.FromTimeParts(
          int(structure.year, 10), int(structure.month, 10),
          int(structure.day, 10), int(structure.hour, 10),
          int(structure.minute, 10), int(structure.second, 10))
    except ValueError:
      logging.warning(
          u'[{0:s}] Invalid keychain time {1!s} in file: {2:s}'.format(
              self.NAME, parser_context.GetDisplayName(file_entry), structure))
      return 0

  def _ReadEntryApplication(
      self, parser_context, file_object, file_entry=None, parser_chain=None):
    """Extracts the information from an application password entry.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_object: A file-like object that points to an Keychain file.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
    """
    offset = file_object.tell()
    try:
      record = self.RECORD_HEADER_APP.parse_stream(file_object)
    except (IOError, construct.FieldError):
      logging.warning((
          u'[{0:s}] Unsupported record header at 0x{1:08x} in file: '
          u'{2:s}').format(
              self.NAME, offset, parser_context.GetDisplayName(file_entry)))
      return

    (ssgp_hash, creation_time, last_mod_time, text_description,
     comments, entry_name, account_name) = self._ReadEntryHeader(
         parser_context, file_entry, file_object, record.record_header, offset)

    # Move to the end of the record, and then, prepared for the next record.
    file_object.seek(
        record.record_header.entry_length + offset - file_object.tell(),
        os.SEEK_CUR)
    event_object = KeychainApplicationRecordEvent(
        creation_time, eventdata.EventTimestamp.CREATION_TIME,
        entry_name, account_name, text_description, comments, ssgp_hash)
    parser_context.ProduceEvent(
        event_object, parser_chain=parser_chain, file_entry=file_entry)

    if creation_time != last_mod_time:
      event_object = KeychainApplicationRecordEvent(
          last_mod_time, eventdata.EventTimestamp.MODIFICATION_TIME,
          entry_name, account_name, text_description, comments, ssgp_hash)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)

  def _ReadEntryHeader(
      self, parser_context, file_entry, file_object, record, offset):
    """Read the common record attributes.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      file_object: A file-like object that points to an Keychain file.
      record: Structure with the header of the record.
      offset: First byte of the record.

    Returns:
      A list of:
        ssgp_hash: Hash of the encrypted data (passwd, cert, note).
        creation_time: When the entry was created.
        last_mod_time: Last time the entry was updated.
        text_description: A brief description of the entry.
        entry_name: Name of the entry
        account_name: Name of the account.
    """
    # Info: The hash header always start with the string ssgp follow by
    #       the hash. Furthermore The fields are always a multiple of four.
    #       Then if it is not multiple the value is padded by 0x00.
    ssgp_hash = binascii.hexlify(file_object.read(record.ssgp_length)[4:])

    file_object.seek(
        record.creation_time - file_object.tell() + offset - 1, os.SEEK_CUR)
    creation_time = self._GetTimestampFromEntry(
        parser_context, file_entry, self.TIME.parse_stream(file_object))

    file_object.seek(
        record.last_mod_time - file_object.tell() + offset - 1, os.SEEK_CUR)
    last_mod_time = self._GetTimestampFromEntry(
        parser_context, file_entry, self.TIME.parse_stream(file_object))

    # The comment field does not always contain data.
    if record.text_description:
      file_object.seek(
          record.text_description - file_object.tell() + offset -1,
          os.SEEK_CUR)
      try:
        text_description = self.TEXT.parse_stream(file_object)
      except construct.FieldError:
        text_description = u'N/A (error)'
    else:
      text_description = u'N/A'

    # The comment field does not always contain data.
    if record.comments:
      file_object.seek(
          record.text_description - file_object.tell() + offset -1,
          os.SEEK_CUR)
      try:
        comments = self.TEXT.parse_stream(file_object)
      except construct.FieldError:
        comments = u'N/A (error)'
    else:
      comments = u'N/A'

    file_object.seek(
        record.entry_name - file_object.tell() + offset - 1, os.SEEK_CUR)
    try:
      entry_name = self.TEXT.parse_stream(file_object)
    except construct.FieldError:
      entry_name = u'N/A (error)'

    file_object.seek(
        record.account_name - file_object.tell() + offset - 1, os.SEEK_CUR)
    try:
      account_name = self.TEXT.parse_stream(file_object)
    except construct.FieldError:
      account_name = u'N/A (error)'

    return (
        ssgp_hash, creation_time, last_mod_time,
        text_description, comments, entry_name, account_name)

  def _ReadEntryInternet(
      self, parser_context, file_object, file_entry=None, parser_chain=None):
    """Extracts the information from an Internet password entry.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_object: A file-like object that points to an Keychain file.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
    """
    offset = file_object.tell()
    try:
      record = self.RECORD_HEADER_INET.parse_stream(file_object)
    except (IOError, construct.FieldError):
      logging.warning((
          u'[{0:s}] Unsupported record header at 0x{1:08x} in file: '
          u'{2:s}').format(
              self.NAME, offset, parser_context.GetDisplayName(file_entry)))
      return

    (ssgp_hash, creation_time, last_mod_time, text_description,
     comments, entry_name, account_name) = self._ReadEntryHeader(
         parser_context, file_entry, file_object, record.record_header, offset)
    if not record.where:
      where = u'N/A'
      protocol = u'N/A'
      type_protocol = u'N/A'
    else:
      file_object.seek(
          record.where - file_object.tell() + offset - 1, os.SEEK_CUR)
      where = self.TEXT.parse_stream(file_object)
      file_object.seek(
          record.protocol - file_object.tell() + offset - 1, os.SEEK_CUR)
      protocol = self.TYPE_TEXT.parse_stream(file_object)
      file_object.seek(
          record.type - file_object.tell() + offset - 1, os.SEEK_CUR)
      type_protocol = self.TEXT.parse_stream(file_object)
      type_protocol = self._PROTOCOL_TRANSLATION_DICT.get(
          type_protocol, type_protocol)
      if record.url:
        file_object.seek(
            record.url - file_object.tell() + offset - 1, os.SEEK_CUR)
        url = self.TEXT.parse_stream(file_object)
        where = u'{0:s}{1:s}'.format(where, url)

    # Move to the end of the record, and then, prepared for the next record.
    file_object.seek(
        record.record_header.entry_length + offset - file_object.tell(),
        os.SEEK_CUR)

    event_object = KeychainInternetRecordEvent(
        creation_time, eventdata.EventTimestamp.CREATION_TIME,
        entry_name, account_name, text_description,
        comments, where, protocol, type_protocol, ssgp_hash)
    parser_context.ProduceEvent(
        event_object, parser_chain=parser_chain, file_entry=file_entry)

    if creation_time != last_mod_time:
      event_object = KeychainInternetRecordEvent(
          last_mod_time, eventdata.EventTimestamp.MODIFICATION_TIME,
          entry_name, account_name, text_description,
          comments, where, protocol, type_protocol, ssgp_hash)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)

  def _VerifyStructure(self, file_object):
    """Verify that we are dealing with an Keychain entry.

    Args:
      file_object: A file-like object that points to an Keychain file.

    Returns:
      A list of table positions if it is a keychain, None otherwise.
    """
    # INFO: The HEADER KEYCHAIN:
    # [DBHEADER] + [DBSCHEMA] + [OFFSET TABLE A] + ... + [OFFSET TABLE Z]
    # Where the table offset is relative to the first byte of the DB Schema,
    # then we must add to this offset the size of the [DBHEADER].
    try:
      db_header = self.KEYCHAIN_DB_HEADER.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return
    if (db_header.minor_version != self.KEYCHAIN_MINOR_VERSION or
        db_header.major_version != self.KEYCHAIN_MAJOR_VERSION or
        db_header.magic != self.KEYCHAIN_MAGIC_HEADER):
      return

    # Read the database schema and extract the offset for all the tables.
    # They are ordered by file position from the top to the bottom of the file.
    try:
      db_schema = self.KEYCHAIN_DB_SCHEMA.parse_stream(file_object)
    except (IOError, construct.FieldError):
      return
    table_offsets = []
    for _ in range(db_schema.number_of_tables):
      try:
        table_offset = self.TABLE_OFFSET.parse_stream(file_object)
      except (IOError, construct.FieldError):
        return
      table_offsets.append(table_offset + self.KEYCHAIN_DB_HEADER.sizeof())
    return table_offsets

  def Parse(self, parser_context, file_entry, parser_chain=None):
    """Extract data from a Keychain file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
    """
    file_object = file_entry.GetFileObject()
    table_offsets = self._VerifyStructure(file_object)
    if not table_offsets:
      file_object.close()
      raise errors.UnableToParseFile(u'The file is not a Keychain file.')

    # Add ourselves to the parser chain, which will be used in all subsequent
    # event creation in this parser.
    parser_chain = self._BuildParserChain(parser_chain)

    for table_offset in table_offsets:
      # Skipping X bytes, unknown data at this point.
      file_object.seek(table_offset - file_object.tell(), os.SEEK_CUR)
      try:
        table = self.TABLE_HEADER.parse_stream(file_object)
      except construct.FieldError as exception:
        logging.warning((
            u'[{0:s}] Unable to parse table header in file: {1:s} '
            u'with error: {2:s}.').format(
                self.NAME, parser_context.GetDisplayName(file_entry),
                exception))
        continue

      # Table_offset: absolute byte in the file where the table starts.
      # table.first_record: first record in the table, relative to the
      #                     first byte of the table.
      file_object.seek(
          table_offset + table.first_record - file_object.tell(), os.SEEK_CUR)

      if table.record_type == self.RECORD_TYPE_INTERNET:
        for _ in range(table.number_of_records):
          self._ReadEntryInternet(
              parser_context, file_object, file_entry=file_entry,
              parser_chain=parser_chain)

      elif table.record_type == self.RECORD_TYPE_APPLICATION:
        for _ in range(table.number_of_records):
          self._ReadEntryApplication(
              parser_context, file_object, file_entry=file_entry,
              parser_chain=parser_chain)

    file_object.close()


manager.ParsersManager.RegisterParser(KeychainParser)
